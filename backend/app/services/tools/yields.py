"""LangChain tool: DeFi yield pool discovery via Beefy Finance API.

Beefy is a multi-chain auto-compounding vault aggregator that covers 20+ networks
with a free, no-auth API. This single provider replaces the previous 6-provider
architecture to reduce memory and complexity.

Supported chains (non-exhaustive):
  ethereum, bsc, polygon, arbitrum, optimism, base, avalanche, solana,
  fantom, gnosis, zkevm, kava, celo, moonbeam, cronos, metis, aurora …
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.tools import tool

from app.services.http_client import get_http_client

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

TVL_MIN_USD = 500_000
TIMEOUT     = 12
APY_MAX_PCT = 500.0

NETWORK_ALIASES: dict[str, str] = {
    "eth":                 "ethereum",
    "ether":               "ethereum",
    "mainnet":             "ethereum",
    "bnb":                 "bsc",
    "binance":             "bsc",
    "binance smart chain": "bsc",
    "poly":                "polygon",
    "matic":               "polygon",
    "arb":                 "arbitrum",
    "arbitrum one":        "arbitrum",
    "op":                  "optimism",
    "avax":                "avalanche",
    "avax-c":              "avalanche",
    "sol":                 "solana",
    "ftm":                 "fantom",
    "xdai":                "gnosis",
    "zkevm":               "zkevm",
    "polygon zkevm":       "zkevm",
}

TOKEN_ALIASES: dict[str, list[str]] = {
    "BNB":   ["BNB", "WBNB"],
    "ETH":   ["ETH", "WETH"],
    "BTC":   ["BTC", "WBTC", "BTCB"],
    "SOL":   ["SOL", "WSOL"],
    "MATIC": ["MATIC", "POL"],
    "AVAX":  ["AVAX", "WAVAX"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _expand_asset(asset_upper: str) -> list[str]:
    return TOKEN_ALIASES.get(asset_upper, [asset_upper])


def _matches(text: str, terms: list[str]) -> bool:
    t = text.upper()
    return any(term in t for term in terms)


def _make_pool(name: str, chain: str, apy_pct: float, tvl_usd: float) -> dict[str, Any]:
    return {
        "project": "Beefy",
        "name":    name,
        "chain":   chain,
        "apy":     round(min(apy_pct, APY_MAX_PCT), 4),
        "tvl":     tvl_usd,
    }


# ── Beefy fetch ───────────────────────────────────────────────────────────────

async def _fetch_beefy(asset_upper: str, net_filter: str | None) -> list[dict]:
    """Fetch active Beefy vaults matching the asset and optional network."""
    client = get_http_client()
    terms  = _expand_asset(asset_upper)

    try:
        vaults_r, apy_r, tvl_r = await asyncio.gather(
            client.get("https://api.beefy.finance/vaults", timeout=TIMEOUT),
            client.get("https://api.beefy.finance/apy",    timeout=TIMEOUT),
            client.get("https://api.beefy.finance/tvl",    timeout=TIMEOUT),
            return_exceptions=True,
        )
    except Exception as exc:
        logger.warning("Beefy fetch failed: %s", exc)
        return []

    if isinstance(vaults_r, Exception) or isinstance(apy_r, Exception):
        logger.warning("Beefy API unavailable")
        return []

    vaults:  list[dict]       = vaults_r.json()
    apy_map: dict[str, float] = apy_r.json()

    tvl_map: dict[str, float] = {}
    if not isinstance(tvl_r, Exception):
        for _key, value in tvl_r.json().items():
            if isinstance(value, dict):
                tvl_map.update(value)

    results = []
    for v in vaults:
        if v.get("status") != "active":
            continue
        chain = (v.get("chain") or "").lower()
        if net_filter and chain != net_filter:
            continue
        if not (
            _matches(v.get("token",       ""), terms)
            or _matches(v.get("earnedToken", ""), terms)
            or _matches(v.get("name",        ""), terms)
        ):
            continue

        vault_id = v.get("id", "")
        apy_pct  = (apy_map.get(vault_id) or 0.0) * 100
        tvl_usd  = tvl_map.get(vault_id) or 0.0
        if tvl_usd < TVL_MIN_USD:
            continue

        results.append(_make_pool(v.get("name", vault_id), chain, apy_pct, tvl_usd))

    return results


# ── LangChain tool ────────────────────────────────────────────────────────────

@tool
async def get_defi_yields(asset: str, network: str = "") -> str:
    """
    Fetches the top 3 highest-APY DeFi yield pools for a given asset via
    Beefy Finance — a multi-chain auto-compounding vault aggregator covering
    20+ networks (ETH, BSC, Polygon, Arbitrum, Optimism, Base, Avalanche,
    Solana, Fantom, Gnosis, zkEVM, Kava, Celo, Cronos, Metis, Aurora …).

    Optionally filter by `network` (e.g. 'ethereum', 'bsc', 'solana', 'base',
    'arb', 'matic', 'op', 'avax', 'bnb').
    TVL > $500K threshold applied. APY capped at 500% to filter data glitches.
    Free API, no authentication required.
    """
    net_filter: str | None = None
    if network:
        n          = network.strip().lower()
        net_filter = NETWORK_ALIASES.get(n, n) or None

    asset_upper = asset.strip().upper()
    pools       = await _fetch_beefy(asset_upper, net_filter)
    top3        = sorted(pools, key=lambda x: x["apy"], reverse=True)[:3]

    if not top3:
        hint = f" on {network}" if network else ""
        return (
            f"No Beefy vaults found for {asset}{hint} (TVL > $500K). "
            "Check the token symbol or try without a network filter."
        )

    net_label = f" on {network}" if network else " (all networks)"
    lines = [f"Top {len(top3)} Beefy vaults for {asset}{net_label}:"]
    for i, pool in enumerate(top3, 1):
        tvl_str = (
            f"${pool['tvl'] / 1_000_000:.1f}M"
            if pool["tvl"] >= 1_000_000
            else f"${pool['tvl'] / 1_000:.0f}K"
        )
        lines.append(
            f"  {i}. {pool['name']} ({pool['chain']}): "
            f"{pool['apy']:.2f}% APY  |  TVL {tvl_str}"
        )
    return "\n".join(lines)