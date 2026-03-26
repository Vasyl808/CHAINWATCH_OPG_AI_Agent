"""LangChain tools: crypto news search and token sentiment analysis.

News freshness strategy: try progressively wider time windows until results found.
  1st attempt: last 24 hours  (timelimit="d")
  2nd attempt: last week       (timelimit="w")
  3rd attempt: last month      (timelimit="m")
  4th attempt: no time limit   (timelimit=None)
"""

from __future__ import annotations

import asyncio
import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# DuckDuckGo timelimit codes → human label
_TIME_WINDOWS = [
    ("d", "last 24h"),
    ("w", "last week"),
    ("m", "last month"),
    (None, "all time"),
]


def _ddgs_import():
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
    return DDGS


def _search_with_fallback(query: str, max_results: int = 5) -> tuple[list[dict], str]:
    """
    Search DuckDuckGo with timelimit fallback.
    Returns (results, time_label) where time_label describes the window used.
    """
    DDGS = _ddgs_import()
    for timelimit, label in _TIME_WINDOWS:
        try:
            kwargs = {"max_results": max_results}
            if timelimit:
                kwargs["timelimit"] = timelimit
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, **kwargs))
            if hits:
                logger.debug("DDG search '%s' → %d results (%s)", query, len(hits), label)
                return hits, label
        except Exception as exc:
            logger.warning("DDG search error (timelimit=%s): %s", timelimit, exc)
    return [], "all time"


@tool
async def search_crypto_news(query: str) -> str:
    """
    Searches for crypto news, scams, exploits, rug pulls via DuckDuckGo.
    Tries to return the freshest results possible (last 24h → week → month → all time).
    FREE, no key needed.
    """
    def _run():
        try:
            results, label = _search_with_fallback(query, max_results=5)
            if not results:
                return f"No news found for '{query}'."
            lines = [f"Latest results for '{query}' ({label}):"]
            for r in results:
                lines.append(
                    f"  * {r['title']}\n"
                    f"    {r.get('body', '')}\n"
                    f"    Source: {r['href']}"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"Search error: {e}"

    return await asyncio.to_thread(_run)


@tool
async def analyze_token_news(token_symbol: str) -> str:
    """
    3-query news analysis for a token: regulatory risk, growth signals, market
    sentiment. Returns raw data for STRONG BUY / BUY / HOLD / SELL / AVOID signal.
    Tries to fetch the freshest news (last 24h → week → month → all time).
    Uses DuckDuckGo - FREE, no key needed.
    """
    QUERIES = [
        (
            "Risk (Regulatory + Team)",
            f"{token_symbol} SEC CFTC lawsuit ban sanctions fraud rug pull scam",
        ),
        (
            "Growth (Institutional + Ecosystem)",
            f"{token_symbol} ETF institutional adoption partnership listing upgrade TVL",
        ),
        (
            "Sentiment (Market + Community)",
            f"{token_symbol} analyst forecast whale sentiment FUD community outlook",
        ),
    ]

    def _run():
        try:
            sections: list[str] = []
            total_hits = 0
            freshness_labels: list[str] = []

            for label, query in QUERIES:
                try:
                    hits, time_label = _search_with_fallback(query, max_results=4)
                    if not hits:
                        continue
                    freshness_labels.append(time_label)
                    lines = [f"\n  {label} (freshness: {time_label})"]
                    for h in hits:
                        body = h.get("body", "")[:200]
                        lines.append(
                            f"    * [{h.get('title', '')}] {body} | {h.get('href', '')}"
                        )
                    sections.append("\n".join(lines))
                    total_hits += len(hits)
                except Exception as exc:
                    logger.warning("analyze_token_news section error: %s", exc)

            if not sections:
                return f"No news data found for token '{token_symbol}'."

            # Determine the dominant freshness window used
            dominant = freshness_labels[0] if freshness_labels else "unknown"
            header = (
                f"NEWS ANALYSIS - {token_symbol.upper()}"
                f"  ({total_hits} results, freshness: {dominant})\n"
                f"  Agent: assign STRONG BUY / BUY / HOLD / SELL / AVOID\n"
                f"  based on risk, growth, and sentiment signals below.\n"
                f"{'=' * 50}"
            )
            return header + "\n".join(sections)
        except Exception as e:
            return f"Analysis error: {e}"

    return await asyncio.to_thread(_run)
