"""Bitcoin chain fetchers: mempool.space, Hiro BRC-20 and Runes."""

from __future__ import annotations

import httpx


async def fetch_bitcoin(
    client: httpx.AsyncClient,
    address: str,
) -> list[tuple[str, str, float]]:
    """Native BTC balance via mempool.space. FREE."""
    results: list[tuple[str, str, float]] = []
    try:
        r = await client.get(f"https://mempool.space/api/address/{address}", timeout=6)
        data = r.json()
        sats = (
            data["chain_stats"]["funded_txo_sum"]
            - data["chain_stats"]["spent_txo_sum"]
        )
        if sats > 0:
            results.append(("Bitcoin", "BTC", sats / 1e8))
    except Exception:
        pass
    return results


async def fetch_hiro_brc20(
    client: httpx.AsyncClient,
    address: str,
) -> list[tuple[str, str, float]]:
    """BRC-20 token balances via Hiro Ordinals API. FREE."""
    results: list[tuple[str, str, float]] = []
    offset, limit = 0, 60
    while True:
        try:
            r = await client.get(
                f"https://api.hiro.so/ordinals/v1/brc-20/balances/{address}",
                params={"limit": limit, "offset": offset},
                timeout=12,
            )
            if r.status_code != 200:
                break
            data = r.json()
            for item in data.get("results", []):
                ticker = (item.get("ticker") or "?").upper()
                bal = float(item.get("overall_balance", 0) or 0)
                if bal > 0:
                    results.append(("Bitcoin BRC-20", ticker, bal))
            total = data.get("total", 0)
            offset += limit
            if offset >= total:
                break
        except Exception:
            break
    return results


async def fetch_hiro_runes(
    client: httpx.AsyncClient,
    address: str,
) -> list[tuple[str, str, float]]:
    """Bitcoin Runes balances via Hiro API. FREE."""
    results: list[tuple[str, str, float]] = []
    offset, limit = 0, 60
    while True:
        try:
            r = await client.get(
                f"https://api.hiro.so/runes/v1/addresses/{address}/balances",
                params={"limit": limit, "offset": offset},
                timeout=12,
            )
            if r.status_code != 200:
                break
            data = r.json()
            for item in data.get("results", []):
                rune_info = item.get("rune", {})
                name = rune_info.get("spaced_name") or rune_info.get("name", "UNKNOWN")
                divisibility = int(item.get("divisibility", 0) or 0)
                raw = int(item.get("amount", 0) or 0)
                amount = raw / (10 ** divisibility) if divisibility > 0 else float(raw)
                if amount > 0:
                    results.append(("Bitcoin Runes", name, amount))
            total = data.get("total", 0)
            offset += limit
            if offset >= total:
                break
        except Exception:
            break
    return results
