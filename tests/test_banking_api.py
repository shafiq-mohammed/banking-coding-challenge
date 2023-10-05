import pytest
from banking.api import app, bank_instance as bank
from unittest.mock import patch


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def obtain_jwt_token(client, email, password):
    """Helper function to login a user and return JWT token."""
    response = client.post('/api/v1/login', json={
        'email_address': email,
        'password': password
    })

    assert response.status_code == 200, f"Login failed with: {response.data}"

    # Assuming the key is 'access_token', adjust as necessary
    token = response.json.get('access_token')
    return token


def test_signup(client):
    response = client.post('/api/v1/signup', json={
        'full_name': 'Alice',
        'email_address': 'alice@example.com',
        'password': 'Alice123!'
    })
    assert response.status_code == 200
    assert response.json['msg'] == "Account created successfully"


def test_login_success(client):
    # Assume 'alice@example.com' is already signed up
    response = client.post('/api/v1/login', json={
        'email_address': 'alice@example.com',
        'password': 'Alice123!'
    })
    assert response.status_code == 200
    assert response.json['msg'] == "Logged in successfully"


def test_login_failure(client):
    # Set up: Ensure an account with bob@example.com exists
    client.post('/api/v1/signup', json={
        'email_address': 'bob@example.com',
        'password': 'correctpass'
    })

    # Now test with the wrong password
    response = client.post('/api/v1/login', json={
        'email_address': 'bob@example.com',
        'password': 'wrongpass'
    })
    assert response.status_code == 401
    assert response.json['msg'] == "Bad username or password"


def test_deposit(client):
    # User's credentials
    email = 'nomiikm@gmail.com'
    password = 'admin@123'

    # Create a user via the signup endpoint
    response = client.post('/api/v1/signup', json={
        'full_name': 'Test User',
        'email_address': email,
        'password': password
    })
    assert response.status_code == 200, f"Signup failed with: {response.data}"
    # Capture the account_id from signup response
    account_id = response.json.get('account_id')
    assert account_id, "Account ID not returned during signup"
    # Obtain a valid JWT token
    token = obtain_jwt_token(client, email, password)

    # Use the token for the deposit test
    headers = {
        'Authorization': f'JWT {token}'
    }
    response = client.post('/api/v1/deposit', headers=headers, json={
        'account_id': account_id,  # Ensure this UUID exists in your test setup
        'amount': 5000  # Amount in cents or your specific denomination
    })
    assert response.status_code == 200
    assert response.json['msg'] == "Amount deposited successfully"


def test_withdraw(client):
    # User's credentials
    email = 'nomiikzz@gmail.com'
    password = 'admin@123'

    # Create a user via the signup endpoint
    response = client.post('/api/v1/signup', json={
        'full_name': 'Test User',
        'email_address': email,
        'password': password
    })
    assert response.status_code == 200, f"Signup failed with: {response.data}"
    # Capture the account_id from signup response
    account_id = response.json.get('account_id')
    assert account_id, "Account ID not returned during signup"
    # Obtain a valid JWT token
    token = obtain_jwt_token(client, email, password)

    # Use the token for the deposit test
    headers = {
        'Authorization': f'JWT {token}'
    }
    client.post('/api/v1/deposit', headers=headers, json={
        'account_id': account_id,  # Ensure this UUID exists in your test setup
        'amount': 6000  # Amount in cents or your specific denomination
    })

    response = client.post('/api/v1/withdraw', headers=headers, json={
        'account_id': account_id,  # Ensure this UUID exists in your test setup
        'amount': 5000  # Amount in cents or your specific denomination
    })
    assert response.status_code == 200
    assert response.json['msg'] == "Amount withdrawn successfully"


def test_transfer(client):
    source_email = 'nomiikzz@gmail.com'
    source_password = 'admin@123'

    target_email = 'nomiikm@gmail.com'
    'admin@123'

    source_account_id = bank.get_account_id_by_email(source_email)
    target_account_id = bank.get_account_id_by_email(target_email)
    token = obtain_jwt_token(client, source_email, source_password)
    headers = {
        'Authorization': f'JWT {token}'
    }
    print(source_account_id, target_account_id)
    response = client.post('/api/v1/transfer', headers=headers, json={
        'source_account_id': source_account_id,
        'target_account_id': target_account_id,
        'amount': 100
    })
    assert response.status_code == 200
    assert response.json['msg'] == "Amount transferred successfully"


def test_negative_deposit(client):
    # Assuming the user is already created and
    # the JWT token is already obtained using helper functions.
    email = 'nomiikm@gmail.com'
    password = 'admin@123'
    account_id = bank.get_account_id_by_email(email)
    token = obtain_jwt_token(client, email, password)
    headers = {'Authorization': f'JWT {token}'}

    response = client.post('/api/v1/deposit', headers=headers, json={
        'account_id': account_id,
        'amount': -5000
    })

    assert response.status_code == 400
    assert response.json['error'] == "Invalid deposit amount"


def test_login_invalid_email(client):
    response = client.post('/api/v1/login', json={
        'email_address': 'doesnotexist@example.com',
        'password': 'randompass'
    })
    assert response.status_code == 401
    assert response.json['error'] == "Invalid credentials"


