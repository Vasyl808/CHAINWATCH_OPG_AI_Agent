"""EVM chain fetchers: Covalent tokens, native RPC balances, Hyperliquid."""

from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import settings
from app.services.portfolio.constants import EVM_CHAINS, SPAM_PATTERN, STABLECOINS

logger = logging.getLogger(__name__)


async def fetch_covalent_tokens(
    client: httpx.AsyncClient,
    chain_name: str,
    covalent_chain_id: str,
    address: str,
) -> list[tuple[str, str, float, float]]:
    """
    Fetch all ERC-20 + native token balances for one chain via Covalent GoldRush.
    Returns: list of (chain_name, symbol, amount, usd_value)
    """
    results: list[tuple[str, str, float, float]] = []
    try:
        r = await client.get(
            f"https://api.covalenthq.com/v1/{covalent_chain_id}/address/{address}/balances_v2/",
            params={"no-spam": "true", "no-nft-fetch": "true"},
            headers={"Authorization": f"Bearer {settings.covalent_api_key}"},
            timeout=15,
        )
        if r.status_code != 200:
            return results
        for item in r.json().get("data", {}).get("items", []):
            sym = item.get("contract_ticker_symbol") or item.get("contract_name", "?")

            if SPAM_PATTERN.search(sym):
                continue

            dec = item.get("contract_decimals")
            if dec is None or dec == 0:
                sym_upper = sym.upper()
                if sym_upper in {"USDC", "USDT", "BUSD", "TUSD", "GUSD", "USDD", "USDP"}:
                    dec = 6
                else:
                    dec = 18
            else:
                dec = int(dec)

            raw = int(item.get("balance", 0) or 0)
            amount = raw / (10 ** dec)

            sym_upper = sym.upper()
            if sym_upper in STABLECOINS:
                usd = amount
            else:
                usd = float(item.get("quote", 0) or 0)

            if amount > 0.000001:
                results.append((chain_name, sym, amount, usd))
    except Exception as e:
        logger.debug(f"Covalent {chain_name} error: {e}")
    return results


async def fetch_evm_native(
    client: httpx.AsyncClient,
    address: str,
    add_fn,
) -> None:
    """Fetch native coin balances across all EVM chains via direct JSON-RPC."""
    native_payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [address, "latest"],
        "id": 1,
    }

    async def _native(chain_name: str, rpc: str, sym: str) -> None:
        try:
            r = await client.post(rpc, json=native_payload, timeout=5)
            raw = r.json().get("result", "0x0") or "0x0"
            bal = int(raw, 16) / 1e18
            if bal > 0.000001:
                add_fn(chain_name, sym, bal)
        except Exception:
            pass

    await asyncio.gather(*[
        _native(name, rpc, sym)
        for name, _, sym, rpc in EVM_CHAINS
    ])


async def fetch_evm_covalent(
    client: httpx.AsyncClient,
    address: str,
    add_fn,
) -> None:
    """Fetch ERC-20 token balances across all EVM chains via Covalent."""
    cov_tasks = [
        fetch_covalent_tokens(client, name, cov_id, address)
        for name, cov_id, _, _ in EVM_CHAINS
    ]
    for batch in await asyncio.gather(*cov_tasks):
        for net, sym, amt, usd in batch:
            add_fn(net, sym, amt, usd)


async def fetch_hyperliquid(
    client: httpx.AsyncClient,
    address: str,
    add_fn,
) -> None:
    """Fetch Hyperliquid spot + perp balances."""
    try:
        r = await client.post(
            settings.hyperliquid_api_url,
            json={"type": "spotState", "user": address},
            timeout=6,
        )
        for coin, info in r.json().get("balances", {}).items():
            amount = float(info.get("total", 0) or 0)
            if amount > 0:
                usd = amount if coin.upper() in STABLECOINS else 0.0
                add_fn("Hyperliquid Spot", coin.upper(), amount, usd)
    except Exception:
        pass

    try:
        r = await client.post(
            settings.hyperliquid_api_url,
            json={"type": "clearinghouseState", "user": address},
            timeout=6,
        )
        result = r.json()
        margin = float(result.get("marginSummary", {}).get("accountValue", 0))
        if margin > 0:
            add_fn("Hyperliquid", "USDC", margin, margin)
        for pos in result.get("assetPositions", []):
            pos_data = pos.get("position", {})
            coin = pos_data.get("coin", "UNKNOWN")
            size = float(pos_data.get("szi", 0) or 0)
            if size != 0:
                usd_val = abs(float(pos_data.get("positionValue", 0) or 0))
                add_fn("Hyperliquid Perp", coin, size, usd_val)
    except Exception:
        pass
