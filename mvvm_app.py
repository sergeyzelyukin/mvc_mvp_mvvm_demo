from __future__ import annotations
from typing import Callable, Optional
from dataclasses import dataclass
from domain import Bank, Treasury, Exchange
from datatypes import TransferPort, Account


# ===== View =====
class ConsoleTransferView:
    def __init__(self, vm: TransferViewModel) -> None:
        self.vm = vm

        self.vm.bind_on_progress(self.show_transfer_progress)
        self.vm.bind_on_error(self.show_transfer_error)
        self.vm.bind_on_result(self.show_transfer_result)
        self.vm.bind_confirm_callback(self.ask_exchange_confirmation)

    def run_once(self) -> None:
        self.vm.from_id = input("From account: ").strip()
        self.vm.to_id = input("To account: ").strip()
        self.vm.amount_text = input("Amount: ").strip()

        self.vm.run_transfer()

    def show_transfer_progress(self, step: int, total_steps: int) -> None:
        print(f"Progress: [{step}/{total_steps}]")

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

    def show_transfer_result(self, message: str) -> None:
        print(f"DONE: {message}")

    def show_transfer_error(self, message: str) -> None:
        print(f"ERROR: {message}")


# ===== ViewModel =====
class TransferViewModel(TransferPort):
    def __init__(self, bank: Bank) -> None:
        self.bank = bank

        # "Input" states
        self.from_id: str = ""
        self.to_id: str = ""
        self.amount_text: str = ""
        # "Output" states
        self.progress_events: list[tuple[int, int]] = []
        self.last_error: Optional[str] = None
        self.last_result: Optional[str] = None

        # Hooks
        self._confirm_callback: Optional[Callable[[dict], bool]] = None
        self.on_progress: Optional[Callable[[int, int], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_result: Optional[Callable[[str], None]] = None

    def bind_confirm_callback(
        self,
        callback: Callable[[dict], bool],
    ) -> None:
        self._confirm_callback = callback

    def bind_on_progress(self, callback: Callable[[int, int], None]) -> None:
        self.on_progress = callback

    def bind_on_error(self, callback: Callable[[str], None]) -> None:
        self.on_error = callback

    def bind_on_result(self, callback: Callable[[str], None]) -> None:
        self.on_result = callback

    def run_transfer(self) -> None:
        # reset "output" state for this run,
        # "input" state should already be set by View by this moment
        self.progress_events.clear()
        self.last_error = None
        self.last_result = None

        try:
            amount_value = float(self.amount_text)
        except ValueError:
            self._emit_error("Amount must be a number")
            return

        try:
            self.bank.transfer(
                self.from_id,
                self.to_id,
                amount_value,
                self,  # pass self as TransferPort
            )
        except Exception as ex:
            self._emit_error(str(ex))

    # -------- internal helpers --------
    def _emit_error(self, message: str) -> None:
        self.last_error = message
        if self.on_error:
            self.on_error(message)

    # -------- TransferPort implementation (domain -> ViewModel) --------
    def report_transfer_progress(self, step: int, total_steps: int) -> None:
        self.progress_events.append((step, total_steps))
        if self.on_progress:
            self.on_progress(step, total_steps)

    def report_transfer_completion(self) -> None:
        self.last_result = "Transfer completed"
        if self.on_result:
            self.on_result(self.last_result)

    def confirm_currency_conversion(
        self,
        from_currency: str,
        to_currency: str,
        rate: float,
        amount_src: float,
        amount_dst: float,
    ) -> bool:
        return self._confirm_callback(
            from_currency, to_currency, rate, amount_src, amount_dst
        )

    def discard_transfer(self, reason: str) -> None:
        self._emit_error(reason)


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
    view_model = TransferViewModel(bank)
    view = ConsoleTransferView(view_model)

    view.run_once()


if __name__ == "__main__":
    main()
