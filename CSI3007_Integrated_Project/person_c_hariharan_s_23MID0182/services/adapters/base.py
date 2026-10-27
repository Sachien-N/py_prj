"""Adapter contracts for readings from smart sockets or future vendor APIs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Protocol

from models import Socket


@dataclass(frozen=True)
class ReadingSample:
    reading_at: datetime
    power_w: Decimal
    cumulative_energy_kwh: Decimal | None = None
    is_simulated: bool = False
    source: str = "adapter"


class AdapterUnavailable(RuntimeError):
    pass


class SmartSocketAdapter(Protocol):
    name: str

    def fetch_readings(self, socket: Socket, *, since: datetime | None = None) -> list[ReadingSample]:
        ...


class ManualAdapter:
    """Manual/simulated entry is performed by the API's reading endpoint."""

    name = "manual"

    def fetch_readings(self, socket: Socket, *, since: datetime | None = None) -> list[ReadingSample]:
        return []


class SimulatedAdapter:
    name = "simulated"

    def fetch_readings(self, socket: Socket, *, since: datetime | None = None) -> list[ReadingSample]:
        now = datetime.now(timezone.utc)
        return [
            ReadingSample(
                reading_at=now,
                power_w=Decimal("0"),
                is_simulated=True,
                source="simulated",
            )
        ]


class FutureVendorAdapter:
    """Placeholder adapter that makes the missing hardware integration explicit."""

    name = "future_vendor"

    def fetch_readings(self, socket: Socket, *, since: datetime | None = None) -> list[ReadingSample]:
        raise AdapterUnavailable(
            "No vendor smart-plug or MQTT integration is configured. Use manual or "
            "simulated readings, or implement this adapter for the device's API."
        )
