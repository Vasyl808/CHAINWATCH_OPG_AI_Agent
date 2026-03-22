"""USD price enrichment via CoinGecko public API (FREE, no key)."""

from __future__ import annotations

import logging

import httpx

from app.services.portfolio.constants import SPAM_PATTERN, STABLECOINS, SYMBOL_TO_COINGECKO_ID

logger = logging.getLogger(__name__)


def smart_round(value: float) -> float:
    """Round to 3 decimals for large values, 6 for small ones."""
    if value == 0:
        return 0.0
    abs_val = abs(value)
    if abs_val >= 1:
        return round(value, 3)
    elif abs_val >= 0.0001:
        return round(value, 6)
    else:
        return round(value, 9)


async def fill_usd_prices(client: httpx.AsyncClient, items: list[dict]) -> None:
    """Fill missing USD values using CoinGecko public API. FREE, no key."""
    logger.info(f"[PRICES] fill_usd_prices called with {len(items)} items")
    
    to_price: set[str] = set()
    for it in items:
        sym = str(it.get("symbol", "")).upper()
        amount = it.get("amount", 0)
        usd_val = it.get("usd_value", 0)
        logger.debug(f"[PRICES] Processing: symbol={sym}, amount={amount}, usd_value={usd_val}")

        if SPAM_PATTERN.search(sym):
            continue

        if sym in STABLECOINS:
            it["usd_value"] = smart_round(float(it.get("amount", 0) or 0))
            logger.debug(f"[PRICES] Stablecoin {sym}: usd_value={it['usd_value']}")
            continue

        if it.get("usd_value") and it["usd_value"] > 0:
            it["usd_value"] = smart_round(float(it["usd_value"]))
            continue

        if sym in SYMBOL_TO_COINGECKO_ID:
            to_price.add(sym)
            logger.debug(f"[PRICES] Will fetch price for {sym} (coingecko_id={SYMBOL_TO_COINGECKO_ID[sym]})")
        else:
            # For tokens without CoinGecko mapping, try DefiLlama search later
            to_price.add(sym)  # Add anyway, will try DefiLlama
            logger.debug(f"[PRICES] No CoinGecko mapping for {sym}, will try DefiLlama")

    logger.info(f"[PRICES] Need to fetch prices for {len(to_price)} symbols: {to_price}")
    
    if not to_price:
        return

    prices: dict[str, float] = {}
    
    # Try CoinGecko first (only for tokens with mapping)
    coingecko_symbols = {s for s in to_price if s in SYMBOL_TO_COINGECKO_ID}
    if coingecko_symbols:
        try:
            ids = ",".join({SYMBOL_TO_COINGECKO_ID[s] for s in coingecko_symbols})
            logger.info(f"[PRICES] Fetching from CoinGecko: ids={ids}")
            r = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": ids, "vs_currencies": "usd"},
                timeout=8,
            )
            data = r.json() if r.status_code == 200 else {}
            logger.info(f"[PRICES] CoinGecko response status={r.status_code}")
            
            if r.status_code == 200 and data:
                for sym in coingecko_symbols:
                    cg_id = SYMBOL_TO_COINGECKO_ID.get(sym)
                    if cg_id and cg_id in data and "usd" in data[cg_id]:
                        prices[sym] = float(data[cg_id]["usd"])
                logger.info(f"[PRICES] Got prices from CoinGecko: {prices}")
            else:
                logger.warning(f"[PRICES] CoinGecko failed, trying DefiLlama fallback")
        except Exception as e:
            logger.error(f"[PRICES] CoinGecko error: {e}")

    # Fallback to DefiLlama for remaining symbols
    remaining = to_price - set(prices.keys())
    if remaining:
        try:
            # Map symbols to DefiLlama identifiers (chain:address)
            symbol_to_llama = {
                # Sui
                "SUI": "sui:0x2::sui::SUI",
                "DEEP": "sui:0xdee9::coin::COIN", # Example, but we will mostly rely on other_chains
                "BLUE": "sui:0x2::blue::BLUE",
                # Ethereum
                "ETH": "ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "WETH": "ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                # Bitcoin (WBTC on ETH)
                "BTC": "ethereum:0x2260fac5e5542a773aa44fbcfedf7c193bc92c20",
                "WBTC": "ethereum:0x2260fac5e5542a773aa44fbcfedf7c193bc92c20",
                # Solana
                "SOL": "solana:So11111111111111111111111111111111111111112",
                "JUP": "solana:JUPyiwr1Jt3iTXwVZqQJwU9ZKNe8iLQuKJgWbSsS",
                "BONK": "solana:DezXAZ8z7PnrnRJjS9pDgSWaGfKvUHBGmXvVUKcJ9hp",
                "WIF": "solana:EKpQGSJtjMFqKkv9GjMwYqmJgNMYvKgZvZbXHwZQpump",
                # BNB Chain
                "BNB": "bsc:0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
                # Avalanche
                "AVAX": "avax:0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7",
                # Polygon
                "POL": "polygon:0x455e53cbb86018ac2b8099fd49c8f6ddc7aaf2c4",
                "MATIC": "polygon:0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0",
                # Arbitrum
                "ARB": "arbitrum:0x912ce59144191c1204e64559fe8253a0e49e6548",
                # Optimism
                "OP": "optimism:0x4200000000000000000000000000000000000042",
                # TRON
                "TRX": "tron:TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                # TON
                "TON": "ton:EQAAAAAAAAsxYzY3MzU3NzIwMjM2NzQyNjQ0NjU2NzY0NjU3MzY3NjY",
                # Cosmos
                "ATOM": "cosmos:uatom",
                "OSMO": "osmosis:uosmo",
                "INJ": "injective:inj",
                "SEI": "sei:usei",
                # Starknet
                "STRK": "starknet:0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
                # Popular tokens
                "LINK": "ethereum:0x514910771af6ca659ccdd628b59514d33cd8d6a2",
                "UNI": "ethereum:0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
                "AAVE": "ethereum:0x7fc66500c84a76ad28e6a8494a2d9f3b6b9c7b4b",
                "PEPE": "ethereum:0x6982508145454ce325ddbe47a25d4ec3d2311933",
                "SHIB": "ethereum:0x95ad61b0a150d7922dcf2fa5ad59efb04c1f1e4d",
                "DOGE": "ethereum:0xba2ae440d9c3c6d479b2c1c1c1c1c1c1c1c1c1c1",
            }
            
            llama_ids = []
            sym_to_llama_id = {}
            for sym in remaining:
                if sym in symbol_to_llama:
                    llama_ids.append(symbol_to_llama[sym])
                    sym_to_llama_id[sym] = symbol_to_llama[sym]
            
            if llama_ids:
                # Chunk IDs to avoid URL too long just in case, though usually small
                chunks = [llama_ids[i:i + 30] for i in range(0, len(llama_ids), 30)]
                for chunk in chunks:
                    ids_str = ",".join(chunk)
                    r = await client.get(
                        f"https://coins.llama.fi/prices/current/{ids_str}",
                        timeout=8,
                    )
                    if r.status_code == 200:
                        data = r.json().get("coins", {})
                        for sym in remaining:
                            lid = sym_to_llama_id.get(sym)
                            if lid and lid in data:
                                price = float(data[lid].get("price", 0) or 0)
                                if price > 0:
                                    prices[sym] = price
                                    logger.info(f"[PRICES] Got {sym} price from DefiLlama: ${price}")
        except Exception as e:
            logger.error(f"[PRICES] DefiLlama fallback error: {e}")

    logger.info(f"[PRICES] Final prices: {prices}")
        
    for it in items:
        sym = str(it.get("symbol", "")).upper()
        if not it.get("usd_value") and sym in prices:
            it["usd_value"] = smart_round(float(it.get("amount", 0) or 0) * prices[sym])
            logger.info(f"[PRICES] Updated {sym}: amount={it.get('amount')} * price={prices[sym]} = usd_value={it['usd_value']}")
