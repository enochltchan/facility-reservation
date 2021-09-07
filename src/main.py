from fastapi import FastAPI, HTTPException
from typing import Optional
from models.models_main import ReservationModel, ReservationUpdateModel, UserModel, NameModel, AmountModel, ActivationModel, LoginDetailsModel, SettingValueModel, HoldModel
import facility
import datetime
import uuid
import api_sqlite
import os
import string


# Create app
app = FastAPI()


@app.on_event('startup')
async def startup():
    """Set whether client logins are allowed on app startup based on environment variable"""
    client_logins_allowed = True
    if os.getenv('CLIENT_LOGINS_ALLOWED') == 'false':
        client_logins_allowed = False
    await api_sqlite.set_settings_value('client_logins_allowed', client_logins_allowed)


@app.get('/')
async def root():
    return {'message': 'Welcome to MPCS, Inc. Team 1 Reservation System!'}


@app.post('/users', status_code=201)
async def add_user(user: UserModel):
    """Add new user using ID from POST request"""
    if user.role not in ('facility manager', 'client', 'remote facility manager'):
        raise HTTPException(status_code=400, detail='User must be one of facility manager, client or remote facility manager')
    if await api_sqlite.add_user(user.id, user.password, user.name, user.role):
        return {'message': 'User added successfully'}
    else:
        raise HTTPException(status_code=400, detail='User already exists')


@app.get('/users')
async def list_users():
    """Get list of all users"""
    rows = await api_sqlite.list_users()
    response = {}
    if rows:
        for row in rows:
            response[row.id] = {
                'name': row.name,
                'account_balance': row.account_balance,
                'activation status': row.activation,
                'role': row.role
            }
        return response
    else:
        raise HTTPException(status_code=404, detail='No users found')


@app.get('/users/{id}')
async def get_user_details(id: str):
    """Get details for user with a given ID"""
    await handle_invalid_user(id)
    row = await api_sqlite.get_user(id)
    if row:
        return {'name': row.name,
                'account balance': row.account_balance,
                'activation status': row.activation,
                'role': row.role
                }
    else:
        raise HTTPException(status_code=404, detail='User not found')


@app.delete('/users/{id}')
async def delete_user(id: str):
    """Delete user with a given ID"""
    await handle_invalid_user(id)
    await api_sqlite.remove_user(id)
    return {'message': 'User removed successfully'}


@app.put('/users/{id}/name')
async def edit_user_name(id: str, name: NameModel):
    """Edit name of user with a given ID"""
    await handle_invalid_user(id)
    await api_sqlite.edit_user_name(id, name.name)
    return {'message': 'User name edited successfully'}


@app.put('/users/{id}/account_balance')
async def add_to_user_balance(id: str, amount: AmountModel):
    """Add to account balance of user with a given ID"""
    await handle_invalid_user(id)
    if facility.account_balance_addition_within_bounds(amount.amount):
        await api_sqlite.add_to_user_balance(id, round(amount.amount, 2))
        row = await api_sqlite.get_user(id)
        return {'message': 'Funds added successfully, Current account balance: $' + str(row.account_balance)}
    else:
        raise HTTPException(status_code=400, detail='Amount not between $1 and $25,000')


@app.put('/users/{id}/activation')
async def change_user_activation(id: str, activation: ActivationModel):
    """Change activation status of user with a given ID"""
    await handle_invalid_user(id)
    await api_sqlite.edit_user_activation(id, activation.activation)
    if activation.activation:
        return {'message': 'User activated successfully'}
    else:
        return {'message': 'User deactivated successfully'}


