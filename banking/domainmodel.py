# coding=utf-8

from hashlib import sha512
from uuid import UUID

from eventsourcing.domain import Aggregate, event


class Account(Aggregate):
    """
    This is the model of the aggregate, it has
    many events that happen, and when you load
    a model using the application object (Bank)
    you get all events saved for the id of the
    individual model. This never saves itself,
    all saving happens in the Bank application.
    """

    _id: UUID

    @event("Opened")
    def __init__(
            self,
            id: UUID,
            full_name: str,
            email_address: str,
            password: str,
    ):
        self._id = id
        self.full_name = full_name
        self.email_address = email_address
        self.password = password
        self.balance = 0  # In cents
        self.closed = False
        self.overdraft_limit = 0

    @event("Credited")
    def credit(self, amount_in_cents: int) -> None:
        """Add money to the account."""
        if self.closed:
            raise AccountClosedError("Account is closed.")
        self.balance += amount_in_cents

    @event("Debited")
    def debit(self, amount_in_cents: int) -> None:
        """Withdraw money from the account. Raise an error if insufficient funds."""
        if amount_in_cents <= 0:
            raise ValueError("Invalid debit amount. Amount should be positive.")
        if self.closed:
            raise AccountClosedError("Account is closed.")
        effective_balance = self.balance + self.overdraft_limit
        if amount_in_cents > effective_balance:
            raise InsufficientFundsError('Insufficient funds')
        self.balance -= amount_in_cents

    @event("Closed")
    def close(self) -> None:
        """Mark account as closed."""
        if self.closed:
            raise AccountClosedError("Account is already closed.")
        self.closed = True

    @event("PasswordChanged")
    def change_password(self, old_password: str, new_password: str) -> None:
        """Change the password of the account."""
        if not self.check_password(old_password):
            raise BadCredentials
        self.password = self.hash_password(new_password)

    @event("OverdraftSet")
    def set_overdraft_limit(self, amount_in_cents: int) -> None:
        """Set an overdraft limit."""
        self.overdraft_limit = amount_in_cents

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash the password before saving it."""
        return sha512(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored one."""
        return self.hash_password(password) == self.password


class TransactionError(Exception):
    pass


class AccountClosedError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


class BadCredentials(Exception):
    pass


class InvalidPasswordError(Exception):
    pass


class AccountNotFoundError(Exception):
    pass
