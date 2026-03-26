"""LangChain tool: historical hack records from DefiLlama."""

from __future__ import annotations

import logging

from langchain_core.tools import tool

from app.services.http_client import get_http_client
from app.services.registry import get_registry

logger = logging.getLogger(__name__)

_HACKS_URLS = [
    "https://api.llama.fi/hacks",
    "https://defillama-datasets.llama.fi/cryptoHacks.json"
]


@tool
async def get_historical_hacks(protocol_or_token: str) -> str:
    """
    Queries DefiLlama hacks database for all recorded exploits for a given
    protocol or token name. Uses a static CDN dataset (no rate limits).
    Results are cached for 10 minutes. FREE, no key needed.
    """
    cache = get_registry().hacks_cache
    cached = cache.get()
    if cached is not None:
        hacks = cached
        logger.debug(f"Using cached hacks data (age: {cache.age:.0f}s)")
    else:
        client = get_http_client()
        hacks = "ERROR"

        for url in _HACKS_URLS:
            try:
                resp = await client.get(url, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    parsed = (
                        data.get("hacks", data.get("data", data))
                        if isinstance(data, dict)
                        else data
                    )
                    if parsed:
                        hacks = parsed
                        break
            except Exception as e:
                logger.warning(f"DefiLlama hacks source failed: {url} - {e}")

        if hacks == "ERROR":
            logger.warning("All hacks sources failed, caching error state.")
        else:
            logger.info(f"Refreshed hacks cache with {len(hacks)} records")

        cache.set(hacks)

    if hacks == "ERROR" or not hacks:
        return "DefiLlama hacks DB temporarily unavailable. Try again in a few minutes."

    keyword = protocol_or_token.lower()
    matches = [
        h for h in hacks
        if keyword in str(h.get("name", "")).lower()
        or keyword in str(h.get("protocol", "")).lower()
        or keyword in str(h.get("token", "")).lower()
    ]
    if not matches:
        return f"No recorded hacks found for '{protocol_or_token}'."

    lines = [f"DefiLlama hack records for '{protocol_or_token}':"]
    for h in matches:
        date = h.get("date", h.get("timestamp", "unknown date"))
        lost = h.get("fundsLost", h.get("amount", 0))
        returned = h.get("fundsReturned", 0)
        attack = h.get("classification", h.get("type", "unknown attack type"))
        name = h.get("name", h.get("protocol", protocol_or_token))
        net_loss = (lost or 0) - (returned or 0)
        returned_str = f", ${returned/1e6:.1f}M returned" if returned else ", no funds returned"
        source_url = h.get("url", h.get("link", h.get("sourceUrl", "")))
        url_str = f" | url: {source_url}" if source_url else ""
        lines.append(
            f"  * [{date}] {name} - ${(lost or 0)/1e6:.1f}M lost{returned_str}"
            f" | Attack: {attack} | Net loss: ${net_loss/1e6:.1f}M{url_str}"
        )
    return "\n".join(lines)