@app.post('/reservations', status_code=201)
async def make_reservation(reservation: ReservationModel):
    """Make new reservation using POST request parameters"""
    await handle_invalid_user(reservation.customer)
    await handle_deactivated_user(reservation.customer)
    # Convert date string to date object
    try:
        date_time = datetime.datetime.strptime(reservation.date_time_string, '%m-%d-%Y %H:%M')
    except ValueError:
        raise HTTPException(status_code=400, detail={'message': 'Date/time format incorrect', 'hold_request_possible': False})
    rows = await api_sqlite.list_reservations()
    # Attempt reservation if customer has not exceeded limit
    if facility.reservation_limit_exceeded(rows, reservation, date_time):
        raise HTTPException(status_code=400, detail={'message': 'Customer limit exceeded', 'hold_request_possible': True})
    # Check if reservation is valid against constraints
    reservation_valid, validity_message, hold_request_possible = facility.reservation_valid(reservation.resource, reservation.customer, date_time)
    # Add reservation and corresponding transaction to database
    if not reservation_valid:
        raise HTTPException(status_code=400, detail={'message': validity_message, 'hold_request_possible': hold_request_possible})
    total_cost = facility.calculate_costs(reservation, date_time)
    # Check if user has sufficient account balance
    row = await api_sqlite.get_user(reservation.customer)
    if row.account_balance < total_cost:
        raise HTTPException(status_code=400, detail={'message': 'Not enough balance in account', 'hold_request_possible': False})
    reservation_uuid = str(uuid.uuid4())
    await api_sqlite.add_reservation(reservation_uuid, date_time, reservation.resource, reservation.customer, reservation.reserver, total_cost)
    await api_sqlite.add_transaction(str(uuid.uuid4()), datetime.datetime.now(), reservation.customer, total_cost)
    await api_sqlite.add_to_user_balance(reservation.customer, - total_cost)
    return {'message': 'Reservation successful with serial number: ' + reservation_uuid + ', Total cost: $' + str(total_cost) + ', Current account balance: $' + str(row.account_balance - total_cost)}


@app.put('/reservations')
async def edit_reservation(reservation: ReservationUpdateModel):
    """Edit existing reservation using PUT request parameters"""
    await handle_invalid_user(reservation.customer)
    await handle_deactivated_user(reservation.customer)
    # Convert date string to date object
    try:
        date_time = datetime.datetime.strptime(reservation.date_time_string, '%m-%d-%Y %H:%M')
    except ValueError:
        raise HTTPException(status_code=400, detail='Date/time format incorrect')
    # Fetch reservation with serial number if exists
    row = await api_sqlite.get_reservation_with_serial_number(reservation.serial_num)
    if not row:
        raise HTTPException(status_code=404, detail='Reservation not found')
    rows = await api_sqlite.list_reservations()
    # Attempt edited reservation if customer has not exceeded limit
    if facility.reservation_limit_exceeded(rows, reservation, date_time):
        raise HTTPException(status_code=400, detail='Customer limit exceeded')
    # Check if edited reservation is valid against constraints
    reservation_valid, validity_message, hold_request_possible = facility.reservation_valid(reservation.resource, reservation.customer, date_time)
    if not reservation_valid:
        raise HTTPException(status_code=400, detail=validity_message)
    # Remove old reservation
    await api_sqlite.remove_reservation(reservation.serial_num)
    # Calculate cost of edited reservation
    total_cost = facility.calculate_costs(reservation, date_time)
    # Calculate refund amount for old reservation
    refund_amount = facility.calculate_refund(row)
    # Calculate net amount and add edited reservation and corresponding transaction
    net_amount = total_cost - refund_amount
    await api_sqlite.add_reservation(reservation.serial_num, date_time, reservation.resource, reservation.customer, reservation.reserver, total_cost)
    if net_amount != 0:
        await api_sqlite.add_transaction(str(uuid.uuid4()), datetime.datetime.now(), reservation.customer, net_amount)
        await api_sqlite.add_to_user_balance(reservation.customer, - net_amount)
    if net_amount >= 0:
        return {'message': 'Modification successful, Total cost: $' + str(net_amount)}
    else:
        return {'message': 'Modification successful, Refund amount: $' + str(- net_amount)}


@app.get('/reservations')
async def list_reservations(start_date_string: Optional[str] = '01-01-2021', end_date_string: Optional[str] = '01-01-2022'):
    """Get list of all reservations with start and end date in format MM-DD-YYYY as optional query parameters"""
    # Convert date strings to date objects
    try:
        start_date = datetime.datetime.strptime(start_date_string, '%m-%d-%Y').date()
        end_date = datetime.datetime.strptime(end_date_string, '%m-%d-%Y').date()
    except ValueError:
        raise HTTPException(status_code=404, detail='Date format incorrect')
    # Return list of all reservations in json format keyed by serial number
    rows = await api_sqlite.list_reservations()
    if rows:
        response = {}
        for row in rows:
            if start_date < row.date_time.date() < end_date:
                response[row.serial_num] = {
                    'date': row.date_time.strftime('%m-%d-%Y %H:%M'),
                    'resource': row.resource,
                    'customer': row.customer
                }
        return response
    else:
        raise HTTPException(status_code=404, detail='No reservations found')


