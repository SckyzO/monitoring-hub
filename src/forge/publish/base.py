"""Publisher protocol: the host-agnostic publish contract (spec §5.5).

A ``Publisher`` takes a local staging tree and pushes it to one remote. The
implementation owns all network I/O and the auth it needs; callers stay
host-agnostic so the blob host can change by swapping the adapter.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class Publisher(Protocol):
    def publish(self, staging: Path) -> None: ...
