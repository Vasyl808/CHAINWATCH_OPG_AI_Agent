"""
Service registry: single container for all shared state.

Initialized once during app startup via lifespan, accessed via FastAPI
dependency injection. No module-level mutable globals anywhere.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from app.services.cache import TTLCache

if TYPE_CHECKING:
    from app.services.agent.pool import AgentPool


class ServiceRegistry:
    """Holds all shared resources: HTTP client, caches, agent pool."""

    def __init__(self, private_key: str = "", max_concurrent: int = 5):
        self.http_client = httpx.AsyncClient(
            timeout=12.0,
            follow_redirects=True,
            limits=httpx.Limits(
                max_connections=8,
                max_keepalive_connections=4,
            ),
        )
        self.hacks_cache = TTLCache(ttl_seconds=600.0)
        self.solana_token_cache = TTLCache(ttl_seconds=3600.0 * 24)

        from app.services.agent.pool import AgentPool
        self.agent_pool = AgentPool(
            private_key=private_key,
            max_concurrent=max_concurrent,
        )

    async def shutdown(self):
        await self.http_client.aclose()


_registry: ServiceRegistry | None = None


def init_registry(private_key: str = "", max_concurrent: int = 5) -> ServiceRegistry:
    """Create and store the registry. Called once from lifespan."""
    global _registry
    _registry = ServiceRegistry(
        private_key=private_key,
        max_concurrent=max_concurrent,
    )
    return _registry


def get_registry() -> ServiceRegistry:
    if _registry is None:
        raise RuntimeError("ServiceRegistry not initialized. App lifespan not started.")
    return _registry