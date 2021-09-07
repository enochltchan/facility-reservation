import sqlite3
import json
import datetime
import uuid
import hashlib

"""Contains functions for pre-loading and clearing test data from test database"""

conn = sqlite3.connect('test_database.db')
curs = conn.cursor()


def add_test_data():
    """Add pre-loaded test data to test database"""
    # Add pre-loaded users
    with open('preloaded_test_data/test_users.json') as users_file:
        users_data = json.load(users_file)
    for id, user in users_data.items():
        password_salt = uuid.uuid4().bytes
        # Sets account balance to 0 and activation status to True
        password_hash = hashlib.pbkdf2_hmac('sha512', user['password'].encode('utf-8'), password_salt, 100000)
        curs.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)', (id, password_hash, password_salt, user['name'], 0.0, True, user['role']))
    # Add pre-loaded reservations
    with open('preloaded_test_data/test_reservations.json') as reservations_file:
        reservations_data = json.load(reservations_file)
    for serial_num, reservation in reservations_data.items():
        curs.execute('INSERT INTO reservations VALUES (?, ?, ?, ?, ?, ?)', (serial_num, datetime.datetime.strptime(reservation['date'], '%m-%d-%Y %H:%M'), reservation['resource'], reservation['customer'], reservation['reserver'], float(reservation['cost'])))
    # Add pre-loaded transactions
    with open('preloaded_test_data/test_transactions.json') as transactions_file:
        transactions_data = json.load(transactions_file)
    for id, transaction in transactions_data.items():
        curs.execute('INSERT INTO transactions VALUES (?, ?, ?, ?)', (id, datetime.datetime.strptime(transaction['date'], '%m-%d-%Y %H:%M'), transaction['customer'], float(transaction['amount'])))
    # Add pre-loaded settings
    with open('preloaded_test_data/test_settings.json') as settings_file:
        settings_data = json.load(settings_file)
    for setting, value in settings_data.items():
        curs.execute('INSERT INTO settings VALUES (?, ?)', (setting, eval(value)))
    conn.commit()


def clear_test_data():
    """Clear all test data from test database"""
    curs.execute('DELETE FROM users')
    curs.execute('DELETE FROM reservations')
    curs.execute('DELETE FROM transactions')
    curs.execute('DELETE FROM settings')
    conn.commit()


if __name__ == '__main__':
    # Uncomment to clear all test data or add pre-loaded test data
    # clear_test_data()
    # add_test_data()
    curs.close()
    conn.close()
