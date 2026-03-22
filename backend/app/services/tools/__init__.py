from .balance import get_omnichain_balance
from .yields import get_defi_yields
from .security import get_historical_hacks
from .news import search_crypto_news, analyze_token_news

ALL_TOOLS = [
    get_omnichain_balance,
    get_defi_yields,
    search_crypto_news,
    get_historical_hacks,
    analyze_token_news,
]

__all__ = ["ALL_TOOLS"]
