# coding=utf-8

import typing
from uuid import UUID

import pytest

from banking.applicationmodel import Bank, AccountNotFoundError
from banking.domainmodel import (
    AccountClosedError,
    InsufficientFundsError,
    BadCredentials,
)


def assertEqual(x: typing.Any, y: typing.Any) -> None:
    assert x == y


def _create_alice_with_200(app: Bank) -> UUID:
    # Create alice.
    alice = app.open_account(
        full_name="Alice",
        email_address="alice@example.com",
        password="alice",
    )

    # Check balance of alice.
    assertEqual(app.get_balance(alice), 0)

    # Deposit funds in alice.
    app.deposit(
        credit_account_id=alice,
        amount_in_cents=10000,
    )

    # Deposit funds in alice.
    app.deposit(
        credit_account_id=alice,
        amount_in_cents=10000,
    )

    return alice


def _create_bob(app: Bank) -> UUID:
    # Create bob.
    bob = app.open_account(
        full_name="Bob",
        email_address="bob@example.com",
        password="bob",
    )

    # Check balance of alice.
    assertEqual(app.get_balance(bob), 0)

    # Deposit funds in bob.
    app.deposit(
        credit_account_id=bob,
        amount_in_cents=100,
    )

    # Deposit funds in bob.
    app.deposit(
        credit_account_id=bob,
        amount_in_cents=100,
    )

    return bob


def _create_sue(app: Bank) -> UUID:
    # Create sue.
    sue = app.open_account(
        full_name="Sue",
        email_address="sue@example.com",
        password="sue",
    )

    # Check balance of sue.
    assertEqual(app.get_balance(sue), 0)

    # Deposit funds in sue.
    app.deposit(
        credit_account_id=sue,
        amount_in_cents=100,
    )

    return sue


def test_account_does_not_exist() -> None:
    app = Bank()
    alice = app.get_account_id_by_email("alice@example.com")
    # Check account not found error.
    with pytest.raises(AccountNotFoundError):
        app.get_balance(alice)


def test_deposit() -> None:
    app = Bank()

    alice = _create_alice_with_200(app)
    bob = _create_bob(app)

    # Check balance of alice.
    assertEqual(app.get_balance(alice), 20000)

    # Check balance of alice.
    assertEqual(app.get_balance(bob), 200)


def test_withdraw() -> None:
    app = Bank()

    alice = _create_alice_with_200(app)

    # Withdraw funds from alice.
    app.withdraw(
        debit_account_id=alice,
        amount_in_cents=5000,
    )

    # Check balance of alice.
    assertEqual(app.get_balance(alice), 15000)


def test_invalid_withdraw_amount() -> None:
    app = Bank()

    alice = _create_alice_with_200(app)

    with pytest.raises(ValueError) as exception_info:
        app.withdraw(
            debit_account_id=alice,
            amount_in_cents=-1
        )

    assert str(exception_info.value) == "Invalid withdraw amount"


def test_insufficient() -> None:
    app = Bank()

    alice = _create_alice_with_200(app)

    # Fail to withdraw funds from alice- insufficient funds.
    with pytest.raises(InsufficientFundsError):
        app.withdraw(
            debit_account_id=alice,
            amount_in_cents=25000,
        )

    # Check balance of alice - should be unchanged.
    assertEqual(app.get_balance(alice), 20000)


def test_transfer() -> None:
    app = Bank()

    alice = _create_alice_with_200(app)
    bob = _create_bob(app)
    sue = _create_sue(app)

    # Transfer funds from alice to bob.
    app.transfer(
        debit_account_id=alice,
        credit_account_id=bob,
        amount_in_cents=5000,
    )

    # Transfer funds from bob to sue.
    app.transfer(
        debit_account_id=bob,
        credit_account_id=sue,
        amount_in_cents=100,
    )

    # Check balances.
    assertEqual(app.get_balance(alice), 15000)
    assertEqual(app.get_balance(bob), 5100)
    assertEqual(app.get_balance(sue), 200)

    # Fail to transfer funds - insufficient funds.
    with pytest.raises(InsufficientFundsError):
        app.transfer(
            debit_account_id=alice,
            credit_account_id=bob,
            amount_in_cents=100000,
        )

    # Check balances - should be unchanged.
    assertEqual(app.get_balance(alice), 15000)
    assertEqual(app.get_balance(bob), 5100)
    assertEqual(app.get_balance(sue), 200)


