from databases import Database
import sqlalchemy
import os
import hashlib
import uuid

# Contains functions for interacting with SQLite database

# Set database URL to production or test database according to environment variable
db_name = os.getenv('DB_NAME', 'production')
if db_name == 'test':
    DATABASE_URL = 'sqlite:///test_database.db'
else:
    DATABASE_URL = 'sqlite:///database.db'

# Databases to hold reservations and transactions
# https://fastapi.tiangolo.com/advanced/async-sql-databases/
metadata = sqlalchemy.MetaData()
reservations = sqlalchemy.Table(
    'reservations',
    metadata,
    sqlalchemy.Column('serial_num', sqlalchemy.String(length=36), primary_key=True),
    sqlalchemy.Column('date_time', sqlalchemy.DateTime),
    sqlalchemy.Column('resource', sqlalchemy.String(length=50)),
    sqlalchemy.Column('customer', sqlalchemy.String(length=50)),
    sqlalchemy.Column('reserver', sqlalchemy.String(length=50)),
    sqlalchemy.Column('cost', sqlalchemy.Float)
)
transactions = sqlalchemy.Table(
    'transactions',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.String(length=36), primary_key=True),
    sqlalchemy.Column('date_time', sqlalchemy.DateTime),
    sqlalchemy.Column('customer', sqlalchemy.String(length=50)),
    sqlalchemy.Column('amount', sqlalchemy.Float)
)
users = sqlalchemy.Table(
    'users',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.String(length=50), primary_key=True),
    sqlalchemy.Column('password_hash', sqlalchemy.String(length=128)),
    sqlalchemy.Column('password_salt', sqlalchemy.String(length=36)),
    sqlalchemy.Column('name', sqlalchemy.String(length=50)),
    sqlalchemy.Column('account_balance', sqlalchemy.Float),
    sqlalchemy.Column('activation', sqlalchemy.Boolean),
    sqlalchemy.Column('role', sqlalchemy.String(length=50))
)
settings = sqlalchemy.Table(
    'settings',
    metadata,
    sqlalchemy.Column('setting', sqlalchemy.String(length=50), primary_key=True),
    sqlalchemy.Column('value', sqlalchemy.Boolean)
)
database = Database(DATABASE_URL)
engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={'check_same_thread': False}
)
metadata.create_all(engine)


async def add_user(id, password, name, role):
    """Add new user with given id if not already existing"""
    await database.connect()
    query = users.select().where(users.c.id == id)
    row = await database.fetch_one(query=query)
    if not row:
        # Hash password according to SHA-512
        # https://stackoverflow.com/questions/9594125/salt-and-hash-a-password-in-python
        password_salt = uuid.uuid4().bytes
        password_hash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), password_salt, 100000)
        query = users.insert()
        values = {'id': id,
                  'password_hash': password_hash,
                  'password_salt': password_salt,
                  'name': name,
                  'account_balance': 0,
                  'activation': True,
                  'role': role
                  }
        await database.execute(query=query, values=values)
        await database.disconnect()
        return True
    else:
        await database.disconnect()
        return False


async def user_valid(id):
    """Check if given user ID is valid"""
    await database.connect()
    query = users.select().where(users.c.id == id)
    row = await database.fetch_one(query=query)
    await database.disconnect()
    if row:
        return True
    else:
        return False


async def password_valid(id, password):
    """Check if password is valid for a given user ID"""
    await database.connect()
    # Get hash of user's password
    query = users.select().where(users.c.id == id)
    row = await database.fetch_one(query=query)
    await database.disconnect()
    # Hash input password and compare
    password_hash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), row.password_salt, 100000)
    if password_hash == row.password_hash:
        return True
    else:
        return False


async def get_user(id):
    """Get user with a given ID"""
    await database.connect()
    query = users.select().where(users.c.id == id)
    row = await database.fetch_one(query=query)
    await database.disconnect()
    return row


async def list_users():
    """List all users"""
    await database.connect()
    query = users.select()
    rows = await database.fetch_all(query=query)
    await database.disconnect()
    return rows


async def remove_user(id):
    """Remove user with given ID"""
    await database.connect()
    query = users.delete().where(users.c.id == id)
    await database.execute(query=query)
    await database.disconnect()
    return True


async def edit_user_name(id, new_name):
    """Edit name of user with given ID"""
    await database.connect()
    query = users.update().where(users.c.id == id).values(name=new_name)
    await database.execute(query=query)
    await database.disconnect()
    return True


