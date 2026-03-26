"""LangChain tool: DeFi yield pool discovery via direct protocol APIs.

Architecture: Strategy + Registry pattern.
  Each protocol is a YieldProvider subclass with a uniform async interface.
  The tool aggregates all registered providers transparently.

Providers (all free, no API key):
  • Beefy Finance   – multi-chain auto-compounding vaults
  • Curve Finance   – stable/crypto AMM pools (APY = fees + CRV gauge + rewards)
  • Raydium         – Solana AMM/CLMM pools
  • Morpho Blue     – Ethereum/Base isolated lending markets
  • Yearn Finance   – vault strategies via yDaemon API
  • Venus Protocol  – BSC money-market (supply APY + XVS rewards)
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.tools import tool

from app.services.http_client import get_http_client

logger = logging.getLogger(__name__)

# ── Global constants ───────────────────────────────────────────────────────────

TVL_MIN_USD = 500_000
TIMEOUT     = 12
APY_MAX_PCT = 500.0   # sanity cap — anything above is a data glitch

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

# When user searches "BNB", also match "WBNB" in pool names, etc.
TOKEN_ALIASES: dict[str, list[str]] = {
    "BNB":   ["BNB", "WBNB"],
    "ETH":   ["ETH", "WETH"],
    "BTC":   ["BTC", "WBTC", "BTCB", "TBTC", "CBBTC"],
    "SOL":   ["SOL", "WSOL"],
    "MATIC": ["MATIC", "POL"],
    "AVAX":  ["AVAX", "WAVAX"],
}


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _make_pool(
    project: str,
    name:    str,
    chain:   str,
    apy_pct: float,
    tvl_usd: float,
    url:     str = "",
) -> dict[str, Any]:
    return {
        "project": project,
        "name":    name,
        "chain":   chain,
        "apy":     round(min(apy_pct, APY_MAX_PCT), 4),
        "tvl":     tvl_usd,
        "url":     url,
    }


def _expand_asset(asset_upper: str) -> list[str]:
    """Return all symbol variants (e.g. 'BNB' → ['BNB', 'WBNB'])."""
    return TOKEN_ALIASES.get(asset_upper, [asset_upper])


def _matches(text: str, terms: list[str]) -> bool:
    t = text.upper()
    return any(term in t for term in terms)


# ── Abstract base class ────────────────────────────────────────────────────────

class YieldProvider(ABC):
    """
    Strategy interface for a single DeFi yield data source.

    Subclasses declare which networks they support via `supported_networks`
    (``None`` means "all chains"). The base-class `fetch` applies the
    network guard so individual providers never need to repeat that check.
    """

    #: Human-readable label used in log messages.
    label: str = ""

    #: Set of canonical network names this provider covers.
    #: ``None`` means the provider is chain-agnostic (e.g. Beefy).
    supported_networks: set[str] | None = None

    # ------------------------------------------------------------------
    # Public entry-point (called by the aggregator)
    # ------------------------------------------------------------------

    async def fetch(
        self,
        client,
        asset_upper: str,
        net_filter:  str | None,
    ) -> list[dict]:
        """Fetch pools, guarding against unsupported networks up front."""
        if not self._supports(net_filter):
            return []
        try:
            return await self._fetch(client, asset_upper, net_filter)
        except Exception as exc:
            logger.warning("%s fetch error: %s", self.label, exc)
            return []

    # ------------------------------------------------------------------
    # Abstract implementation hook
    # ------------------------------------------------------------------

    @abstractmethod
    async def _fetch(
        self,
        client,
        asset_upper: str,
        net_filter:  str | None,
    ) -> list[dict]:
        """Provider-specific pool retrieval logic."""
        ...

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _supports(self, net_filter: str | None) -> bool:
        return (
            net_filter is None
            or self.supported_networks is None
            or net_filter in self.supported_networks
        )


# ── Beefy Finance ──────────────────────────────────────────────────────────────

class BeefyProvider(YieldProvider):
    label = "Beefy"
    supported_networks = None  # 20+ chains

    async def _fetch(self, client, asset_upper, net_filter) -> list[dict]:
        terms = _expand_asset(asset_upper)

        vaults_r, apy_r, tvl_r = await asyncio.gather(
            client.get("https://api.beefy.finance/vaults", timeout=TIMEOUT),
            client.get("https://api.beefy.finance/apy",    timeout=TIMEOUT),
            client.get("https://api.beefy.finance/tvl",    timeout=TIMEOUT),
            return_exceptions=True,
        )
        if isinstance(vaults_r, Exception) or isinstance(apy_r, Exception):
            logger.warning("Beefy unavailable: %s", vaults_r or apy_r)
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
                _matches(v.get("token",      ""), terms)
                or _matches(v.get("earnedToken", ""), terms)
                or _matches(v.get("name",        ""), terms)
            ):
                continue

            vault_id = v.get("id", "")
            apy_pct  = (apy_map.get(vault_id) or 0.0) * 100
            tvl_usd  = tvl_map.get(vault_id) or 0.0
            if tvl_usd < TVL_MIN_USD:
                continue

            beefy_url = f"https://app.beefy.com/vault/{vault_id}"
            results.append(_make_pool("Beefy", v.get("name", vault_id), chain, apy_pct, tvl_usd, beefy_url))

        return results


# ── Curve Finance ──────────────────────────────────────────────────────────────

_CURVE_CHAINS = [
    "ethereum", "polygon", "arbitrum", "optimism", "avalanche",
    "fantom", "base", "bsc", "celo", "kava", "zkevm", "gnosis",
    "moonbeam", "fraxtal",
]
_CURVE_REGISTRIES = ["main", "factory", "factory-crypto", "factory-stable-ng"]


class CurveProvider(YieldProvider):
    label = "Curve"
    supported_networks = set(_CURVE_CHAINS)

    async def _fetch(self, client, asset_upper, net_filter) -> list[dict]:
        terms  = _expand_asset(asset_upper)
        chains = [net_filter] if net_filter else _CURVE_CHAINS

        async def _one_pool(chain: str, registry: str) -> list[dict]:
            url = f"https://api.curve.fi/api/getPools/{chain}/{registry}"
            try:
                body = (await client.get(url, timeout=TIMEOUT)).json()
                if not body.get("success"):
                    return []
                out = []
                for p in body.get("data", {}).get("poolData", []):
                    all_symbols = {
                        c.get("symbol", "").upper()
                        for key in ("coins", "wrappedCoins")
                        for c in (p.get(key) or [])
                    }
                    if not any(t in all_symbols for t in terms):
                        continue

                    base_apy   = float(p.get("latestDailyApy") or p.get("latestWeeklyApy") or 0)
                    gauge      = p.get("gaugeCrvApy") or []
                    crv_apy    = float(gauge[0]) if gauge else 0.0
                    reward_sum = sum(float(x) for x in (p.get("rewardsApys") or []) if x)
                    tvl        = float(p.get("usdTotal") or 0)

                    if tvl < TVL_MIN_USD:
                        continue

                    name     = p.get("name") or p.get("id") or "?"
                    pool_id  = p.get("id") or ""
                    curve_url = f"https://curve.fi/#/{chain}/pools/{pool_id}/deposit" if pool_id else "https://curve.fi"
                    out.append(_make_pool("Curve", name, chain, base_apy + crv_apy + reward_sum, tvl, curve_url))
                return out
            except Exception:
                return []

        nested = await asyncio.gather(
            *[_one_pool(c, reg) for c in chains for reg in _CURVE_REGISTRIES],
            return_exceptions=True,
        )
        return [p for sub in nested if isinstance(sub, list) for p in sub]


# ── Raydium (Solana) ───────────────────────────────────────────────────────────

class RaydiumProvider(YieldProvider):
    label = "Raydium"
    supported_networks = {"solana", "sol"}

    _BASE = "https://api-v3.raydium.io"
    _PAGE_SIZE = 100

    async def _fetch(self, client, asset_upper, net_filter) -> list[dict]:
        terms = _expand_asset(asset_upper)
        results = []

        for pool_type in ("standard", "concentrated"):
            page = 1
            while True:
                resp = await client.get(
                    f"{self._BASE}/pools/info/list",
                    params={
                        "poolType": pool_type,
                        "poolSortField": "liquidity",  # ← було "tvl" — ламало API
                        "sortType": "desc",
                        "pageSize": self._PAGE_SIZE,
                        "page": page,
                    },
                    timeout=TIMEOUT,
                )
                resp.raise_for_status()
                body = resp.json()

                pools: list[dict] = body.get("data", {}).get("data", [])
                if not pools:
                    break

                for p in pools:
                    mint_a = p.get("mintA", {}).get("symbol", "")
                    mint_b = p.get("mintB", {}).get("symbol", "")
                    name = f"{mint_a}-{mint_b}"

                    if not _matches(name, terms):
                        continue

                    tvl = float(p.get("tvl") or 0)
                    if tvl < TVL_MIN_USD:
                        continue

                    day = p.get("day") or {}
                    week = p.get("week") or {}
                    apr = float(day.get("apr") or week.get("apr") or 0)

                    pool_id = p.get("id", "")
                    raydium_url = (
                        f"https://raydium.io/liquidity/increase/?mode=add&pool_id={pool_id}"
                        if pool_id else "https://raydium.io/liquidity/"
                    )
                    results.append(_make_pool("Raydium", name, "solana", apr, tvl, raydium_url))

                if float(pools[-1].get("tvl") or 0) < TVL_MIN_USD:
                    break

                page += 1

        return results

# ── Morpho Blue (Ethereum + Base) ─────────────────────────────────────────────

_MORPHO_URL   = "https://blue-api.morpho.org/graphql"
_MORPHO_QUERY = """
{
  markets(first: 300, orderBy: SupplyAssetsUsd, orderDirection: Desc) {
    items {
      uniqueKey
      loanAsset       { symbol }
      collateralAsset { symbol }
      state {
        supplyApy
        supplyAssetsUsd
      }
    }
  }
}
"""


class MorphoProvider(YieldProvider):
    label = "Morpho Blue"
    supported_networks = {"ethereum", "base"}

    async def _fetch(self, client, asset_upper, net_filter) -> list[dict]:
        terms = _expand_asset(asset_upper)
        resp  = await client.post(
            _MORPHO_URL,
            json={"query": _MORPHO_QUERY},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT,
        )
        items = resp.json().get("data", {}).get("markets", {}).get("items", [])

        results = []
        for m in items:
            loan_sym = (m.get("loanAsset")       or {}).get("symbol", "").upper()
            col_sym  = (m.get("collateralAsset")  or {}).get("symbol", "").upper()
            if not (_matches(loan_sym, terms) or _matches(col_sym, terms)):
                continue

            state   = m.get("state") or {}
            apy_pct = float(state.get("supplyApy")      or 0) * 100
            tvl_usd = float(state.get("supplyAssetsUsd") or 0)
            if tvl_usd < TVL_MIN_USD:
                continue

            name       = f"{col_sym}/{loan_sym}" if col_sym else loan_sym
            unique_key = m.get("uniqueKey", "")
            morpho_url = f"https://app.morpho.org/market?id={unique_key}" if unique_key else "https://app.morpho.org"
            results.append(_make_pool("Morpho Blue", name, "ethereum", apy_pct, tvl_usd, morpho_url))

        return results


# ── Yearn Finance ──────────────────────────────────────────────────────────────

_YEARN_CHAIN_IDS: dict[str, int] = {
    "ethereum": 1,
    "arbitrum": 42161,
    "optimism": 10,
    "base":     8453,
    "polygon":  137,
}


class YearnProvider(YieldProvider):
    label = "Yearn"
    supported_networks = set(_YEARN_CHAIN_IDS)

    async def _fetch(self, client, asset_upper, net_filter) -> list[dict]:
        terms     = _expand_asset(asset_upper)
        chain_map = {
            name: cid for name, cid in _YEARN_CHAIN_IDS.items()
            if not net_filter or name == net_filter
        }

        async def _one_chain(chain: str, chain_id: int) -> list[dict]:
            resp = await client.get(
                f"https://ydaemon.yearn.fi/{chain_id}/vaults/all", timeout=TIMEOUT
            )
            resp.raise_for_status()
            out = []
            for v in resp.json():
                token_sym    = (v.get("token", {}).get("symbol") or "").upper()
                display_name = (v.get("display_name") or v.get("name") or "").upper()
                if not (_matches(token_sym, terms) or _matches(display_name, terms)):
                    continue

                apr_obj = v.get("apr") or {}
                apy_pct = float(apr_obj.get("netAPR") or apr_obj.get("grossAPR") or 0) * 100
                tvl_usd = float((v.get("tvl") or {}).get("tvl") or 0)
                if tvl_usd < TVL_MIN_USD:
                    continue

                vault_addr = v.get("address", "")
                chain_id   = _YEARN_CHAIN_IDS.get(chain, 1)
                yearn_url  = (
                    f"https://yearn.fi/vaults/{chain_id}/{vault_addr}"
                    if vault_addr else "https://yearn.fi/vaults"
                )
                out.append(_make_pool(
                    "Yearn",
                    v.get("display_name") or v.get("name", "?"),
                    chain,
                    apy_pct,
                    tvl_usd,
                    yearn_url,
                ))
            return out

        nested = await asyncio.gather(
            *[_one_chain(c, cid) for c, cid in chain_map.items()],
            return_exceptions=True,
        )
        return [p for sub in nested if isinstance(sub, list) for p in sub]


# ── Venus Protocol (BSC) ───────────────────────────────────────────────────────
# GET /markets?chainId=56&limit=500
# Response: { result: [{ underlyingSymbol, symbol,
#                        supplyApy, supplyXvsApy,   ← strings, already %
#                        liquidityCents }] }         ← TVL in US cents

class VenusProvider(YieldProvider):
    label = "Venus"
    supported_networks = {"bsc", "bnb"}

    _URL      = "https://api.venus.io/markets"
    _CHAIN_ID = "56"

    async def _fetch(self, client, asset_upper, net_filter) -> list[dict]:
        terms = _expand_asset(asset_upper)
        resp  = await client.get(
            self._URL,
            params={"chainId": self._CHAIN_ID, "limit": "500"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()

        results = []
        for m in resp.json().get("result", []):
            underlying = (m.get("underlyingSymbol") or "").upper()
            vsymbol    = (m.get("symbol")           or "").upper()
            if not (_matches(underlying, terms) or _matches(vsymbol, terms)):
                continue

            apy_pct = float(m.get("supplyApy") or 0) + float(m.get("supplyXvsApy") or 0)
            tvl_usd = float(m.get("liquidityCents") or 0) / 100
            if tvl_usd < TVL_MIN_USD:
                continue

            venus_url = "https://app.venus.io/markets"
            results.append(_make_pool(
                "Venus",
                f"{underlying} (Venus {vsymbol})",
                "bsc",
                apy_pct,
                tvl_usd,
                venus_url,
            ))
        return results


# ── Provider registry ──────────────────────────────────────────────────────────

# To add a new protocol: create a YieldProvider subclass and append it here.
PROVIDERS: list[YieldProvider] = [
    BeefyProvider(),
    CurveProvider(),
    RaydiumProvider(),
    MorphoProvider(),
    YearnProvider(),
    VenusProvider(),
]


# ── LangChain tool ─────────────────────────────────────────────────────────────

@tool
async def get_defi_yields(asset: str, network: str = "") -> str:
    """
    Fetches the top 5 highest-APY DeFi yield pools for a given asset by
    querying multiple protocol APIs directly (no aggregator needed):

      • Beefy Finance   – BSC, ETH, Polygon, Arbitrum, Optimism, Base, Avalanche,
                          Solana, Monad, Fantom, and 20+ more chains
      • Curve Finance   – ETH, Polygon, Arbitrum, Optimism, Base, BSC, Avalanche,
                          Fantom, Gnosis, zkEVM, Kava, Celo …
                          APY includes base swap-fee + CRV gauge + extra rewards
      • Raydium         – Solana AMM / CLMM pools
      • Morpho Blue     – Ethereum / Base isolated lending markets
      • Yearn Finance   – ETH, Arbitrum, Optimism, Base, Polygon vaults
      • Venus Protocol  – BSC money-market supply APY + XVS rewards
                          Best for BNB, CAKE, BUSD, XVS on BNB Chain

    Optionally filter by `network` (e.g. 'ethereum', 'bsc', 'solana', 'base',
    'arb', 'matic', 'op', 'avax', 'bnb').
    TVL > $500 K threshold applied across all providers.
    APY capped at 500 % to filter out data glitches.
    All APIs are free and require no authentication key.
    """
    net_filter: str | None = None
    if network:
        n          = network.strip().lower()
        net_filter = NETWORK_ALIASES.get(n, n) or None

    asset_upper = asset.strip().upper()
    client      = get_http_client()

    raw_results = await asyncio.gather(
        *[p.fetch(client, asset_upper, net_filter) for p in PROVIDERS],
        return_exceptions=True,
    )

    # Flatten + deduplicate
    seen:   set[tuple]  = set()
    unique: list[dict]  = []
    for res in raw_results:
        if not isinstance(res, list):
            continue
        for pool in res:
            key = (pool["project"], pool["name"], pool["chain"])
            if key not in seen:
                seen.add(key)
                unique.append(pool)

    top5 = sorted(unique, key=lambda x: x["apy"], reverse=True)[:5]

    if not top5:
        hint = f" on {network}" if network else ""
        return (
            f"No yield pools found for {asset}{hint} across "
            f"{', '.join(p.label for p in PROVIDERS)}. "
            "Check the token symbol or try without a network filter."
        )

    net_label = f" on {network}" if network else " (all networks)"
    lines = [f"Top {len(top5)} DeFi yield pools for {asset}{net_label}:"]
    for i, pool in enumerate(top5, 1):
        tvl_str = (
            f"${pool['tvl'] / 1_000_000:.1f}M"
            if pool["tvl"] >= 1_000_000
            else f"${pool['tvl'] / 1_000:.0f}K"
        )
        url_part = f"\n     🔗 {pool['url']}" if pool.get("url") else ""
        lines.append(
            f"  {i}. {pool['project']} — {pool['name']} ({pool['chain']}): "
            f"{pool['apy']:.2f}% APY  |  TVL {tvl_str}{url_part}"
        )
    return "\n".join(lines)