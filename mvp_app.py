# mvp_app.py
from __future__ import annotations
from typing import Optional, Callable
from domain import Bank, Treasury, Exchange
from datatypes import TransferPort, Account


# ===== View (Passive View) =====
class ConsoleTransferView:
    """
    Passive View:
      - owns I/O
      - pushes raw inputs to the Presenter via a bound handler
      - exposes only render methods the Presenter calls
      - contains no business logic or parsing
    """

    def __init__(self) -> None:
        self._on_submit: Optional[Callable[[str, str, str], None]] = None

    def bind_submit(self, handler: Callable[[str, str, str], None]) -> None:
        self._on_submit = handler

    # "Run once" to simulate a submit; View PUSHES inputs to presenter
    def run_once(self) -> None:
        from_id = input("From account: ").strip()
        to_id = input("To account: ").strip()
        amount_text = input("Amount: ").strip()
        assert self._on_submit is not None, "Presenter must bind_submit() first"

        self._on_submit(from_id, to_id, amount_text)

    # Render-only API the Presenter uses
    def show_transfer_progress(self, step: int, total: int) -> None:
        print(f"Progress: [{step}/{total}]")

    def ask_exchange_confirmation(
        self,
        from_ccy: str,
        to_ccy: str,
        rate: float,
        amount_src: float,
        amount_dst: float,
    ) -> bool:
        print(
            f"Convert {amount_src:.2f} {from_ccy} -> {amount_dst:.2f} {to_ccy} at {rate:.4f}"
        )
        ans = input("Proceed? [y/N]: ").strip().lower()
        return ans == "y"

    def show_transfer_result(self, text: str) -> None:
        print(f"DONE: {text}")

    def show_transfer_error(self, text: str) -> None:
        print(f"ERROR: {text}")


# ===== Presenter (implements TransferPort; owns presentation logic) =====
class TransferPresenter(TransferPort):
    """
    Presenter:
      - receives raw inputs from the View
      - parses/validates
      - calls the domain model
      - implements TransferPort and delegates UI work to the View
    """

    def __init__(self, bank: Bank, view: ConsoleTransferView) -> None:
        self.bank = bank
        self.view = view
        self.view.bind_submit(self.on_submit)

    # View event: raw inputs pushed into the Presenter
    def on_submit(self, from_id: str, to_id: str, amount_text: str) -> None:
        try:
            amount = float(amount_text)
        except ValueError:
            self.view.show_transfer_error("Amount must be a number")
            return

        try:
            self.bank.transfer(from_id, to_id, amount, self)
        except Exception as ex:
            self.view.show_transfer_error(str(ex))
            return

    # ---- TransferPort (domain -> presenter -> view) ----
    def report_transfer_progress(self, step: int, total_steps: int) -> None:
        self.view.show_transfer_progress(step, total_steps)

    def report_transfer_completion(self) -> None:
        self.view.show_transfer_result("Transfer completed")

    def confirm_currency_conversion(
        self,
        from_currency: str,
        to_currency: str,
        rate: float,
        amount_src: float,
        amount_dst: float,
    ) -> bool:
        return self.view.ask_exchange_confirmation(
            from_currency, to_currency, rate, amount_src, amount_dst
        )

    def discard_transfer(self, reason: str) -> None:
        self.view.show_transfer_error(reason)


def main() -> None:
    treasury = Treasury()
    treasury.add_account(Account("alice", "USD", 1000.0))
    treasury.add_account(Account("bob", "EUR", 100.0))

    exchange = Exchange()
    exchange.add_rate("USD", "EUR", 0.9)
    exchange.add_rate("EUR", "USD", 1.1)
    exchange.add_rate("USD", "AUD", 1.5)
    exchange.add_rate("AUD", "USD", 0.67)

    bank = Bank(treasury, exchange)
    view = ConsoleTransferView()
    TransferPresenter(bank, view)  # wires itself via bind_submit

    view.run_once()  # View PUSHES inputs to Presenter


if __name__ == "__main__":
    main()