def test_closed() -> None:
    app = Bank()

    alice = _create_alice_with_200(app)
    bob = _create_bob(app)

    # Close alice .
    app.close_account(alice)

    # Fail to transfer funds - alice  is closed.
    with pytest.raises(AccountClosedError):
        app.transfer(
            debit_account_id=alice,
            credit_account_id=bob,
            amount_in_cents=5000,
        )

    # Fail to withdraw funds - alice is closed.
    with pytest.raises(AccountClosedError):
        app.withdraw(
            debit_account_id=alice,
            amount_in_cents=100,
        )

    # Fail to deposit funds - alice is closed.
    with pytest.raises(AccountClosedError):
        app.deposit(
            credit_account_id=alice,
            amount_in_cents=100000,
        )

    # Fail to set overdraft limit on alice - account is closed.
    with pytest.raises(AccountClosedError):
        app.set_overdraft_limit(
            account_id=alice,
            amount_in_cents=50000,
        )

    # Check balances - should be unchanged.
    assertEqual(app.get_balance(alice), 20000)
    assertEqual(app.get_balance(bob), 200)

    # Check overdraft limits - should be unchanged.
    assertEqual(
        app.get_overdraft_limit(alice),
        0,
    )
    assertEqual(
        app.get_overdraft_limit(bob),
        0,
    )


def test_debit() -> None:
    app = Bank()
    alice = _create_alice_with_200(app)
    account = app.get_account(alice)
    with pytest.raises(ValueError):
        account.debit(-1)


def test_overdraft() -> None:
    app = Bank()

    alice = _create_alice_with_200(app)
    bob = _create_bob(app)

    # Check overdraft limit of alice.
    assertEqual(
        app.get_overdraft_limit(alice),
        0,
    )

    # Set overdraft limit on bob.
    app.set_overdraft_limit(
        account_id=bob,
        amount_in_cents=50000,
    )

    # Can't set negative overdraft limit.
    with pytest.raises(AssertionError):
        app.set_overdraft_limit(
            account_id=bob,
            amount_in_cents=-50000,
        )

    # Check overdraft limit of bob.
    assertEqual(
        app.get_overdraft_limit(bob),
        50000,
    )

    # Withdraw funds from bob.
    app.withdraw(
        debit_account_id=bob,
        amount_in_cents=50200,
    )

    # Check balance of bob - should be overdrawn.
    assertEqual(
        app.get_balance(bob),
        -50000,
    )

    # Fail to withdraw funds from bob - insufficient funds.
    with pytest.raises(InsufficientFundsError):
        app.withdraw(
            debit_account_id=bob,
            amount_in_cents=100,
        )


def test_password() -> None:
    app = Bank()

    alice = _create_alice_with_200(app)

    app.validate_password(alice, "alice")
    app.change_password(alice, "alice", "alice2")
    app.validate_password(alice, "alice2")
    with pytest.raises(BadCredentials):
        app.validate_password(alice, "alice")


def test_credit_closed_account() -> None:
    app = Bank()

    # Assuming this function creates Alice with 20000 cents.
    alice = _create_alice_with_200(app)

    # Close Alice's account.
    alice_account = app.get_account(alice)
    alice_account.close()

    # Attempt to credit a closed account.
    # This should raise an AccountClosedError.

    with pytest.raises(AccountClosedError) as exception_info:
        alice_account.credit(amount_in_cents=5000)

    assert str(exception_info.value) == "Account is closed."

    # Check balance of Alice.
    # It should still be 20000 cents as no credit was made.
    assertEqual(app.get_balance(alice), 20000)


def test_debit_closed_account() -> None:
    app = Bank()

    # Assuming this function creates Alice with 20000 cents.
    alice = _create_alice_with_200(app)

    # Close Alice's account.
    alice_account = app.get_account(alice)
    alice_account.close()

    # Attempt to debit from a closed account.
    # This should raise an AccountClosedError.
    with pytest.raises(AccountClosedError) as exception_info:
        alice_account.debit(amount_in_cents=5000)

    assert str(exception_info.value) == "Account is closed."

    # Check balance of Alice.
    # It should still be 20000 cents as no debit was made.
    assertEqual(app.get_balance(alice), 20000)


def test_close_already_closed_account() -> None:
    app = Bank()

    # Assuming this function creates Alice with 20000 cents.
    alice = _create_alice_with_200(app)

    # Close Alice's account.
    alice_account = app.get_account(alice)
    alice_account.close()

    # Attempt to close an already closed account.\
    # This should raise an AccountClosedError.
    with pytest.raises(AccountClosedError) as exception_info:
        alice_account.close()

    assert str(exception_info.value) == "Account is already closed."
