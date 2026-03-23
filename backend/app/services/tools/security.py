"""LangChain tool: historical hack records from DefiLlama."""

from __future__ import annotations

import logging

from langchain_core.tools import tool

from app.services.http_client import get_http_client
from app.services.registry import get_registry

logger = logging.getLogger(__name__)

_HACKS_URLS = [
    "https://api.llama.fi/hacks",
    "https://defillama-datasets.llama.fi/cryptoHacks.json",
]


@tool
async def get_historical_hacks(protocol: str) -> str:
    """
    Queries DefiLlama hacks database for all recorded exploits for a given
    protocol name. Results are cached for 10 minutes.
    FREE, no key needed.
    """
    cache  = get_registry().hacks_cache
    cached = cache.get()

    if cached is not None:
        hacks = cached
    else:
        client = get_http_client()
        hacks  = "ERROR"

        for url in _HACKS_URLS:
            try:
                resp = await client.get(url, timeout=20)
                if resp.status_code == 200:
                    data   = resp.json()
                    parsed = (
                        data.get("hacks", data.get("data", data))
                        if isinstance(data, dict)
                        else data
                    )
                    if parsed:
                        hacks = parsed
                        break
            except Exception as e:
                logger.warning("DefiLlama hacks source failed: %s — %s", url, e)

        if hacks == "ERROR":
            logger.warning("All hacks sources failed.")
        else:
            logger.info("Refreshed hacks cache: %d records", len(hacks))

        cache.set(hacks)

    if hacks == "ERROR" or not hacks:
        return "DefiLlama hacks DB temporarily unavailable."

    keyword = protocol.lower()
    matches = [
        h for h in hacks
        if keyword in str(h.get("name",     "")).lower()
        or keyword in str(h.get("protocol", "")).lower()
    ]
    if not matches:
        return f"No recorded hacks for '{protocol}'."

    lines = [f"DefiLlama hacks for '{protocol}':"]
    for h in matches:
        date      = h.get("date", h.get("timestamp", "?"))
        lost      = h.get("fundsLost",     h.get("amount", 0)) or 0
        returned  = h.get("fundsReturned", 0) or 0
        attack    = h.get("classification", h.get("type", "unknown"))
        name      = h.get("name", h.get("protocol", protocol))
        net_loss  = lost - returned
        ret_str   = f", ${returned/1e6:.1f}M returned" if returned else ", none returned"
        lines.append(
            f"  * [{date}] {name} — ${lost/1e6:.1f}M lost{ret_str}"
            f" | {attack} | Net: ${net_loss/1e6:.1f}M"
        )
    return "\n".join(lines)