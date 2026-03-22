"""Other chain fetchers: TRON, TON, BNB Beacon, Starknet, Sui."""

from __future__ import annotations

import asyncio

import httpx

from app.core.config import settings
from app.services.portfolio.constants import STARKNET_TOKENS, STARKNET_BALANCE_SELECTOR


# ---------------------------------------------------------------------------
# BNB Beacon Chain
# ---------------------------------------------------------------------------

async def fetch_bnb_beacon(
    client: httpx.AsyncClient,
    address: str,
) -> list[tuple[str, str, float]]:
    """BEP-2 token balances via Binance DEX public API. FREE."""
    results: list[tuple[str, str, float]] = []
    try:
        r = await client.get(f"https://dex.binance.org/api/v1/account/{address}", timeout=10)
        if r.status_code != 200:
            return results
        for bal in r.json().get("balances", []):
            symbol = bal.get("symbol", "?").split("-")[0].upper()
            total = (
                float(bal.get("free", 0) or 0)
                + float(bal.get("locked", 0) or 0)
                + float(bal.get("frozen", 0) or 0)
            )
            if total > 0:
                results.append(("BNB Beacon Chain", symbol, total))
    except Exception:
        pass
    return results


# ---------------------------------------------------------------------------
# TRON
# ---------------------------------------------------------------------------

async def fetch_tron(
    client: httpx.AsyncClient,
    address: str,
) -> list[tuple[str, str, float]]:
    """TRX + TRC-20 + TRC-10 balances via TronScan. FREE."""
    results: list[tuple[str, str, float]] = []
    try:
        r = await client.get(
            "https://apilist.tronscan.org/api/account",
            params={"address": address},
            timeout=12,
        )
        if r.status_code != 200:
            return results
        data = r.json()

        trx_sun = int(data.get("balance", 0) or 0)
        if trx_sun > 0:
            results.append(("TRON", "TRX", trx_sun / 1_000_000))

        for tok in data.get("trc20token_balances", []):
            sym = tok.get("tokenAbbr") or tok.get("tokenName", "?")
            raw = int(tok.get("balance", 0) or 0)
            dec = int(tok.get("tokenDecimal", 6) or 6)
            amount = raw / (10 ** dec)
            if amount > 0:
                results.append(("TRON TRC-20", sym, amount))

        for tok in data.get("tokenBalances", []):
            sym = tok.get("name", "?")
            raw = int(tok.get("balance", 0) or 0)
            dec = int(tok.get("precision", 6) or 6)
            amount = raw / (10 ** dec)
            if amount > 0:
                results.append(("TRON TRC-10", sym, amount))
    except Exception:
        pass
    return results


# ---------------------------------------------------------------------------
# TON
# ---------------------------------------------------------------------------

async def fetch_ton(
    client: httpx.AsyncClient,
    address: str,
) -> list[tuple[str, str, float]]:
    """TON + Jetton balances via tonapi.io. FREE."""
    results: list[tuple[str, str, float]] = []
    headers = {"Accept": "application/json"}
    try:
        r = await client.get(
            f"https://tonapi.io/v2/accounts/{address}", headers=headers, timeout=8
        )
        if r.status_code == 200:
            nano = int(r.json().get("balance", 0) or 0)
            if nano > 0:
                results.append(("TON", "TON", nano / 1_000_000_000))
    except Exception:
        pass
    try:
        r2 = await client.get(
            f"https://tonapi.io/v2/accounts/{address}/jettons",
            headers=headers,
            params={"currencies": "usd"},
            timeout=12,
        )
        if r2.status_code == 200:
            for item in r2.json().get("balances", []):
                meta = item.get("jetton", {})
                sym = meta.get("symbol", "?")
                raw = int(item.get("balance", 0) or 0)
                dec = int(meta.get("decimals", 9) or 9)
                amount = raw / (10 ** dec)
                if amount > 0:
                    results.append(("TON Jetton", sym, amount))
    except Exception:
        pass
    return results


# ---------------------------------------------------------------------------
# Starknet
# ---------------------------------------------------------------------------

