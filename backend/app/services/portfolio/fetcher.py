"""Main portfolio orchestrator: routes address -> chain-specific fetchers."""

from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.services.http_client import get_http_client
from app.services.portfolio.bitcoin import fetch_bitcoin, fetch_hiro_brc20, fetch_hiro_runes
from app.services.portfolio.cosmos import fetch_cosmos, get_matching_cosmos_chains
from app.services.portfolio.evm import (
    fetch_covalent_tokens,
    fetch_evm_covalent,
    fetch_evm_native,
    fetch_hyperliquid,
)
from app.services.portfolio.other_chains import (
    fetch_bnb_beacon,
    fetch_starknet,
    fetch_sui,
    fetch_ton,
    fetch_tron,
)
from app.services.portfolio.prices import fill_usd_prices
from app.services.portfolio.solana import fetch_solana

logger = logging.getLogger(__name__)


async def fetch_portfolio(address: str) -> list[dict]:
    """
    Detect blockchain from address format and return all token balances.

    Routing:
      bc1.../1.../3...    -> Bitcoin + BRC-20 + Runes
      bnb1... (43 chars)  -> BNB Beacon Chain BEP-2
      T... (34 chars)     -> TRON TRX + TRC-20 + TRC-10
      EQ.../UQ... (48)    -> TON + Jettons
      cosmos1/osmo1/...   -> Cosmos chains
      0x... (66 chars)    -> Sui + Starknet
      0x... (42 chars)    -> EVM 32 chains
      [32-44 chars]       -> Solana SOL + SPL
    """
    address = address.strip()
    results_map: dict[tuple[str, str], dict] = {}

    def _add(network: str, symbol: str, amount: float, usd: float = 0.0) -> None:
        logger.debug(f"[PORTFOLIO] _add called: network={network}, symbol={symbol}, amount={amount}, usd={usd}")
        logger.debug(f"[PORTFOLIO] results_map: {results_map}")
        key = (network, symbol)
        if key in results_map:
            results_map[key]["amount"] = max(results_map[key]["amount"], amount)
            if usd > results_map[key]["usd_value"]:
                results_map[key]["usd_value"] = usd
        else:
            results_map[key] = {
                "symbol": symbol,
                "amount": amount,
                "usd_value": usd,
                "network": network,
            }

    client = get_http_client()

    # -- Bitcoin --
    if address.startswith(("bc1", "1", "3")) and len(address) > 25:
        if settings.covalent_api_key:
            cov_res = await fetch_covalent_tokens(client, "Bitcoin", "btc-mainnet", address)
            for net, sym, amt, usd in cov_res:
                if sym.upper() == "BTC":
                    _add("Bitcoin", "BTC", amt, usd)
                else:
                    _add(net, sym, amt, usd)

        btc, brc20, runes = await asyncio.gather(
            fetch_bitcoin(client, address),
            fetch_hiro_brc20(client, address),
            fetch_hiro_runes(client, address),
        )
        for net, sym, amt in [*btc, *brc20, *runes]:
            _add(net, sym, amt)

    # -- BNB Beacon Chain --
    elif address.startswith("bnb1") and len(address) == 43:
        for net, sym, amt in await fetch_bnb_beacon(client, address):
            _add(net, sym, amt)

    # -- TRON --
    elif address.startswith("T") and len(address) == 34 and address.isalnum():
        if settings.covalent_api_key:
            cov_res = await fetch_covalent_tokens(client, "TRON TRC-20", "tron-mainnet", address)
            for net, sym, amt, usd in cov_res:
                if sym.upper() == "TRX":
                    _add("TRON", "TRX", amt, usd)
                else:
                    _add(net, sym, amt, usd)

        for net, sym, amt in await fetch_tron(client, address):
            _add(net, sym, amt)

    # -- TON --
    elif address.startswith(("EQ", "UQ")) and len(address) == 48:
        if settings.covalent_api_key:
            cov_res = await fetch_covalent_tokens(client, "TON", "ton-mainnet", address)
            for net, sym, amt, usd in cov_res:
                if sym.upper() in ("TON", "TONCOIN"):
                    _add("TON", "TON", amt, usd)
                else:
                    _add(net, sym, amt, usd)

        for net, sym, amt in await fetch_ton(client, address):
            _add(net, sym, amt)

    # -- Cosmos --
    elif any(address.startswith(p) for p, *_ in [
        ("cosmos1",), ("osmo1",), ("juno1",), ("stars1",), ("axelar1",),
        ("inj1",), ("sei1",), ("strd1",), ("dydx1",), ("noble1",),
        ("neutron1",), ("archway1",), ("umee1",), ("kava1",), ("evmos1",),
    ]):
        matched = get_matching_cosmos_chains(address)
        batches = await asyncio.gather(*[
            fetch_cosmos(client, address, cid, sym, exp)
            for cid, sym, exp in matched
        ])
        for batch in batches:
            for net, sym, amt in batch:
                _add(net, sym, amt)

    # -- Solana --
    elif not address.startswith("0x") and 32 <= len(address) <= 44:
        if settings.covalent_api_key:
            cov_res = await fetch_covalent_tokens(client, "Solana SPL", "solana-mainnet", address)
            for net, sym, amt, usd in cov_res:
                if sym.upper() == "SOL":
                    _add("Solana", "SOL", amt, usd)
                else:
                    _add(net, sym, amt, usd)

        await fetch_solana(client, address, _add)

    # -- Sui + Starknet (0x + 64 hex = 66 total) --
    elif address.startswith("0x") and len(address) == 66:
        if settings.covalent_api_key:
            cov_sui, cov_stark = await asyncio.gather(
                fetch_covalent_tokens(client, "Sui", "sui-mainnet", address),
                fetch_covalent_tokens(client, "Starknet", "starknet-mainnet", address),
            )
            for net, sym, amt, usd in [*cov_sui, *cov_stark]:
                _add(net, sym, amt, usd)

        _, starknet_results = await asyncio.gather(
            fetch_sui(client, address, _add),
            fetch_starknet(client, address),
        )
        for net, sym, amt in starknet_results:
            _add(net, sym, amt)

    # -- EVM (0x + 40 hex = 42 chars) --
    elif address.startswith("0x") and len(address) == 42:
        await fetch_evm_native(client, address, _add)

        if settings.covalent_api_key:
            await fetch_evm_covalent(client, address, _add)
        else:
            logger.debug(
                "COVALENT_API_KEY not set - ERC-20 tokens skipped. "
                "Get a free key at https://goldrush.dev"
            )

        await fetch_hyperliquid(client, address, _add)

    # -- USD price fill --
    items = list(results_map.values())
    logger.info(f"[PORTFOLIO] Before fill_usd_prices: {len(items)} items")
    for it in items:
        logger.info(f"[PORTFOLIO] Item: network={it['network']}, symbol={it['symbol']}, amount={it['amount']}, usd_value={it['usd_value']}")
    
    try:
        await fill_usd_prices(client, items)
    except Exception as e:
        logger.error(f"[PORTFOLIO] Error in fill_usd_prices: {e}")

    logger.info(f"[PORTFOLIO] Final result: {len(items)} items")
    for it in items:
        logger.info(f"[PORTFOLIO] Final: network={it['network']}, symbol={it['symbol']}, amount={it['amount']}, usd_value={it.get('usd_value', 0)}")

    return items
