"""Solana chain fetchers: SOL native, SPL tokens, Jupiter price."""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.services.registry import get_registry


async def _get_solana_token_map(client: httpx.AsyncClient) -> dict:
    """Jupiter strict token list for mint -> symbol resolution. FREE, no key."""
    cache = get_registry().solana_token_cache
    cached = cache.get()
    if cached is not None:
        return cached
    try:
        resp = await client.get(settings.jupiter_token_list_url, timeout=12)
        token_map = {t["address"]: t["symbol"] for t in resp.json()}
    except Exception:
        token_map = {}
    cache.set(token_map)
    return token_map


async def fetch_solana(
    client: httpx.AsyncClient,
    address: str,
    add_fn,
) -> None:
    """Fetch SOL native + SPL token balances + Jupiter prices."""
    sol_rpc = settings.sol_rpc_url

    # Native SOL
    try:
        r = await client.post(
            sol_rpc,
            json={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [address]},
            timeout=6,
        )
        sol = r.json().get("result", {}).get("value", 0) / 1e9
        if sol > 0:
            add_fn("Solana", "SOL", sol)
    except Exception:
        pass

    # SPL tokens
    token_map = await _get_solana_token_map(client)
    spl_aggregated: dict[str, dict] = {}

    for program_id in [
        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
    ]:
        try:
            r = await client.post(
                sol_rpc,
                json={
                    "jsonrpc": "2.0", "id": 1,
                    "method": "getTokenAccountsByOwner",
                    "params": [address, {"programId": program_id}, {"encoding": "jsonParsed"}],
                },
                timeout=12,
            )
            for acc in r.json().get("result", {}).get("value", []):
                info = acc["account"]["data"]["parsed"]["info"]
                mint = info["mint"]
                raw = int(info["tokenAmount"]["amount"])
                dec = info["tokenAmount"]["decimals"]
                if raw > 0:
                    amount = raw / (10 ** dec)
                    if mint in spl_aggregated:
                        spl_aggregated[mint]["amount"] += amount
                    else:
                        spl_aggregated[mint] = {
                            "symbol": token_map.get(mint, mint[:8] + "..."),
                            "amount": amount
                        }
        except Exception:
            pass

    # Jupiter price feed
    spl_prices: dict[str, float] = {}
    if spl_aggregated:
        try:
            mints = list(spl_aggregated.keys())
            chunk_size = 100
            for i in range(0, len(mints), chunk_size):
                chunk = mints[i:i + chunk_size]
                r = await client.get(
                    "https://api.jup.ag/price/v2?ids=" + ",".join(chunk),
                    timeout=10,
                )
                for mint, info in r.json().get("data", {}).items():
                    if info and info.get("price"):
                        spl_prices[mint] = float(info["price"])
        except Exception:
            pass

    for mint, data in spl_aggregated.items():
        symbol = data["symbol"]
        amount = data["amount"]
        usd = amount * spl_prices.get(mint, 0)
        # Anti-spam: Protect native SOL symbol from being overwritten by fakes inside SPL
        if symbol.upper() == "SOL" and mint != "So11111111111111111111111111111111111111112":
            symbol = f"Fake_SOL_{mint[:8]}"
            
        add_fn("Solana SPL", symbol, amount, usd)
