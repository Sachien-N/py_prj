"""Modular smart-socket adapter interface.

Manual and simulated adapters are implemented. Vendor/MQTT integrations can add a
new adapter without changing the reading aggregation or tariff code.
"""

from services.adapters.base import (
    AdapterUnavailable,
    FutureVendorAdapter,
    ManualAdapter,
    ReadingSample,
    SimulatedAdapter,
    SmartSocketAdapter,
)

__all__ = [
    "AdapterUnavailable",
    "FutureVendorAdapter",
    "ManualAdapter",
    "ReadingSample",
    "SimulatedAdapter",
    "SmartSocketAdapter",
]
