"""AgentPool: manages shared LLM, concurrency, and SSE streaming."""

from __future__ import annotations

import asyncio
import json
import traceback
import warnings
import logging
import psutil
import os
from typing import Any, AsyncGenerator

logger = logging.getLogger(__name__)

def _log_ram(context: str):
    process = psutil.Process(os.getpid())
    rss_mb = process.memory_info().rss / (1024 * 1024)
    logger.info(f"[RAM LOG PID:{os.getpid()}] {context}: {rss_mb:.2f} MB")

import opengradient as og
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from app.core.config import settings
from app.services.tools import ALL_TOOLS
from app.services.agent.prompts import STEP_MAP, build_prompt

# Apply LLM patches on first import of this module
import app.services.agent.llm_patch  # noqa: F401

warnings.filterwarnings("ignore")


def _make_sse(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


class AgentPool:
    """
    Pool that manages a single shared LLM client, caches its OPG
    approval, and enforces concurrency limits via asyncio.Semaphore.

    Created and stored in ServiceRegistry during app lifespan — no
    class-level singleton or module globals.
    """

    def __init__(self, private_key: str, max_concurrent: int = 5):
        self.private_key = private_key
        self.max_concurrent = max_concurrent

        self._llm_client: og.LLM | None = None
        self._agent: Any = None
        self._semaphore: asyncio.Semaphore | None = None
        self._waiting_queues: list[asyncio.Event] = []
        self._active_count: int = 0

    def _ensure_initialized(self):
        """Lazy initialization of async primitives and LLM resources."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)

        if self._llm_client is None:
            self._llm_client = og.LLM(private_key=self.private_key)
            self._llm_client.ensure_opg_approval(opg_amount=settings.og_opg_approval_amount)

            _langchain_llm = og.agents.langchain_adapter(
                private_key=self.private_key,
                model_cid=settings.og_model_cid,
                max_tokens=settings.og_llm_max_tokens,
            )
            self._agent = create_react_agent(_langchain_llm, ALL_TOOLS)

    def get_status(self) -> dict:
        """Returns the current pool load for this worker process."""
        import os
        return {
            "worker_pid": os.getpid(),
            "active_agents": self._active_count,
            "queued_agents": len(self._waiting_queues),
            "max_concurrent": self.max_concurrent,
            "total_slots": self.max_concurrent,
        }

    async def stream_analysis(
        self,
        address: str,
        token: str | None = None,
        network: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Yields SSE-formatted strings for a full wallet analysis.
        Enforces concurrency limits and yields queue position updates if waiting.
        """
        _log_ram(f"stream_analysis START for address {address}")
        yield _make_sse({"type": "status", "message": "Connecting to TEE agent pool..."})

        await asyncio.to_thread(self._ensure_initialized)
        _log_ram("stream_analysis after ensure_initialized")

        if self._semaphore.locked():
            waiter = asyncio.Event()
            self._waiting_queues.append(waiter)
            position = len(self._waiting_queues)
            yield _make_sse({
                "type": "queued",
                "message": f"Server busy. You are at position {position} in the queue.",
                "position": position,
            })

            while True:
                try:
                    await asyncio.wait_for(self._semaphore.acquire(), timeout=2.0)
                    self._waiting_queues.remove(waiter)
                    break
                except asyncio.TimeoutError:
                    if waiter in self._waiting_queues:
                        new_pos = self._waiting_queues.index(waiter) + 1
                        if new_pos != position:
                            position = new_pos
                            yield _make_sse({
                                "type": "queued",
                                "message": f"Queue advanced. You are at position {position}.",
                                "position": position,
                            })
                        else:
                            yield _make_sse({"type": "ping"})
        else:
            await self._semaphore.acquire()

        self._active_count += 1
        yield _make_sse({"type": "status", "message": "Agent allocated - starting analysis..."})

        try:
            async for chunk in self._run_agent(address, token, network):
                yield chunk
        except asyncio.TimeoutError:
            yield _make_sse({"type": "error", "message": "Analysis timed out (exceeded 5 minutes)."})
        except Exception as e:
            traceback.print_exc()
            yield _make_sse({"type": "error", "message": f"Agent crashed: {e}"})
        finally:
            self._active_count -= 1
            self._semaphore.release()
            _log_ram("stream_analysis END for address " + address)
            yield _make_sse({"type": "stream_end"})

    async def _run_agent(
        self,
        address: str,
        token: str | None = None,
        network: str | None = None,
    ) -> AsyncGenerator[str, None]:
        notified_steps: set[int] = set()
        prompt = build_prompt(address, token, network)

        async def _log_agent_ram():
            try:
                while True:
                    await asyncio.sleep(10)
                    _log_ram("Agent working")
            except asyncio.CancelledError:
                pass

        logger_task = asyncio.create_task(_log_agent_ram())

        try:
            async with asyncio.timeout(300):
                async for chunk in self._agent.astream({"messages": [("user", prompt)]}):
                    if "agent" in chunk:
                        msg: AIMessage = chunk["agent"]["messages"][0]

                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                tool_name: str = tc["name"]
                                call_id: str = tc["id"]
                                args: dict = tc["args"]

                                if tool_name in STEP_MAP:
                                    step_num, step_title = STEP_MAP[tool_name]
                                    if step_num not in notified_steps:
                                        notified_steps.add(step_num)
                                        yield _make_sse({
                                            "type": "step_start",
                                            "step": step_num,
                                            "title": step_title,
                                        })

                                yield _make_sse({
                                    "type": "tool_call",
                                    "name": tool_name,
                                    "args": args,
                                    "call_id": call_id,
                                })

                        elif msg.content:
                            yield _make_sse(
                                {"type": "step_start", "step": 4, "title": "Final Recommendation"}
                            )
                            yield _make_sse({"type": "complete", "report": msg.content})

                    elif "tools" in chunk:
                        for tm in chunk["tools"]["messages"]:
                            if not isinstance(tm, ToolMessage):
                                continue
                            content = tm.content
                            if len(content) > 800:
                                content = content[:800] + "\n... (truncated)"

                            yield _make_sse({
                                "type": "tool_result",
                                "name": tm.name,
                                "content": content,
                                "call_id": tm.tool_call_id,
                            })
        finally:
            logger_task.cancel()
            try:
                await logger_task
            except asyncio.CancelledError:
                pass


def get_agent_pool() -> AgentPool:
    """Get the AgentPool instance from the service registry."""
    from app.services.registry import get_registry
    return get_registry().agent_pool


async def stream_analysis(
    address: str,
    private_key: str,
    token: str | None = None,
    network: str | None = None,
) -> AsyncGenerator[str, None]:
    """Wrapper that retrieves AgentPool from registry."""
    pool = get_agent_pool()
    async for chunk in pool.stream_analysis(address, token, network):
        yield chunk
