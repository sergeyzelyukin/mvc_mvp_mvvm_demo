# mvc_app.py
from __future__ import annotations
from domain import Bank, Treasury, Exchange
from datatypes import TransferPort, Account


# ----- View (console) -----
class ConsoleTransferView:
    def get_transfer_inputs(self) -> tuple[str, str, str]:
        from_id = input("From account: ").strip()
        to_id = input("To account: ").strip()
        amount_text = input("Amount: ").strip()
        return from_id, to_id, amount_text

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


# ----- Controller (implements TransferPort, pulls inputs) -----
class TransferController(TransferPort):
    def __init__(self, bank: Bank, view: ConsoleTransferView) -> None:
        self.bank = bank  # Model
        self.view = view  # View

    # TransferPort methods (domain calls these)
    def report_transfer_progress(self, step: int, total_steps: int) -> None:
        self.view.show_transfer_progress(
            step, total_steps
        )  # ask View to visualize progress

    def report_transfer_completion(self):
        self.view.show_transfer_result("Transfer completed")  # ask View to show result

    def confirm_currency_conversion(
        self,
        from_currency: str,
        to_currency: str,
        rate: float,
        amount_src: float,
        amount_dst: float,
    ) -> bool:  # ask View to get confirmation
        return self.view.ask_exchange_confirmation(
            from_currency, to_currency, rate, amount_src, amount_dst
        )

    def discard_transfer(self, reason):
        self.view.show_transfer_error(reason)  # ask View to show error

    # Entry point
    def run(self) -> None:
        # Controller pulls input by itself
        from_id, to_id, amount_text = self.view.get_transfer_inputs()

        # Controller does input validation
        try:
            amount = float(amount_text)
        except ValueError:
            self.view.show_transfer_error(
                "Amount must be a number"
            )  # ask View to show error
            return

        # Controller calls Model to run the operation
        try:
            self.bank.transfer(
                from_id, to_id, amount, self
            )  # ask Model to do funds transfer
        except Exception as ex:
            self.view.show_transfer_error(str(ex))  # ask View to treat exception


def main() -> None:
    treasury = Treasury()
    treasury.add_account(Account("alice", "USD", 1000.0))
    treasury.add_account(Account("bob", "EUR", 100.0))

    exchange = Exchange()
    exchange.add_rate("USD", "EUR", 0.9)
    exchange.add_rate("EUR", "USD", 1.1)
    exchange.add_rate("USD", "AUD", 1.5)
    exchange.add_rate("AUD", "USD", 0.67)

    bank = Bank(treasury, exchange)  # Model
    view = ConsoleTransferView()  # View
    controller = TransferController(bank, view)  # Controller

    controller.run()


if __name__ == "__main__":
    main()