async def fetch_starknet(
    client: httpx.AsyncClient,
    address: str,
) -> list[tuple[str, str, float]]:
    """ERC-20 balances on Starknet via public JSON-RPC. FREE."""
    results: list[tuple[str, str, float]] = []
    rpc = "https://starknet-mainnet.public.blastapi.io"

    async def _call(contract: str, symbol: str, decimals: int) -> None:
        try:
            r = await client.post(
                rpc,
                json={
                    "jsonrpc": "2.0", "id": 1,
                    "method": "starknet_call",
                    "params": {
                        "request": {
                            "contract_address": contract,
                            "entry_point_selector": STARKNET_BALANCE_SELECTOR,
                            "calldata": [address],
                        },
                        "block_id": "latest",
                    },
                },
                timeout=8,
            )
            res = r.json().get("result", [])
            if len(res) >= 2:
                raw = (int(res[1], 16) << 128) | int(res[0], 16)
            elif len(res) == 1:
                raw = int(res[0], 16)
            else:
                return
            amount = raw / (10 ** decimals)
            if amount > 0:
                results.append(("Starknet", symbol, amount))
        except Exception:
            pass

    await asyncio.gather(*[_call(c, s, d) for c, s, d in STARKNET_TOKENS])

    # Deduplicate
    seen: dict[str, tuple[str, str, float]] = {}
    for net, sym, amt in results:
        if sym not in seen or amt > seen[sym][2]:
            seen[sym] = (net, sym, amt)
    return list(seen.values())


# ---------------------------------------------------------------------------
# Sui
# ---------------------------------------------------------------------------

async def fetch_sui(
    client: httpx.AsyncClient,
    address: str,
    add_fn,
) -> None:
    """Fetch all Sui coin balances via public JSON-RPC. FREE."""
    import logging
    logger = logging.getLogger(__name__)
    
    coins_data: list[tuple[str, str, float]] = []  # (coin_type, symbol, amount)
    
    try:
        r = await client.post(
            settings.sui_rpc_url,
            json={
                "jsonrpc": "2.0", "id": 1,
                "method": "suix_getAllBalances",
                "params": [address],
            },
            timeout=8,
        )
        result = r.json().get("result", [])
        logger.info(f"[SUI] Found {len(result)} coin types for {address[:16]}...")
        
        for b in result:
            total = int(b.get("totalBalance", 0))
            if total == 0:
                continue
            coin_type = b["coinType"]
            try:
                meta_r = await client.post(
                    settings.sui_rpc_url,
                    json={
                        "jsonrpc": "2.0", "id": 1,
                        "method": "suix_getCoinMetadata",
                        "params": [coin_type],
                    },
                    timeout=4,
                )
                meta = meta_r.json().get("result", {})
                symbol = meta.get("symbol", coin_type.split("::")[-1])
                decimals = meta.get("decimals", 9)
            except Exception:
                symbol = coin_type.split("::")[-1]
                decimals = 9
            
            amount = total / (10 ** decimals)
            
            # Anti-spam: Protect native SUI symbol from being overwritten by fakes
            # because the portfolio aggregator deduplicates by (network, symbol).
            if symbol.upper() == "SUI" and coin_type != "0x2::sui::SUI":
                symbol = f"Fake_SUI_{coin_type.split('::')[0][:8]}"
            
            logger.info(f"[SUI] Coin: {symbol}, raw={total}, decimals={decimals}, amount={amount}")
            coins_data.append((coin_type, symbol, amount))
    except Exception as e:
        logger.error(f"[SUI] Error fetching balances: {e}")

    # Fetch prices from DefiLlama for Sui tokens
    from app.services.portfolio.constants import STABLECOINS
    from app.services.portfolio.prices import smart_round
    
    prices: dict[str, float] = {}
    sui_tokens = [(ct, sym, amt) for ct, sym, amt in coins_data if sym.upper() not in STABLECOINS]
    
    if sui_tokens:
        try:
            # DefiLlama supports Sui tokens
            chunk_size = 30
            for i in range(0, len(sui_tokens), chunk_size):
                chunk = sui_tokens[i:i + chunk_size]
                coins_str = ",".join([f"sui:{ct}" for ct, sym, amt in chunk])
                r = await client.get(
                    f"https://coins.llama.fi/prices/current/{coins_str}",
                    timeout=8,
                )
                if r.status_code == 200:
                    data = r.json().get("coins", {})
                    for k, v in data.items():
                        # k is like "sui:0x2::sui::SUI"
                        ct = k.split("sui:", 1)[-1]
                        price = float(v.get("price", 0) or 0)
                        if price > 0:
                            prices[ct] = price
                            logger.info(f"[SUI] Got price for {ct} from DefiLlama: ${price}")
        except Exception as e:
            logger.warning(f"[SUI] DefiLlama error: {e}")

    # Add tokens with prices
    for coin_type, symbol, amount in coins_data:
        sym_upper = symbol.upper()
        if sym_upper in STABLECOINS:
            usd = smart_round(amount)
        elif coin_type in prices:
            usd = smart_round(amount * prices[coin_type])
        else:
            usd = 0.0
        logger.info(f"[SUI] Adding: symbol={symbol}, amount={amount}, usd={usd}")
        add_fn("Sui", symbol, amount, usd)
