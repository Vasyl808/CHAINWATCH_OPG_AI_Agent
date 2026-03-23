"""LangChain tool: token news sentiment analysis via DuckDuckGo."""

from __future__ import annotations

import asyncio

from langchain_core.tools import tool


@tool
async def search_crypto_news(token_symbol: str) -> str:
    """
    2-query news analysis for a token: risk signals and market sentiment.
    Returns data for STRONG BUY / BUY / HOLD / SELL / AVOID signal.
    Uses DuckDuckGo — FREE, no key needed.
    """
    QUERIES = [
        (
            "Risk",
            f"{token_symbol} lawsuit ban fraud rug pull scam hack 2025",
        ),
        (
            "Sentiment",
            f"{token_symbol} ETF adoption forecast analyst outlook 2025",
        ),
    ]

    def _do_analyze() -> str:
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            sections: list[str] = []
            for label, query in QUERIES:
                try:
                    with DDGS() as ddgs:
                        hits = list(ddgs.text(query, max_results=3))
                    if not hits:
                        continue
                    lines = [f"\n  [{label}]"]
                    for h in hits:
                        body = h.get("body", "")[:150]
                        lines.append(f"    * {h.get('title', '')} — {body}")
                    sections.append("\n".join(lines))
                except Exception:
                    pass

            if not sections:
                return f"No news data found for '{token_symbol}'."

            return (
                f"NEWS — {token_symbol.upper()} | "
                f"Assign: STRONG BUY / BUY / HOLD / SELL / AVOID\n"
                + "\n".join(sections)
            )
        except Exception as e:
            return f"Analysis error: {e}"

    return await asyncio.to_thread(_do_analyze)