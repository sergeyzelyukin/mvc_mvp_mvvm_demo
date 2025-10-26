from typing import Protocol
from dataclasses import dataclass


@dataclass
class Account:
    id: str
    currency: str
    balance: float


class TransferPort(Protocol):
    """UI/presentation boundary the domain calls (no UI code here)."""

    def report_transfer_progress(self, step: int, total_steps: int) -> None: ...

    def report_transfer_completion(self) -> None: ...

    def confirm_currency_conversion(
        self,
        from_currency: str,
        to_currency: str,
        rate: float,
        amount_src: float,
        amount_dst: float,
    ) -> bool: ...

    def discard_transfer(self, reason: str) -> None: ...