@app.get('/reservations/serial_num/{serial_num}')
async def get_reservation(serial_num: str):
    """Get a reservation with given serial number"""
    row = await api_sqlite.get_reservation_with_serial_number(serial_num)
    if not row:
        raise HTTPException(status_code=404, detail='Reservation not found')
    return {
        'date': row.date_time.strftime('%m-%d-%Y %H:%M'),
        'resource': row.resource
    }


@app.get('/reservations/{customer}')
async def list_reservations_for_customer(customer: str, start_date_string: Optional[str] = '01-01-2021', end_date_string: Optional[str] = '01-01-2022'):
    """Get list of all reservations for a customer with customer as path parameter, and start and end date in format MM-DD-YYYY as optional query parameters"""
    await handle_invalid_user(customer)
    # Convert date strings to date objects
    try:
        start_date = datetime.datetime.strptime(start_date_string, '%m-%d-%Y').date()
        end_date = datetime.datetime.strptime(end_date_string, '%m-%d-%Y').date()
    except ValueError:
        raise HTTPException(status_code=404, detail='Date format incorrect')
    # Return list of all reservations for customer in json format keyed by serial number
    rows = await api_sqlite.list_reservations_for_customer(customer)
    response = {}
    reservations_found = False
    for row in rows:
        if start_date < row.date_time.date() < end_date and row.customer == customer:
            response[row.serial_num] = {
                'date': row.date_time.strftime('%m-%d-%Y %H:%M'),
                'resource': row.resource
            }
            reservations_found = True
    if reservations_found:
        return response
    else:
        raise HTTPException(status_code=404, detail='No reservations found for customer')


@app.delete('/reservations')
async def cancel_reservation(customer: str, serial_num: str):
    """Cancel reservation using serial number as query parameter"""
    await handle_invalid_user(customer)
    # Fetch reservation with serial number if exists
    row = await api_sqlite.get_reservation_with_serial_number(serial_num)
    # Remove reservation and add corresponding transactions to database
    if row:
        refund_amount = facility.calculate_refund(row)
        if refund_amount != 0:
            await api_sqlite.add_transaction(str(uuid.uuid4()), datetime.datetime.now(), row.customer, - refund_amount)
            await api_sqlite.add_to_user_balance(customer, refund_amount)
        await api_sqlite.remove_reservation(serial_num)
        return {'message': 'Cancellation successful, Refund amount: $' + str(refund_amount)}
    else:
        raise HTTPException(status_code=404, detail='Reservation not found')


@app.get('/transactions')
async def list_transactions(start_date_string: Optional[str] = '01-01-2021', end_date_string: Optional[str] = '01-01-2022'):
    """Get list of all transactions with start and end date in format MM-DD-YYYY as optional query parameters"""
    # Convert date strings to date objects
    try:
        start_date = datetime.datetime.strptime(start_date_string, '%m-%d-%Y').date()
        end_date = datetime.datetime.strptime(end_date_string, '%m-%d-%Y').date()
    except ValueError:
        raise HTTPException(status_code=404, detail='Date format incorrect')
    # Return list of all transactions in json format keyed by id
    rows = await api_sqlite.list_transactions()
    if rows:
        response = {}
        for row in rows:
            if start_date < row.date_time.date() < end_date:
                response[row.id] = {
                    'date': row.date_time.strftime('%m-%d-%Y %H:%M'),
                    'customer': row.customer,
                    'amount': str(row.amount)
                }
        return response
    else:
        raise HTTPException(status_code=404, detail='No transactions found')


@app.get('/transactions/{customer}')
async def list_transactions(customer: str, start_date_string: Optional[str] = '01-01-2021', end_date_string: Optional[str] = '01-01-2022'):
    """Get list of all transactions for a customer with customer as path parameter, and start and end date in format MM-DD-YYYY as optional query parameters"""
    await handle_invalid_user(customer)
    # Convert date strings to date objects
    try:
        start_date = datetime.datetime.strptime(start_date_string, '%m-%d-%Y').date()
        end_date = datetime.datetime.strptime(end_date_string, '%m-%d-%Y').date()
    except ValueError:
        raise HTTPException(status_code=404, detail='Date format incorrect')
    # Return list of all transactions for customer in json format keyed by id
    rows = await api_sqlite.list_transactions_for_customer(customer)
    response = {}
    transactions_found = False
    for row in rows:
        if start_date < row.date_time.date() < end_date and row.customer == customer:
            response[row.id] = {
                'date': row.date_time.strftime('%m-%d-%Y %H:%M'),
                'amount': str(row.amount)
            }
            transactions_found = True
    if transactions_found:
        return response
    else:
        raise HTTPException(status_code=404, detail='No transactions found for customer')


