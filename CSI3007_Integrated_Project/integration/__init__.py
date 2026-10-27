"""Integration layer for the CSI3007 integrated project.

Modules:
    service_registry  — single source of truth for the runnable services.
    health_checks     — real (never fabricated) availability probes.
    api_gateway       — FastAPI landing page + status endpoints on port 8000.

The gateway coordinates presentation and monitoring only. Business data always
flows directly between the person applications over their documented,
authenticated REST APIs.
"""
