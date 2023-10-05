# coding=utf-8
# flake8: noqa E402
from uuid import UUID
from eventsourcing.application import AggregateNotFound
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, _default_jwt_encode_handler, current_identity  # type: ignore
from banking.domainmodel import AccountNotFoundError, InsufficientFundsError
from banking.applicationmodel import Bank

app = Flask(__name__)
app.config["SECRET_KEY"] = "super-secret"

bank_instance = Bank()


# Utility to get the bank instance
def bank() -> Bank:
    return bank_instance


class User:
    id: str


# Authenticate user function for JWT
def authenticate(email, password):
    try:
        account_id = bank().get_account_id_by_email(email)
        account = bank().get_account(account_id)
        if account and account.check_password(password):
            user_instance = User()
            user_instance.id = str(account.id)
            return user_instance
    except (AccountNotFoundError, AggregateNotFound):
        return None


def identity(payload):
    user_id = payload['identity']
    user_instance = User()
    user_instance.id = user_id
    return user_instance


jwt = JWT(app, authenticate, identity)


@app.route('/api/v1/signup', methods=['POST'])
def signup():
    full_name = request.json.get('full_name', None)
    email_address = request.json.get('email_address', None)
    password = request.json.get('password', None)

    account_id = bank().open_account(full_name, email_address, password)

    if not account_id:
        return jsonify({"msg": "Account creation failed"}), 400

    return jsonify({"msg": "Account created successfully", "account_id": str(account_id)}), 200


@app.route('/api/v1/login', methods=['POST'])
def login():
    email_address = request.json.get('email_address', None)
    password = request.json.get('password', None)

    try:
        account_id = bank().get_account_id_by_email(email_address)
        account = bank().get_account(account_id)

        if not account or not account.check_password(password):
            return jsonify({"msg": "Bad username or password"}), 401

        # Generate the JWT token
        user = User()
        user.id = str(account.id)
        token = _default_jwt_encode_handler(user)

        # Decode token if it's in bytes format
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        return jsonify({"msg": "Logged in successfully", "access_token": token}), 200

    except AccountNotFoundError:
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": "An error occurred: {}".format(str(e))}), 400


@app.route('/api/v1/deposit', methods=['POST'])
@jwt_required()
def deposit():
    account_id = UUID(request.json.get('account_id', ''))
    amount = request.json.get('amount', None)

    try:
        bank().deposit(account_id, amount)
        return jsonify({"msg": "Amount deposited successfully", "data": amount}), 200
    except ValueError as ve:  # Handle the invalid deposit amount error
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"msg": str(e)}), 400


@app.route('/api/v1/withdraw', methods=['POST'])
@jwt_required()
def withdraw():
    account_id = UUID(request.json.get('account_id', ''))
    amount = request.json.get('amount', None)

    try:
        bank().withdraw(account_id, amount)
        return jsonify({"msg": "Amount withdrawn successfully"}), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 400


@app.route('/api/v1/transfer', methods=['POST'])
@jwt_required()
def transfer():
    source_account_id = UUID(request.json.get('source_account_id', ''))
    target_account_id = UUID(request.json.get('target_account_id', ''))
    amount = request.json.get('amount', None)

    try:
        bank().transfer(source_account_id, target_account_id, amount)
        return jsonify({"msg": "Amount transferred successfully"}), 200
    except AccountNotFoundError:
        return jsonify({"error": "Account not found: {}".format(str(target_account_id))}), 404
    except InsufficientFundsError:  # Handle the insufficient funds error
        return jsonify({"error": "Insufficient funds"}), 400
    except Exception as e:
        return jsonify({"msg": str(e)}), 400


@app.route('/api/v1/account', methods=['GET'])
@jwt_required()
def get_account_details():
    user_id = str(current_identity.id)  # This retrieves the user's identity from the JWT token
    try:
        account = bank().get_account(UUID(user_id))
        return jsonify({
            "balance": str(account.balance),
            "identity": user_id
        }), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 400
