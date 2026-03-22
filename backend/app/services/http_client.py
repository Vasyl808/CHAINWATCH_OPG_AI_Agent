"""Shared async HTTP client — accessed via ServiceRegistry."""

from __future__ import annotations

import httpx

from app.services.registry import get_registry


def get_http_client() -> httpx.AsyncClient:
    """Return the shared httpx.AsyncClient from the service registry."""
    return get_registry().http_client
