"""LangChain tools: crypto news search and token sentiment analysis."""

from __future__ import annotations

import asyncio

from langchain_core.tools import tool


@tool
async def search_crypto_news(query: str) -> str:
    """
    Searches for crypto news, scams, exploits, rug pulls via DuckDuckGo.
    FREE, no key needed.
    """
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        def _do_search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=5))

        results = await asyncio.to_thread(_do_search)
        if not results:
            return f"No news found for '{query}'."
        lines = [f"Latest results for '{query}':"]
        for r in results:
            lines.append(f"  * {r['title']}\n    {r['body']}\n    Source: {r['href']}")
        return "\n".join(lines)
    except Exception as e:
        return f"Search error: {e}"


@tool
async def analyze_token_news(token_symbol: str) -> str:
    """
    3-query news analysis for a token: regulatory risk, growth signals, market
    sentiment. Returns raw data for STRONG BUY / BUY / HOLD / SELL / AVOID signal.
    Uses DuckDuckGo - FREE, no key needed.
    """
    QUERIES = [
        (
            "Risk (Regulatory + Team)",
            f"{token_symbol} SEC CFTC lawsuit ban sanctions fraud rug pull scam 2024 2025",
        ),
        (
            "Growth (Institutional + Ecosystem)",
            f"{token_symbol} ETF institutional adoption partnership listing upgrade TVL 2025",
        ),
        (
            "Sentiment (Market + Community)",
            f"{token_symbol} analyst forecast whale sentiment FUD community outlook 2025",
        ),
    ]

    def _do_analyze():
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            sections: list[str] = []
            total_hits = 0
            for label, query in QUERIES:
                try:
                    with DDGS() as ddgs:
                        hits = list(ddgs.text(query, max_results=4))
                    if not hits:
                        continue
                    lines = [f"\n  {label}"]
                    for h in hits:
                        body = h.get("body", "")[:200]
                        lines.append(
                            f"    * [{h.get('title', '')}] {body} | {h.get('href', '')}"
                        )
                    sections.append("\n".join(lines))
                    total_hits += len(hits)
                except Exception:
                    pass

            if not sections:
                return f"No news data found for token '{token_symbol}'."

            header = (
                f"NEWS ANALYSIS - {token_symbol.upper()}"
                f"  ({total_hits} results, 3 queries)\n"
                f"  Agent: assign STRONG BUY / BUY / HOLD / SELL / AVOID\n"
                f"  based on risk, growth, and sentiment signals below.\n"
                f"{'=' * 50}"
            )
            return header + "\n".join(sections)
        except Exception as e:
            return f"Analysis error: {e}"

    return await asyncio.to_thread(_do_analyze)
