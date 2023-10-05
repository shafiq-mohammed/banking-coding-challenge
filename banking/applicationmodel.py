# coding=utf-8

from uuid import UUID, uuid5, NAMESPACE_URL

from eventsourcing.application import AggregateNotFound, Application

from banking.domainmodel import Account, BadCredentials, AccountClosedError, AccountNotFoundError


class Bank(Application):

    def get_account_id_by_email(self, email_address: str) -> UUID:
        """Generate a deterministic UUID based on the email."""
        return uuid5(NAMESPACE_URL, email_address)

    def open_account(self, full_name: str, email_address: str, password: str) -> UUID:
        account_id = self.get_account_id_by_email(email_address)
        # Hash the password before using it with the aggregate
        hashed_password = Account.hash_password(password)
        try:
            existing_account = self.repository.get(account_id)
            if existing_account:
                raise ValueError(f"Account with email {email_address} already exists.")
        except AggregateNotFound:
            pass

        account = Account(account_id, full_name=full_name, email_address=email_address, password=hashed_password)
        print(account.password)
        self.save(account)
        return account.id

    def deposit(self, credit_account_id: UUID, amount_in_cents: int) -> None:
        if amount_in_cents <= 0:
            raise ValueError("Invalid deposit amount")
        account = self.get_account(credit_account_id)
        if account.closed:
            raise AccountClosedError
        account.credit(amount_in_cents)
        self.save(account)

    def withdraw(self, debit_account_id: UUID, amount_in_cents: int) -> None:
        if amount_in_cents <= 0:
            raise ValueError("Invalid withdraw amount")
        account = self.get_account(debit_account_id)
        if account.closed:
            raise AccountClosedError
        account.debit(amount_in_cents)
        self.save(account)

    def transfer(self, debit_account_id: UUID, credit_account_id: UUID, amount_in_cents: int) -> None:
        source_account = self.get_account(debit_account_id)
        target_account = self.get_account(credit_account_id)
        if source_account.closed or target_account.closed:
            raise AccountClosedError
        source_account.debit(amount_in_cents)
        target_account.credit(amount_in_cents)
        self.save(source_account, target_account)

    def close_account(self, account_id: UUID) -> None:
        account = self.get_account(account_id)
        account.close()
        self.save(account)

    def get_balance(self, account_id: UUID) -> int:
        account = self.get_account(account_id)
        return account.balance

    def validate_password(self, account_id: UUID, password: str) -> None:
        account = self.get_account(account_id)
        if not account.check_password(password):
            raise BadCredentials

    def change_password(self, account_id: UUID, old_password: str, new_password: str) -> None:
        account = self.get_account(account_id)
        account.change_password(old_password, new_password)
        self.save(account)

    def set_overdraft_limit(self, account_id: UUID, amount_in_cents: int) -> None:
        if amount_in_cents < 0:
            raise AssertionError("Overdraft limit cannot be negative.")
        account = self.get_account(account_id)
        if account.closed:
            raise AccountClosedError
        account.set_overdraft_limit(amount_in_cents)
        self.save(account)

    def get_overdraft_limit(self, account_id: UUID) -> int:
        account = self.get_account(account_id)
        return account.overdraft_limit

    def get_account(self, account_id: UUID) -> Account:
        try:
            return self.repository.get(account_id)
        except AggregateNotFound:
            raise AccountNotFoundError(f"No account found with ID: {account_id}")
