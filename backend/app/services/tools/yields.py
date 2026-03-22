"""LangChain tool: DeFi yield pool discovery via DefiLlama."""

from __future__ import annotations

import logging

from langchain_core.tools import tool

from app.core.config import settings
from app.services.http_client import get_http_client
from app.services.portfolio.constants import NETWORK_ALIASES
from app.services.registry import get_registry

logger = logging.getLogger(__name__)


@tool
async def get_defi_yields(asset: str, network: str = "") -> str:
    """
    Fetches the top 5 highest-APY DeFi yield pools from DefiLlama for a given
    asset symbol. Optionally filter by network (e.g., 'Ethereum', 'Arbitrum').
    Searches by symbol AND underlying tokens. TVL > $1M threshold.
    Results are cached for 10 minutes. FREE, no key needed.
    """
    cache = get_registry().yields_cache
    cached = cache.get()
    if cached is not None:
        data = cached
        logger.debug(f"Using cached yields data (age: {cache.age:.0f}s)")
    else:
        client = get_http_client()
        try:
            r = await client.get(settings.defillama_yields_url, timeout=15)
            data = r.json()["data"]
            cache.set(data)
            logger.info(f"Refreshed yields cache with {len(data)} pools")
        except Exception as e:
            logger.error(f"DefiLlama yields fetch error: {e}")
            return f"Yield data unavailable: {e}"

    try:
        network_filter = network.strip().lower() if network else None
        if network_filter and network_filter in NETWORK_ALIASES:
            network_filter = NETWORK_ALIASES[network_filter]

        asset_upper = asset.upper()
        pools = []
        for p in data:
            if network_filter:
                pool_chain = p.get("chain", "").lower()
                if pool_chain != network_filter:
                    continue

            if (p.get("symbol") or "").upper() == asset_upper:
                if p.get("tvlUsd", 0) > 1_000_000:
                    pools.append(p)
            elif asset_upper in [t.upper() for t in (p.get("underlyingTokens") or [])]:
                if p.get("tvlUsd", 0) > 1_000_000:
                    pools.append(p)

        top = sorted(pools, key=lambda x: x.get("apy", 0), reverse=True)[:5]

        if not top:
            pools = [
                p for p in data
                if asset_upper in (p.get("symbol") or "").upper()
                and (not network_filter or p.get("chain", "").lower() == network_filter)
                and p.get("tvlUsd", 0) > 500_000
            ][:10]
            top = sorted(pools, key=lambda x: x.get("apy", 0), reverse=True)[:5]

        if not top:
            network_hint = f" on {network}" if network else ""
            return f"No yield pools found for {asset}{network_hint}. Try a broader search or check if the token has DeFi pools."

        network_label = f" on {network}" if network else " (all networks)"
        lines = [f"Top {len(top)} DeFi yield pools for {asset}{network_label}:"]
        for i, p in enumerate(top, 1):
            apy = p.get("apy", 0)
            tvl = p.get("tvlUsd", 0) / 1e6
            chain = p.get("chain", "unknown")
            project = p.get("project", "unknown")
            pool_name = p.get("symbol") or "?"
            safety = []
            if p.get("stablecoin"):
                safety.append("stablecoin")
            if p.get("rewardTokens"):
                safety.append("rewards")
            if p.get("ilRisk", True):
                safety.append("IL risk")
            if p.get("audits", 0) > 0:
                safety.append(f"{p.get('audits')} audits")

            safety_str = f" [{', '.join(safety)}]" if safety else ""
            lines.append(
                f"  {i}. {project} ({pool_name}) on {chain}: "
                f"{apy:.2f}% APY  |  TVL ${tvl:.1f}M{safety_str}"
            )
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"DefiLlama yields error: {e}")
        return f"Yield data unavailable: {e}"
