import datetime
from models.resource import Resource

"""Contains resources and functions for business logic"""

# Facility resource list
resources = []
num_resources = 0
for i in range(15):
    resources.append(Resource('workshop', num_resources, 99 / 2))
    num_resources += 1
for i in range(2):
    resources.append(Resource('mini microvac', num_resources, 2000 / 2))
    num_resources += 1
    resources.append(Resource('irradiator', num_resources, 2200 / 2))
    num_resources += 1
    resources.append(Resource('polymer extruder', num_resources, 500 / 2))
    num_resources += 1
resources.append(Resource('high velocity crusher', num_resources, 10000))
num_resources += 1
resources.append(Resource('1.21 gigawatt lightning harvester', num_resources, 8800 / 2))
num_resources += 1


def reservation_valid(resource_name, customer, date_time):
    """Check if reservation is valid according to date, time and resource constraints"""
    # Time ending with :00 or :30
    if not date_time.minute in (0, 30):
        return False, 'Time not :00 or :30', False
    # Within working hours
    if not ((date_time.weekday() in range(5) and date_time.hour in range(9, 17)) or (
                date_time.weekday() == 5 and date_time.hour in range(10, 16))):
        return False, 'Time outside working hours', True
    # Within 30 days from now
    if not date_time > datetime.datetime.now() > date_time - datetime.timedelta(days=30):
        return False, 'Date not within 30 days from now', False
    num_machines = 0
    num_irradiators = 0
    harvester_running = False
    # Count number of machines, number of irradiators and check if harvester is running at same time
    for resource in resources:
        if resource.name != 'workshop' and date_time in resource.reservations:
            num_machines += 1
        if resource.name == 'irradiator' and date_time in resource.reservations:
            num_irradiators += 1
        if resource.name == '1.21 gigawatt lightning harvester' and date_time in resource.reservations:
            harvester_running = True
    # Check if resource is present in facility
    resource_name_valid = False
    for resource in resources:
        if resource.name == resource_name:
            resource_name_valid = True
            # Only 3 other machines can run along with harvester
            if harvester_running:
                if num_machines > 3:
                    break
            # Only 1 irradiator can run at a time
            elif resource_name == 'irradiator':
                if num_irradiators != 0:
                    break
                # Check if irradiator is cooling down
                time_valid = True
                for invalid_date_time in (
                        date_time - datetime.timedelta(minutes=60),
                        date_time - datetime.timedelta(minutes=30),
                        date_time, date_time + datetime.timedelta(minutes=30),
                        date_time + datetime.timedelta(minutes=60)):
                    if invalid_date_time in resource.reservations:
                        time_valid = False
                if time_valid:
                    resource.reservations[date_time] = customer
                    return True, 'Reservation successful', False
                else:
                    return False, 'Time invalid for irradiator', True
            # Harvester can only run along with 3 other machines
            elif resource_name == '1.21 gigawatt lightning harvester':
                if num_machines > 3:
                    break
                else:
                    resource.reservations[date_time] = customer
                    return True, 'Reservation successful', False
            # Check if high velocity crusher is recalibrating
            elif resource_name == 'high velocity crusher':
                time_valid = True
                for minutes in range(-360, 390, 30):
                    if date_time + datetime.timedelta(minutes=minutes) in resource.reservations:
                        time_valid = False
                if time_valid:
                    resource.reservations[date_time] = customer
                    return True, 'Reservation successful', False
                else:
                    return False, 'Time invalid for crusher', True
            # Reservation valid if all constraints fulfilled
            elif date_time not in resource.reservations:
                resource.reservations[date_time] = customer
                return True, 'Reservation successful', False
    if resource_name_valid:
        return False, 'Resource unavailable', True
    else:
        return False, 'Resource name invalid', False


def reservation_limit_exceeded(rows, reservation, date_time):
    """Check if customer has exceeded concurrent and weekly reservation limits"""
    num_days_reserved_in_week = 0
    machine_reserved_at_same_time = False
    days_of_reservations_in_week = []
    for row in rows:
        # List days on which customer has reservations in the same week (between last Sunday and next Sunday)
        if date_time + datetime.timedelta(days=6 - date_time.weekday()) > row.date_time > date_time - datetime.timedelta(days=date_time.weekday()) and row.customer == reservation.customer:
            if row.date_time.weekday() not in days_of_reservations_in_week:
                days_of_reservations_in_week.append(row.date_time.weekday())
                num_days_reserved_in_week += 1
        # Include day of current reservation
        if date_time.weekday() not in days_of_reservations_in_week:
            days_of_reservations_in_week.append(date_time.weekday())
            num_days_reserved_in_week += 1
        # Check whether customer has reserved a machine at the same time
        if row.date_time == date_time and row.customer == reservation.customer and row.resource != 'workshop':
            machine_reserved_at_same_time = True
    # Customer must have reservations on at most 3 days in a week and should not be reserving 2 machines at the same time
    if num_days_reserved_in_week <= 3 and (reservation.resource == 'workshop' or not machine_reserved_at_same_time):
        return False
    else:
        return True


def calculate_costs(reservation, date_time):
    """Calculate total cost for reservation"""
    total_cost = 0.0
    # Calculate total cost and down payment and confirm reservation if valid
    discount_rate = 1.0
    # 25% discount if reserved 2 weeks in advance
    if date_time - datetime.timedelta(weeks=2) > datetime.datetime.now():
        discount_rate = 0.75
    for resc in resources:
        if resc.name == reservation.resource:
            total_cost += round(discount_rate * resc.cost, 2)
            return total_cost
    return total_cost


def calculate_refund(row):
    """Calculate refund amount for cancellation"""
    refund_amount = 0.0
    # Calculate refund (if any) and confirm cancellation if valid
    # 75% refund if cancelled 7 days in advance
    if (row.date_time - datetime.timedelta(days=2) > datetime.datetime.now()) or (row.date_time.weekday() in range(2) and row.date_time - datetime.timedelta(days=3) > datetime.datetime.now()):
        refund_amount += round(0.5 * row.cost, 2)
    # 50% refund if cancelled 2 days in advance
    elif row.date_time - datetime.timedelta(days=7) > datetime.datetime.now():
        refund_amount += round(0.75 * row.cost, 2)
    return refund_amount


def account_balance_addition_within_bounds(amount):
    """Check if addition to account balance is within bounds"""
    if 1 <= amount <= 25_000:
        return True
    else:
        return False


def get_formatted_list_of_start_times(date_old, start_time_old, end_time_old):
    """Get list of start times in format MM-DD-YYYY hh:mm from given date in format YYYY-MM-DD and start and end times in format hhmm"""
    start_times_new = []
    # Reformat date
    date_new = datetime.datetime.strftime(datetime.datetime.strptime(date_old, '%Y-%m-%d'), '%m-%d-%Y')
    # Loop to add start times of 30-minute blocks to list
    current_time = datetime.datetime.strptime(start_time_old, '%H:%M')
    while datetime.datetime.strftime(current_time, '%H:%M') != end_time_old:
        start_times_new.append(date_new + ' ' + datetime.datetime.strftime(current_time, '%H:%M'))
        current_time = current_time + datetime.timedelta(minutes=30)
    return start_times_new


def time_ends_with_00_or_30(input_time):
    """Check if given time ends with :00 or :30"""
    if datetime.datetime.strptime(input_time, '%H:%M').minute in (0, 30):
        return True
    return False

def time_compare(time1, time2):
    """Check if time1 is greater than time2 with times in format hh:mm"""
    return datetime.datetime.strptime(time1, '%H:%M') > datetime.datetime.strptime(time2, '%H:%M')
