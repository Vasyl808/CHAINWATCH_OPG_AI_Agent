"""Cosmos chain fetchers: bank balances via cosmos.directory REST proxy."""

from __future__ import annotations

import httpx

from app.services.portfolio.constants import COSMOS_CHAINS


def resolve_cosmos_denom(denom: str, native_sym: str, native_exp: int) -> tuple[str, int]:
    if denom.startswith("ibc/"):
        return "IBC-" + denom[4:8], 6
    if denom.startswith("factory/"):
        return denom.rsplit("/", 1)[-1][:12].upper(), 6
    if denom == f"u{native_sym.lower()}":
        return native_sym, 6
    if denom == f"a{native_sym.lower()}":
        return native_sym, 18
    if denom == native_sym.lower():
        return native_sym, native_exp
    if denom.startswith("u"):
        return denom[1:].upper(), 6
    if denom.startswith("a"):
        return denom[1:].upper(), 18
    return denom[:12].upper(), 6


async def fetch_cosmos(
    client: httpx.AsyncClient,
    address: str,
    chain_id: str,
    native_sym: str,
    native_exp: int,
) -> list[tuple[str, str, float]]:
    """Bank balances via cosmos.directory REST proxy. FREE."""
    results: list[tuple[str, str, float]] = []
    display = chain_id.title().replace("Cosmoshub", "Cosmos Hub")
    try:
        r = await client.get(
            f"https://rest.cosmos.directory/{chain_id}/cosmos/bank/v1beta1/balances/{address}",
            params={"pagination.limit": "200"},
            timeout=10,
        )
        if r.status_code != 200:
            return results
        for bal in r.json().get("balances", []):
            denom = bal.get("denom", "")
            raw = int(bal.get("amount", 0) or 0)
            if raw == 0:
                continue
            sym, dec = resolve_cosmos_denom(denom, native_sym, native_exp)
            amount = raw / (10 ** dec)
            if amount > 0:
                results.append((display, sym, amount))
    except Exception:
        pass
    return results


def get_matching_cosmos_chains(address: str) -> list[tuple[str, str, int]]:
    """Return cosmos chain configs matching the given address prefix."""
    return [
        (chain_id, sym, exp)
        for prefix, chain_id, sym, exp in COSMOS_CHAINS
        if address.startswith(prefix)
    ]