@app.post('/validity')
async def validate(login_details: LoginDetailsModel):
    """Check validity of a given user ID and password combination"""
    if await api_sqlite.user_valid(login_details.id):
        if await api_sqlite.password_valid(login_details.id, login_details.password):
            return {'validity': True}
    return {'validity': False}


@app.get('/settings/{setting}')
async def get_setting(setting: str):
    """Get current value of setting"""
    await handle_invalid_setting(setting)
    return {'value': await api_sqlite.get_settings_value(setting)}


@app.post('/settings/{setting}')
async def set_setting(setting: str, value: SettingValueModel):
    """Set value of setting"""
    await handle_invalid_setting(setting)
    await api_sqlite.set_settings_value(setting, value.value)
    return {'message': 'Modification successful'}


@app.post('/hold')
async def add_hold(hold: HoldModel):
    """Make new hold using POST request parameters"""
    await handle_invalid_user(hold.username)
    # Validate remote facility manager username and password
    if not await api_sqlite.password_valid(hold.username, hold.password):
        return {'success': False, 'message': 'Login details invalid'}
    # Check if start and end times end with :00 or :30
    if not (facility.time_ends_with_00_or_30(hold.start_time) or facility.time_ends_with_00_or_30(hold.end_time)):
        return {'success': False, 'message': 'Start and end times must be :00 or :30'}
    # Check if end time is after start time
    if not facility.time_compare(hold.end_time, hold.start_time):
        return {'success': False, 'message': 'End time must be after start time'}
    # Get list of start times for 30-minute blocks
    start_times = facility.get_formatted_list_of_start_times(hold.start_date, hold.start_time, hold.end_time)
    # Create list for serial numbers of reservations corresponding to holds for cancellation purposes
    serial_nums = []
    # Remove trailing digits from resource name
    resource = hold.request.rstrip(string.digits)
    # Add corresponding reservations to database
    for start_time in start_times:
        date_time = datetime.datetime.strptime(start_time, '%m-%d-%Y %H:%M')
        reservation_valid, validity_message, hold_request_possible = facility.reservation_valid(resource, hold.client_name, date_time)
        if not reservation_valid:
            return {'success': False, 'message': validity_message}
        total_cost = facility.calculate_costs(ReservationModel(resource=resource, customer=hold.client_name, reserver=hold.username, date_time_string=start_time), date_time)
        reservation_serial_num = str(uuid.uuid4())
        await api_sqlite.add_reservation(reservation_serial_num, date_time, resource, hold.client_name, hold.username, total_cost)
        serial_nums.append(reservation_serial_num)
    return {'success': True, 'facility_name': 'Team 1, Chicago, IL', 'message': 'Hold added successfully with serial numbers for 30-minute blocks: ' + str(serial_nums)}


@app.get('/hold')
async def list_holds():
    """List all holds made for other facilities"""
    rows = await api_sqlite.list_holds()
    if rows:
        response = {}
        for row in rows:
            response[row.serial_num] = {
                'date': row.date_time.strftime('%m-%d-%Y %H:%M'),
                'resource': row.resource,
                'customer': row.customer,
                'reserver': row.reserver
            }
        return response
    else:
        raise HTTPException(status_code=404, detail='No holds found')


async def handle_invalid_user(id):
    """Raise exception if user with given ID is invalid"""
    if not await api_sqlite.user_valid(id):
        raise HTTPException(status_code=400, detail='User ID invalid')


async def handle_deactivated_user(id):
    """Raise exception if user with given ID is deactivated"""
    if not await api_sqlite.user_activated(id):
        raise HTTPException(status_code=403, detail='User deactivated')


async def handle_invalid_setting(setting):
    """"Raise exception if setting name is invalid"""
    if not await api_sqlite.setting_name_valid(setting):
        raise HTTPException(status_code=400, detail='Setting must be one of "client_logins_allowed" or "client_adding_funds_allowed"')
