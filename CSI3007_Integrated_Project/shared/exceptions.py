"""Shared exception types for the integration layer.

The person applications each define their own ``errors.AppError``; this module
adds the small set of errors the gateway and launcher need.
"""

from __future__ import annotations


class IntegrationError(Exception):
    """Base class for integration-layer failures."""


class ServiceUnavailableError(IntegrationError):
    """A person application did not answer its health check in time."""

    def __init__(self, service_key: str, base_url: str):
        self.service_key = service_key
        self.base_url = base_url
        super().__init__(f"Service '{service_key}' is unavailable at {base_url}")


class ServiceRegistryError(IntegrationError):
    """An unknown service key was requested from the registry."""


class StartupError(IntegrationError):
    """The launcher failed to start one or more services."""

    def __init__(self, message: str, failed_services: dict[str, str] | None = None):
        self.failed_services = failed_services or {}
        super().__init__(message)