async def add_to_user_balance(id, amount):
    """Add to account balance of user with given ID"""
    await database.connect()
    # Get current account balance
    query = users.select().where(users.c.id == id)
    row = await database.fetch_one(query=query)
    # Calculate new account balance
    new_balance = row.account_balance + amount
    # Update account balance
    query = users.update().where(users.c.id == id).values(account_balance=new_balance)
    await database.execute(query=query)
    await database.disconnect()
    return True


async def edit_user_activation(id, activation):
    """Edit activation status of user with given ID"""
    await database.connect()
    query = users.update().where(users.c.id == id).values(activation=activation)
    await database.execute(query=query)
    await database.disconnect()
    return True


async def user_activated(id):
    """Check if user with given ID is activated"""
    await database.connect()
    query = users.select().where(users.c.id == id)
    row = await database.fetch_one(query=query)
    await database.disconnect()
    if row.activation:
        return True
    else:
        return False


async def list_reservations():
    """List all reservations"""
    await database.connect()
    query = reservations.select()
    rows = await database.fetch_all(query=query)
    await database.disconnect()
    return rows


async def list_transactions():
    """List all transactions"""
    await database.connect()
    query = transactions.select()
    rows = await database.fetch_all(query=query)
    await database.disconnect()
    return rows


async def list_reservations_for_customer(customer):
    """List all reservations for a particular customer"""
    await database.connect()
    query = reservations.select().where(reservations.c.customer == customer)
    rows = await database.fetch_all(query=query)
    await database.disconnect()
    return rows


async def list_transactions_for_customer(customer):
    """List all transactions for a particular customer"""
    await database.connect()
    query = transactions.select().where(transactions.c.customer == customer)
    rows = await database.fetch_all(query=query)
    await database.disconnect()
    return rows


async def get_reservation_with_serial_number(serial_num):
    """Get transaction with a particular serial number if it exists"""
    await database.connect()
    query = reservations.select().where(reservations.c.serial_num == serial_num)
    row = await database.fetch_one(query=query)
    await database.disconnect()
    return row


async def add_reservation(reservation_uuid, date_time, resource, customer, reserver, total_cost):
    """Add new reservation with given values"""
    await database.connect()
    query = reservations.insert()
    values = {
        'serial_num': reservation_uuid,
        'date_time': date_time,
        'resource': resource,
        'customer': customer,
        'reserver': reserver,
        'cost': total_cost
    }
    await database.execute(query=query, values=values)
    await database.disconnect()
    return True


async def add_transaction(transaction_uuid, date_time, customer, amount):
    """Add new transaction with given values"""
    await database.connect()
    query = transactions.insert()
    values = {
        'id': transaction_uuid,
        'date_time': date_time,
        'customer': customer,
        'amount': amount
    }
    await database.execute(query=query, values=values)
    await database.disconnect()
    return True


async def remove_reservation(serial_num):
    """Remove reservation with given serial number"""
    await database.connect()
    query = reservations.delete().where(reservations.c.serial_num == serial_num)
    await database.execute(query=query)
    await database.disconnect()
    return True


async def get_settings_value(setting):
    """Returns current value of setting (client_logins_allowed/client_adding_funds_allowed)"""
    await database.connect()
    query = settings.select().where(settings.c.setting == setting)
    row = await database.fetch_one(query=query)
    await database.disconnect()
    return row.value


async def set_settings_value(setting, value):
    """Sets value of setting (client_logins_allowed/client_adding_funds_allowed)"""
    await database.connect()
    query = settings.update().where(settings.c.setting == setting).values(value=value)
    await database.execute(query=query)
    await database.disconnect()
    return True


async def setting_name_valid(setting):
    """Check if given setting name is valid"""
    await database.connect()
    query = settings.select().where(settings.c.setting == setting)
    row = await database.fetch_one(query=query)
    await database.disconnect()
    if row:
        return True
    else:
        return False


async def list_holds():
    """List holds made for other facilities"""
    await database.connect()
    # Get list of remote facility manager IDs from users table
    query = users.select().where(users.c.role == 'remote facility manager')
    rows = await database.fetch_all(query=query)
    remote_facility_managers = []
    for row in rows:
        remote_facility_managers.append(row.id)
    # Get list of holds made by remote facility managers
    holds = []
    for remote_facility_manager in remote_facility_managers:
        query = reservations.select().where(reservations.c.reserver == remote_facility_manager)
        rows = await database.fetch_all(query=query)
        holds.extend(rows)
    await database.disconnect()
    return holds