def test_overdraw(client):
    # Using the same setup as in the `test_withdraw` function.
    email = 'nomiikzz@gmail.com'
    password = 'admin@123'
    account_id = bank.get_account_id_by_email(email)
    token = obtain_jwt_token(client, email, password)
    headers = {'Authorization': f'JWT {token}'}

    # Trying to withdraw more than what was deposited.
    response = client.post('/api/v1/withdraw', headers=headers, json={
        'account_id': account_id,
        'amount': 10000
    })

    assert response.status_code == 400
    assert response.json['msg'] == "Insufficient funds"


def test_get_account_details(client):
    # Assuming the user is already created and
    # the JWT token is already obtained using helper functions.
    email = 'nomiikm@gmail.com'
    password = 'admin@123'
    token = obtain_jwt_token(client, email, password)
    headers = {'Authorization': f'JWT {token}'}

    response = client.get('/api/v1/account', headers=headers)

    assert response.status_code == 200
    assert 'balance' in response.json
    assert 'identity' in response.json


def test_signup_failure(client):
    # Mock the behavior of open_account
    # to simulate an error scenario
    with patch('banking.api.bank_instance.open_account', return_value=None):
        response = client.post('/api/v1/signup', json={
            'full_name': 'Failed User',
            'email_address': 'failed@example.com',
            'password': 'Failed123!'
        })
        assert response.status_code == 400
        assert response.json['msg'] == "Account creation failed"


def test_login_generic_exception_handling(client):
    # An exception to simulate an unexpected error
    class UnexpectedError(Exception):
        pass

    # Mock the get_account_id_by_email to raise the UnexpectedError
    with patch('banking.api.bank_instance.get_account_id_by_email',
               side_effect=UnexpectedError("unexpected error")):
        # Making the request
        response = client.post('/api/v1/login', json={
            'email_address': 'user@example.com',
            'password': 'correctpassword'
        })

        # Assertions
        assert response.status_code == 400
        assert response.json['error'] == "An error occurred: unexpected error"


def test_deposit_generic_exception_handling(client):
    # An exception to simulate an unexpected error
    class UnexpectedError(Exception):
        pass

    # Mock the deposit method to raise the UnexpectedError
    with patch('banking.api.bank_instance.deposit',
               side_effect=UnexpectedError("unexpected deposit error")):
        email = 'nomiikm@gmail.com'
        password = 'admin@123'
        account_id = bank.get_account_id_by_email(email)
        token = obtain_jwt_token(client, email, password)
        headers = {'Authorization': f'JWT {token}'}
        # Making the request
        response = client.post('/api/v1/deposit', headers=headers, json={
            'account_id': account_id,
            'amount': 100
        })
        print(response.data)

        # Assertions
        assert response.status_code == 400
        assert response.json['msg'] == "unexpected deposit error"


def test_transfer_account_not_found(client):
    source_email = 'nomiikzz@gmail.com'
    source_password = 'admin@123'
    source_account = bank.get_account_id_by_email(source_email)
    non_existent_target_account_id = "0db7b668-2856-4c86-83cf-a0b42c80d935"
    token = obtain_jwt_token(client, source_email, source_password)

    response = client.post('/api/v1/transfer',
                           headers={"Authorization": f"JWT {token}"}, json={
                            'source_account_id': str(source_account),
                            'target_account_id': non_existent_target_account_id,
                            'amount': 100
                            })

    assert response.status_code == 404
    assert response.json["error"] == f"Account not found: {non_existent_target_account_id}"


def test_transfer_insufficient_funds(client):
    source_email = 'nomiikzz@gmail.com'
    source_password = 'admin@123'
    target_email = 'nomiikm@gmail.com'
    # Assume you have functions to setup mock accounts and get a valid JWT token
    source_account = bank.get_account_id_by_email(source_email)
    target_account = bank.get_account_id_by_email(target_email)
    token = obtain_jwt_token(client, source_email, source_password)

    response = client.post('/api/v1/transfer', headers={"Authorization": f"JWT {token}"}, json={
        'source_account_id': str(source_account),
        'target_account_id': str(target_account),
        'amount': 500000  # An amount greater than the source account balance
    })

    assert response.status_code == 400
    assert response.json["error"] == "Insufficient funds"


def test_transfer_generic_exception(client):
    source_email = 'nomiikzz@gmail.com'
    source_password = 'admin@123'
    target_email = 'nomiikm@gmail.com'
    # Assume you have functions to setup mock accounts and get a valid JWT token
    source_account = bank.get_account_id_by_email(source_email)
    target_account = bank.get_account_id_by_email(target_email)
    token = obtain_jwt_token(client, source_email, source_password)

    with patch('banking.api.bank_instance.transfer', side_effect=Exception("Some generic error")):
        response = client.post('/api/v1/transfer', headers={"Authorization": f"JWT {token}"}, json={
            'source_account_id': str(source_account),
            'target_account_id': str(target_account),
            'amount': 100
        })

        assert response.status_code == 400
        assert response.json["msg"] == "Some generic error"


def test_get_account_details_generic_exception(client):
    source_email = 'nomiikzz@gmail.com'
    source_password = 'admin@123'
    # Assume you have functions to setup mock accounts and get a valid JWT token
    token = obtain_jwt_token(client, source_email, source_password)

    # Assuming that bank().get_account is the method that might throw an unexpected exception.
    with patch('banking.api.bank_instance.get_account', side_effect=Exception("Some generic error")):
        response = client.get('/api/v1/account', headers={"Authorization": f"JWT {token}"})

        assert response.status_code == 400
        assert response.json["msg"] == "Some generic error"
