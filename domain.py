from typing import Dict, Tuple
from datatypes import TransferPort, Account


class Treasury:
    """Holds accounts and moves money. No I/O here."""

    def __init__(self) -> None:
        self._accounts: Dict[str, Account] = {}

    def add_account(self, account: Account) -> None:
        self._accounts[account.id] = account

    def get_account(self, account_id: str) -> Account:
        if account_id not in self._accounts:
            raise IndexError(f"account {account_id} does not exist")
        return self._accounts[account_id]

    def subtract_amount(self, account_id: str, amount: float) -> None:
        acc = self.get_account(account_id)
        acc.balance -= amount

    def add_amount(self, account_id: str, amount: float) -> None:
        acc = self.get_account(account_id)
        acc.balance += amount


class Exchange:
    """Very simple conversion."""

    def __init__(self):
        self._currency_table: Dict[Tuple[str, str], float] = {}

    def add_rate(self, from_ccy: str, to_ccy: str, rate: float):
        self._currency_table[(from_ccy, to_ccy)] = rate

    def get_rate(self, from_ccy: str, to_ccy: str) -> float:
        if from_ccy == to_ccy:
            return 1.0
        return self._currency_table[(from_ccy, to_ccy)]


class Bank:
    """
    Orchestrates a transfer. Calls TransferPort for progress + confirmation.
    No prints, no input(), no tkinter — strictly UI-agnostic.
    """

    def __init__(self, treasury: Treasury, exchange: Exchange) -> None:
        self.treasury = treasury
        self.exchange = exchange

    def transfer(
        self, from_id: str, to_id: str, amount_src: float, port: TransferPort
    ) -> None:
        number_of_steps = 4  # check, convert, subtract, add

        # Step 1: checking accounts & currencies
        port.report_transfer_progress(1, number_of_steps)
        account_src = self.treasury.get_account(from_id)
        account_dst = self.treasury.get_account(to_id)
        if account_src.balance < amount_src:
            port.discard_transfer("Insufficient funds")
            return

        # Step 2: if different currencies, ask confirmation
        port.report_transfer_progress(2, number_of_steps)
        if account_src.currency == account_dst.currency:
            amount_dst = amount_src
        else:
            try:
                rate = self.exchange.get_rate(
                    account_src.currency, account_dst.currency
                )
            except KeyError:
                port.discard_transfer(
                    f"No conversion rate {account_src.currency}->{account_dst.currency}"
                )
                return

            amount_dst = amount_src * rate

            confirmation = port.confirm_currency_conversion(
                account_src.currency, account_dst.currency, rate, amount_src, amount_dst
            )
            if not confirmation:
                port.discard_transfer("Currency conversion not approved")
                return

        # Step 3: subtract funds
        port.report_transfer_progress(3, number_of_steps)
        self.treasury.subtract_amount(account_src.id, amount_src)

        # Step 4: add funds
        port.report_transfer_progress(4, number_of_steps)
        self.treasury.add_amount(account_dst.id, amount_dst)
        port.report_transfer_completion()
