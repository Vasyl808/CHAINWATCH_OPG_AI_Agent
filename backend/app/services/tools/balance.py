"""LangChain tool: omnichain balance discovery."""

from langchain_core.tools import tool

from app.services.portfolio import fetch_portfolio


@tool
async def get_omnichain_balance(address: str) -> str:
    """
    Detects blockchain from address format and returns native coin + all token
    balances across 50+ blockchains. No API key required for basic usage.
    Set COVALENT_API_KEY (free at goldrush.dev) for full ERC-20 token discovery
    across 200+ EVM chains.
    """
    portfolio = await fetch_portfolio(address)
    if not portfolio:
        return (
            f"No balances found for {address} - "
            "wallet may be empty or APIs are temporarily overloaded."
        )

    lines = []
    for item in portfolio:
        usd_val = item.get("usd_value", 0.0)
        amount = item.get("amount", 0.0)
        
        if usd_val and amount > 0:
            price = usd_val / amount
            usd_str = f" (Price: ${price:.2f} | Total: ${usd_val:.2f})"
        elif usd_val:
            usd_str = f" (Total: ${usd_val:.2f})"
        else:
            usd_str = ""
            
        lines.append(f"{item['network']} [{item['symbol']}]: {amount:.4f}{usd_str}")

    return "Balances found:\n" + "\n".join(f"  * {line}" for line in lines)
