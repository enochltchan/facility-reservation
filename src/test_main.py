from fastapi.testclient import TestClient
from main import app
import main
from models.models_main import ReservationModel, UserModel
import api_sqlite
import api_sqlite_test_data
import pytest
import asyncio
import re
from collections import namedtuple
import unittest.mock as mock
import datetime
from databases import Database
import os
import sqlite3

# source for async mocking: https://dino.codes/posts/mocking-asynchronous-functions-python/
# Note: set environment variable to "test" before running pytest

client = TestClient(app)

### API Tests
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {'message': 'Welcome to MPCS, Inc. Team 1 Reservation System!'}

## add_user
@pytest.fixture()
def mock_add_user(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.add_user', return_value=future)
    return future
def test_api_add_user_successful(mock_add_user):
    mock_add_user.set_result(True)
    actual = client.post("/users", json={'id': '', 'password': '', 'name': '', 'role': 'facility manager'})
    expected = {'message': 'User added successfully'}
    assert actual.status_code == 201
    assert actual.json() == expected
def test_api_add_user_unsuccessful_alreadyexists(mock_add_user):
    mock_add_user.set_result(False)
    actual = client.post("/users", json={'id': '', 'password': '', 'name': '', 'role': 'facility manager'})
    expected = {'detail': 'User already exists'}
    assert actual.status_code == 400
    assert actual.json() == expected
def test_api_add_user_unsuccessful_wrongrole(mock_add_user):
    mock_add_user.set_result(False)
    actual = client.post("/users", json={'id': '', 'password': '', 'name': '', 'role': ''})
    expected = {'detail': 'User must be one of facility manager, client or remote facility manager'}
    assert actual.status_code == 400
    assert actual.json() == expected

## list_users
@pytest.fixture()
def mock_list_users(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.list_users', return_value=future)
    return future
def test_api_list_users_successful(mock_list_users):
    User = namedtuple('User', ['id', 'password_hash', 'password_salt', 'name', 'account_balance', 'activation', 'role'])
    user1 = User('1', '', '', 'User1', 100, False, '')
    user2 = User('2', '', '', 'User2', 200, True, '')
    mock_list_users.set_result([user1, user2])
    actual = client.get("/users")
    expected = {'1': {'name': 'User1', 'account_balance': 100, 'activation status': False, 'role': ''},
    '2': {'name': 'User2', 'account_balance': 200, 'activation status': True, 'role': ''}}
    assert actual.status_code == 200
    assert actual.json() == expected
def test_api_list_users_unsuccessful(mock_list_users):
    mock_list_users.set_result([])
    actual = client.get("/users")
    expected = {'detail': 'No users found'}
    assert actual.status_code == 404
    assert actual.json() == expected

## get_user_details
@pytest.fixture()
def mock_handle_invalid_user(mocker):
    future = asyncio.Future()
    mocker.patch('main.handle_invalid_user', return_value=future)
    return future
@pytest.fixture()
def mock_get_user(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.get_user', return_value=future)
    return future
def test_api_get_user_details_successful(mock_handle_invalid_user, mock_get_user):
    mock_handle_invalid_user.set_result(True)
    User = namedtuple('User', ['id', 'password_hash', 'password_salt', 'name', 'account_balance', 'activation', 'role'])
    user1 = User('1', '', '', 'User1', 100, False, '')
    mock_get_user.set_result(user1)
    actual = client.get("/users/1")
    expected = {'name': 'User1', 'account balance': 100, 'activation status': False, 'role': ''}
    assert actual.status_code == 200
    assert actual.json() == expected
def test_api_get_user_details_unsuccessful(mock_handle_invalid_user, mock_get_user):
    mock_handle_invalid_user.set_result(True)
    mock_get_user.set_result([])
    actual = client.get("/users/1")
    expected = {'detail': 'User not found'}
    assert actual.status_code == 404
    assert actual.json() == expected

## delete_user
def test_api_delete_user_successful(mock_handle_invalid_user):
    mock_handle_invalid_user.set_result(True)
    actual = client.delete("/users/1")
    expected = {'message': 'User removed successfully'}
    assert actual.status_code == 200
    assert actual.json() == expected

## edit_user_name
@pytest.fixture()
def mock_edit_user_name(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.edit_user_name', return_value=future)
    return future
def test_api_edit_user_name_successful(mock_handle_invalid_user, mock_edit_user_name):
    mock_handle_invalid_user.set_result(True)
    mock_edit_user_name.set_result(True)
    actual = client.put("/users/1/name", json={'name': 'dave'})
    expected = {'message': 'User name edited successfully'}
    assert actual.status_code == 200
    assert actual.json() == expected

## add_to_user_balance
@pytest.fixture()
def mock_add_to_user_balance(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.add_to_user_balance', return_value=future)
    return future
def test_api_add_to_user_balance_successful(mock_handle_invalid_user, mock_add_to_user_balance, mock_get_user):
    mock_handle_invalid_user.set_result(True)
    with mock.patch('facility.account_balance_addition_within_bounds', return_value=True):
        mock_add_to_user_balance.set_result(True)
        User = namedtuple('User', ['id', 'password_hash', 'password_salt', 'name', 'account_balance', 'activation', 'role'])
        user1 = User('1', '', '', 'User1', 100, False, '')
        mock_get_user.set_result(user1)
        actual = client.put("/users/1/account_balance", json={'amount': 50})
        expected = {'message': 'Funds added successfully, Current account balance: $100'}
        assert actual.status_code == 200
        assert actual.json() == expected
def test_api_add_to_user_balance_unsuccessful(mock_handle_invalid_user):
    mock_handle_invalid_user.set_result(True)
    with mock.patch('facility.account_balance_addition_within_bounds', return_value=False):
        actual = client.put("/users/1/account_balance", json={'amount': 26000})
        expected = {'detail': 'Amount not between $1 and $25,000'}
        assert actual.status_code == 400
        assert actual.json() == expected

## change_user_activation
@pytest.fixture()
def mock_edit_user_activation(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.edit_user_activation', return_value=future)
    return future
def test_api_change_user_activation_activationsuccessful(mock_handle_invalid_user, mock_edit_user_activation):
    mock_handle_invalid_user.set_result(True)
    mock_edit_user_activation.set_result(True)
    actual = client.put("/users/1/activation", json={'id': '1', 'activation': True})
    expected = {'message': 'User activated successfully'}
    assert actual.status_code == 200
    assert actual.json() == expected
def test_api_change_user_activation_deactivationsuccessful(mock_handle_invalid_user, mock_edit_user_activation):
    mock_handle_invalid_user.set_result(True)
    mock_edit_user_activation.set_result(True)
    actual = client.put("/users/1/activation", json={'id': '1','activation': False})
    expected = {'message': 'User deactivated successfully'}
    assert actual.status_code == 200
    assert actual.json() == expected

## list_reservations
@pytest.fixture()
def mock_list_reservations(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.list_reservations', return_value=future)
    return future
def test_api_list_reservations_nonempty(mock_list_reservations):
    res = namedtuple('res', ['serial_num', 'date_time', 'resource', 'customer', 'cost'])
    res1 = res('1', datetime.datetime(2021,10,11,12,00), 'mini microvac', 'tester1', 50)
    res2 = res('2', datetime.datetime(2021,10,11,12,30), 'mini microvac', 'tester2', 50)
    mock_list_reservations.set_result([res1, res2])
    actual = client.get("/reservations")
    expected = {'1': {'date': '10-11-2021 12:00', 'resource': 'mini microvac', 'customer': 'tester1'},
    '2': {'date': '10-11-2021 12:30', 'resource': 'mini microvac', 'customer': 'tester2'}}
    assert actual.status_code == 200
    assert actual.json() == expected
def test_api_list_reservations_empty(mock_list_reservations):
    mock_list_reservations.set_result(False)
    actual = client.get("/reservations")
    expected = {'detail': 'No reservations found'}
    assert actual.status_code == 404
    assert actual.json() == expected

## get_reservation
@pytest.fixture()
def mock_get_reservation_with_serial_number(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.get_reservation_with_serial_number', return_value=future)
    return future
def test_api_get_reservation_nonempty(mock_get_reservation_with_serial_number):
    res = namedtuple('res', ['serial_num', 'date_time', 'resource', 'customer', 'cost'])
    res1 = res('1', datetime.datetime(2021,10,11,12,00), 'mini microvac', 'tester1', 50)
    mock_get_reservation_with_serial_number.set_result(res1)
    actual = client.get("/reservations/serial_num/test_serial_num")
    expected = {'date': '10-11-2021 12:00', 'resource': 'mini microvac'}
    assert actual.status_code == 200
    assert actual.json() == expected
def test_api_get_reservation_empty(mock_get_reservation_with_serial_number):
    mock_get_reservation_with_serial_number.set_result([])
    actual = client.get("/reservations/serial_num/test_serial_num")
    expected = {'detail': 'Reservation not found'}
    assert actual.status_code == 404
    assert actual.json() == expected

## list_reservations_for_customer
@pytest.fixture()
def mock_list_reservations_for_customer(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.list_reservations_for_customer', return_value=future)
    return future
def test_api_list_reservations_for_customer_nonempty(mock_handle_invalid_user, mock_list_reservations_for_customer):
    mock_handle_invalid_user.set_result(True)
    res = namedtuple('res', ['serial_num', 'date_time', 'resource', 'customer', 'cost'])
    res1 = res('1', datetime.datetime(2021,10,11,12,00), 'mini microvac', 'tester1', 50)
    res2 = res('2', datetime.datetime(2021,10,11,12,30), 'mini microvac', 'tester1', 50)
    mock_list_reservations_for_customer.set_result([res1, res2])
    actual = client.get("/reservations/tester1")
    expected = {'1': {'date': '10-11-2021 12:00', 'resource': 'mini microvac'},
    '2': {'date': '10-11-2021 12:30', 'resource': 'mini microvac'}}
    assert actual.status_code == 200
    assert actual.json() == expected
def test_api_list_reservations_for_customer_empty(mock_handle_invalid_user, mock_list_reservations_for_customer):
    mock_handle_invalid_user.set_result(True)
    mock_list_reservations_for_customer.set_result([])
    actual = client.get("/reservations/tester1")
    expected = {'detail': 'No reservations found for customer'}
    assert actual.status_code == 404
    assert actual.json() == expected
    
## list_transactions
@pytest.fixture()
def mock_list_transactions(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.list_transactions', return_value=future)
    return future
def test_api_list_transactions_nonempty(mock_list_transactions):
    trans = namedtuple('trans', ['id', 'date_time', 'customer', 'amount'])
    trans1 = trans('1', datetime.datetime(2021,10,11,12,00), 'tester1', 50)
    trans2 = trans('2', datetime.datetime(2021,10,11,12,30), 'tester2', 50)
    mock_list_transactions.set_result([trans1, trans2])
    actual = client.get("/transactions")
    expected = {'1': {'date': '10-11-2021 12:00', 'customer': 'tester1', 'amount': '50'},
    '2': {'date': '10-11-2021 12:30', 'customer': 'tester2', 'amount': '50'}}
    assert actual.status_code == 200
    assert actual.json() == expected
def test_api_list_transactions_empty(mock_list_transactions):
    mock_list_transactions.set_result([])
    actual = client.get("/transactions")
    expected = {'detail': 'No transactions found'}
    assert actual.status_code == 404
    assert actual.json() == expected

## list_transactions_for_customer
@pytest.fixture()
def mock_list_transactions_for_customer(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.list_transactions_for_customer', return_value=future)
    return future
def test_api_list_transactions_for_customer_nonempty(mock_handle_invalid_user, mock_list_transactions_for_customer):
    mock_handle_invalid_user.set_result(True)
    trans = namedtuple('trans', ['id', 'date_time', 'customer', 'amount'])
    trans1 = trans('1', datetime.datetime(2021,10,11,12,00), 'tester1', 50)
    trans2 = trans('2', datetime.datetime(2021,10,11,12,30), 'tester1', 50)
    mock_list_transactions_for_customer.set_result([trans1, trans2])
    actual = client.get("/transactions/tester1")
    expected = {'1': {'date': '10-11-2021 12:00', 'amount': '50'},
    '2': {'date': '10-11-2021 12:30', 'amount': '50'}}
    assert actual.status_code == 200
    assert actual.json() == expected
def test_api_list_transactions_for_customer_empty(mock_handle_invalid_user, mock_list_transactions_for_customer):
    mock_handle_invalid_user.set_result(True)
    mock_list_transactions_for_customer.set_result([])
    actual = client.get("/transactions/tester1")
    expected = {'detail': 'No transactions found for customer'}
    assert actual.status_code == 404
    assert actual.json() == expected
    
## validate
@pytest.fixture()
def mock_user_valid(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.user_valid', return_value=future)
    return future
@pytest.fixture()
def mock_password_valid(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.password_valid', return_value=future)
    return future
def test_api_validate_true(mock_user_valid, mock_password_valid):
    mock_user_valid.set_result(True)
    mock_password_valid.set_result(True)
    actual = client.post("/validity", json={'id': '', 'password': ''})
    expected = {'validity': True}
    assert actual.status_code == 200
    assert actual.json() == expected
def test_api_validate_false(mock_user_valid, mock_password_valid):
    mock_user_valid.set_result(False)
    actual = client.post("/validity", json={'id': '', 'password': ''})
    expected = {'validity': False}
    assert actual.status_code == 200
    assert actual.json() == expected

## get_setting
@pytest.fixture()
def mock_handle_invalid_setting(mocker):
    future = asyncio.Future()
    mocker.patch('main.handle_invalid_setting', return_value=future)
    return future
@pytest.fixture()
def mock_get_settings_value(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.get_settings_value', return_value=future)
    return future
def test_api_get_setting(mock_handle_invalid_setting, mock_get_settings_value):
    mock_handle_invalid_setting.set_result(True)
    setting = namedtuple('setting', ['setting', 'value'])
    setting1 = setting('', True)
    mock_get_settings_value.set_result(setting1)
    actual = client.get("/settings/test_setting")
    expected = {'value': ['', True]}
    assert actual.status_code == 200
    assert actual.json() == expected

## set_setting
@pytest.fixture()
def mock_set_settings_value(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.set_settings_value', return_value=future)
    return future
def test_api_set_setting(mock_handle_invalid_setting, mock_set_settings_value):
    mock_handle_invalid_setting.set_result(True)
    mock_set_settings_value.set_result(True)
    actual = client.post("/settings/test_setting", json={'value': True})
    expected = {'message': 'Modification successful'}
    assert actual.status_code == 200
    assert actual.json() == expected

## list_holds
@pytest.fixture()
def mock_list_holds(mocker):
    future = asyncio.Future()
    mocker.patch('api_sqlite.list_holds', return_value=future)
    return future
def test_api_list_holds_nonempty(mock_list_holds):
    res = namedtuple('res', ['serial_num', 'date_time', 'resource', 'customer', 'reserver', 'total_cost'])
    res1 = res('1', datetime.datetime(2021,10,11,12,00), 'mini microvac', 'tester1', 'tester1_remote', 50)
    res2 = res('2', datetime.datetime(2021,10,11,12,30), 'mini microvac', 'tester1', 'tester1_remote', 50)
    mock_list_holds.set_result([res1, res2])
    actual = client.get("/hold")
    expected = {'1': {'date': '10-11-2021 12:00', 'resource': 'mini microvac', 'customer': 'tester1', 'reserver': 'tester1_remote'},
    '2': {'date': '10-11-2021 12:30', 'resource': 'mini microvac', 'customer': 'tester1', 'reserver': 'tester1_remote'}}
    assert actual.status_code == 200
    assert actual.json() == expected
def test_api_list_holds_empty(mock_list_holds):
    mock_list_holds.set_result([])
    actual = client.get("/hold")
    expected = {'detail': 'No holds found'}
    assert actual.status_code == 404
    assert actual.json() == expected

### Database Tests
def delete_users_from_test_db():
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('DELETE FROM users')
    conn.commit()
    curs.close()
    conn.close()

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_add_user_successful():
    delete_users_from_test_db()
    actual = await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    expected = True
    assert actual == expected
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT id FROM users')
    row = [row[0] for row in curs]
    actual = row[0]
    curs.close()
    conn.close()
    expected = 'test_id'
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_add_user_unsuccessful():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    actual = await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    expected = False
    assert actual == expected


@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_user_valid_valid():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    actual = await api_sqlite.user_valid('test_id')
    expected = True
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_user_valid_invalid():
    delete_users_from_test_db()
    actual = await api_sqlite.user_valid('test_id')
    expected = False
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_password_valid_valid():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    actual = await api_sqlite.password_valid('test_id', 'test_pass')
    expected = True
    assert actual == expected


@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_password_valid_invalid():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    actual = await api_sqlite.password_valid('test_id', 'test_pass_invalid')
    expected = False
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_get_user():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    actual = await api_sqlite.get_user('test_id')
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT * FROM users WHERE id = "test_id"')
    expected = [row for row in curs][0]
    curs.close()
    conn.close()
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_list_users():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id1', 'test_pass1', 'test_name1', 'facility_manager')
    await api_sqlite.add_user('test_id2', 'test_pass2', 'test_name2', 'remote facility_manager')
    actual = await api_sqlite.list_users()
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT * FROM users')
    expected = [row for row in curs]
    curs.close()
    conn.close()
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_remove_user():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    await api_sqlite.remove_user('test_id')
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT * FROM users')
    actual = [row for row in curs]
    curs.close()
    conn.close()
    expected = []
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_edit_user_name():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    await api_sqlite.edit_user_name('test_id', 'new_test_name')
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT name FROM users WHERE id = "test_id"')
    row = [row[0] for row in curs]
    curs.close()
    conn.close()
    actual = row[0]
    expected = 'new_test_name'
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_add_to_user_balance():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    await api_sqlite.add_to_user_balance('test_id', 50)
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT account_balance FROM users WHERE id = "test_id"')
    row = [row[0] for row in curs]
    curs.close()
    conn.close()
    actual = row[0]
    expected = 50
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_edit_user_activation():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    await api_sqlite.edit_user_activation('test_id', False)
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT activation FROM users WHERE id = "test_id"')
    row = [row[0] for row in curs]
    curs.close()
    conn.close()
    actual = row[0]
    expected = False
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_user_activated_activated():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    actual = await api_sqlite.user_activated('test_id')
    expected = True
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_user_activated_deactivated():
    delete_users_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'facility_manager')
    await api_sqlite.edit_user_activation('test_id', False)
    actual = await api_sqlite.user_activated('test_id')
    expected = False
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_list_reservations():
    delete_reservations_from_test_db()
    await api_sqlite.add_reservation('uuid1', datetime.datetime(2021,10,11,12,00), 'mini microvac', 'test_customer1', 'test_reserver1', 50)
    await api_sqlite.add_reservation('uuid2', datetime.datetime(2021,10,12,12,00), 'mini microvac', 'test_customer2', 'test_reserver2', 50)
    rows = await api_sqlite.list_reservations()
    actual = [row[0] for row in rows]
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT * FROM reservations')
    expected = [row[0] for row in curs]
    curs.close()
    conn.close()
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_list_transactions():
    delete_transactions_from_test_db()
    await api_sqlite.add_transaction('uuid1', datetime.datetime(2021,10,11,12,00), 'test_customer1', 50)
    await api_sqlite.add_transaction('uuid2', datetime.datetime(2021,10,12,12,00), 'test_customer2', 50)
    rows = await api_sqlite.list_transactions()
    actual = [row[0] for row in rows]
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT * FROM transactions')
    expected = [row[0] for row in curs]
    curs.close()
    conn.close()
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_list_reservations_for_customer():
    delete_reservations_from_test_db()
    await api_sqlite.add_reservation('uuid1', datetime.datetime(2021,10,11,12,00), 'mini microvac', 'test_customer1', 'test_reserver1', 50)
    await api_sqlite.add_reservation('uuid2', datetime.datetime(2021,10,12,12,00), 'mini microvac', 'test_customer2', 'test_reserver2', 50)
    rows = await api_sqlite.list_reservations_for_customer('test_customer2')
    actual = [row[0] for row in rows]
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT * FROM reservations WHERE customer == "test_customer2"')
    expected = [row[0] for row in curs]
    curs.close()
    conn.close()
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_list_transactions_for_customer():
    delete_transactions_from_test_db()
    await api_sqlite.add_transaction('uuid1', datetime.datetime(2021,10,11,12,00), 'test_customer1', 50)
    await api_sqlite.add_transaction('uuid2', datetime.datetime(2021,10,12,12,00), 'test_customer2', 50)
    rows = await api_sqlite.list_transactions_for_customer('test_customer2')
    actual = [row[0] for row in rows]
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT * FROM transactions WHERE customer == "test_customer2"')
    expected = [row[0] for row in curs]
    curs.close()
    conn.close()
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_get_reservation_with_serial_number():
    delete_reservations_from_test_db()
    await api_sqlite.add_reservation('uuid1', datetime.datetime(2021,10,11,12,00), 'mini microvac', 'test_customer1', 'test_reserver1', 50)
    await api_sqlite.add_reservation('uuid2', datetime.datetime(2021,10,12,12,00), 'mini microvac', 'test_customer2', 'test_reserver2', 50)
    row = await api_sqlite.get_reservation_with_serial_number('uuid2')
    actual = row[0]
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT * FROM reservations WHERE serial_num == "uuid2"')
    expected = [row[0] for row in curs][0]
    curs.close()
    conn.close()
    assert actual == expected

def delete_reservations_from_test_db():
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('DELETE FROM reservations')
    conn.commit()
    curs.close()
    conn.close()

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_add_reservation():
    delete_reservations_from_test_db()
    actual = await api_sqlite.add_reservation("1", datetime.datetime(2021,10,11,12,00), "mini microvac", "tester1", "tester1", 50)
    expected = True
    assert actual == expected
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT serial_num FROM reservations')
    row = [row[0] for row in curs]
    conn.commit()
    curs.close()
    conn.close()
    actual = row[0]
    expected = "1"
    assert actual == expected

def delete_transactions_from_test_db():
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('DELETE FROM transactions')
    conn.commit()
    curs.close()
    conn.close()

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_add_transaction():
    delete_transactions_from_test_db()
    actual = await api_sqlite.add_transaction("1", datetime.datetime(2021,10,11,12,00), "tester1", 50)
    expected = True
    assert actual == expected
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT id FROM transactions')
    row = [row[0] for row in curs]
    conn.commit()
    curs.close()
    conn.close()
    actual = row[0]
    expected = "1"
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_remove_reservation():
    delete_reservations_from_test_db()
    await api_sqlite.add_reservation("1", datetime.datetime(2021,10,11,12,00), "mini microvac", "tester1", "tester1", 50)
    actual = await api_sqlite.remove_reservation("1")
    expected = True
    assert actual == expected
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT serial_num FROM reservations')
    row = [row[0] for row in curs]
    conn.commit()
    curs.close()
    conn.close()
    actual = row
    expected = []
    assert actual == expected

def delete_settings_from_test_db():
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('DELETE FROM settings')
    conn.commit()
    curs.close()
    conn.close()

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_setting_name_valid():
    delete_settings_from_test_db()
    actual = await api_sqlite.setting_name_valid("test_invalid_setting")
    expected = False
    assert actual == expected

@mock.patch.dict(os.environ, {"DB_NAME": "test"})
@pytest.mark.asyncio
async def test_db_list_holds():
    delete_users_from_test_db()
    delete_reservations_from_test_db()
    await api_sqlite.add_user('test_id', 'test_pass', 'test_name', 'remote facility manager')
    await api_sqlite.add_reservation('uuid1', datetime.datetime(2021,10,11,12,00), 'mini microvac', 'test_customer1', 'test_id', 50)
    await api_sqlite.add_reservation('uuid2', datetime.datetime(2021,10,12,12,00), 'mini microvac', 'test_customer2', 'test_reserver2', 50)
    rows = await api_sqlite.list_holds()
    actual = [row[0] for row in rows]
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT * FROM reservations WHERE reserver == "test_id"')
    expected = [row[0] for row in curs]
    curs.close()
    conn.close()
    assert actual == expected

### End-to-end integration tests
def test_e2e_add_user_successful():
    delete_users_from_test_db()
    actual = client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    expected = {'message': 'User added successfully'}
    assert actual.status_code == 201
    assert actual.json() == expected
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT id FROM users')
    row = [row[0] for row in curs]
    actual = row[0]
    curs.close()
    conn.close()
    expected = 'test_id'
    assert actual == expected

def test_e2e_add_user_unsuccessful_alreadyexists():
    delete_users_from_test_db()
    client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    actual = client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    expected = {'detail': 'User already exists'}
    assert actual.status_code == 400
    assert actual.json() == expected
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT id FROM users')
    row = [row[0] for row in curs]
    actual = row[0]
    curs.close()
    conn.close()
    expected = 'test_id'
    assert actual == expected

def test_e2e_add_user_unsuccessful_wrongrole():
    delete_users_from_test_db()
    actual = client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'test_wrong_role'})
    expected = {'detail': 'User must be one of facility manager, client or remote facility manager'}
    assert actual.status_code == 400
    assert actual.json() == expected
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT id FROM users')
    row = [row[0] for row in curs]
    actual = row
    curs.close()
    conn.close()
    expected = []
    assert actual == expected

def test_e2e_list_users_successful():
    delete_users_from_test_db()
    client.post("/users", json={'id': 'test_id1', 'password': 'test_pass1', 'name': 'test_name1', 'role': 'facility manager'})
    client.post("/users", json={'id': 'test_id2', 'password': 'test_pass2', 'name': 'test_name2', 'role': 'client'})
    actual = client.get("/users")
    expected = {'test_id1': {'name': 'test_name1', 'account_balance': 0, 'activation status': True, 'role': 'facility manager'},
    'test_id2': {'name': 'test_name2', 'account_balance': 0, 'activation status': True, 'role': 'client'}}
    assert actual.status_code == 200
    assert actual.json() == expected

def test_e2e_list_users_unsuccessful():
    delete_users_from_test_db()
    actual = client.get("/users")
    expected = {'detail': 'No users found'}
    assert actual.status_code == 404
    assert actual.json() == expected

def test_e2e_get_user_details_successful():
    delete_users_from_test_db()
    client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    actual = client.get("/users/test_id")
    expected = {'name': 'test_name', 'account balance': 0, 'activation status': True, 'role': 'facility manager'}
    assert actual.status_code == 200
    assert actual.json() == expected

def test_e2e_delete_user_successful():
    delete_users_from_test_db()
    client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    actual = client.delete("/users/test_id")
    expected = {'message': 'User removed successfully'}
    assert actual.status_code == 200
    assert actual.json() == expected
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT id FROM users WHERE id = "test_id"')
    row = [row[0] for row in curs]
    actual = row
    curs.close()
    conn.close()
    expected = []
    assert actual == expected

def test_e2e_edit_user_name_successful():
    delete_users_from_test_db()
    client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    actual = client.put("/users/test_id/name", json={'name': 'new_test_name'})
    expected = {'message': 'User name edited successfully'}
    assert actual.status_code == 200
    assert actual.json() == expected
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT name FROM users WHERE id = "test_id"')
    row = [row[0] for row in curs]
    actual = row[0]
    curs.close()
    conn.close()
    expected = 'new_test_name'
    assert actual == expected

def test_e2e_add_to_user_balance_successful():
    delete_users_from_test_db()
    client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    actual = client.put("/users/test_id/account_balance", json={'amount': 50})
    expected = {'message': 'Funds added successfully, Current account balance: $50.0'}
    assert actual.status_code == 200
    assert actual.json() == expected

def test_e2e_add_to_user_balance_unsuccessful():
    delete_users_from_test_db()
    client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    actual = client.put("/users/test_id/account_balance", json={'amount': 26000})
    expected = {'detail': 'Amount not between $1 and $25,000'}
    assert actual.status_code == 400
    assert actual.json() == expected

def test_e2e_change_user_activation_activationsuccessful():
    delete_users_from_test_db()
    client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    actual = client.put("/users/test_id/activation", json={'id': 'test_id', 'activation': True})
    expected = {'message': 'User activated successfully'}
    assert actual.status_code == 200
    assert actual.json() == expected
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT activation FROM users WHERE id = "test_id"')
    row = [row[0] for row in curs]
    actual = row[0]
    curs.close()
    conn.close()
    expected = True
    assert actual == expected

def test_e2e_change_user_activation_deactivationsuccessful():
    delete_users_from_test_db()
    client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    actual = client.put("/users/test_id/activation", json={'id': 'test_id', 'activation': False})
    expected = {'message': 'User deactivated successfully'}
    assert actual.status_code == 200
    assert actual.json() == expected
    conn = sqlite3.connect('test_database.db')
    curs = conn.cursor()
    curs.execute('SELECT activation FROM users WHERE id = "test_id"')
    row = [row[0] for row in curs]
    actual = row[0]
    curs.close()
    conn.close()
    expected = False
    assert actual == expected

def test_e2e_validite_valid():
    delete_users_from_test_db()
    client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    actual = client.post("/validity", json={'id': 'test_id', 'password': 'test_pass'})
    expected = {'validity': True}
    assert actual.status_code == 200
    assert actual.json() == expected

def test_e2e_validite_invalid():
    delete_users_from_test_db()
    client.post("/users", json={'id': 'test_id', 'password': 'test_pass', 'name': 'test_name', 'role': 'facility manager'})
    actual = client.post("/validity", json={'id': 'test_id', 'password': 'invalid_test_pass'})
    expected = {'validity': False}
    assert actual.status_code == 200
    assert actual.json() == expected
