"""
Monkey-patch OpenGradientChatModel to add a native `_agenerate` method.

This prevents LangChain from falling back to run_in_executor(_generate) ->
asyncio.run() which causes httpx/anyio Event objects to bind to the wrong
event loop. By providing a real _agenerate, we call self._llm.chat() directly
in the current event loop.

This module applies patches on import -- import it once early in the app lifecycle.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from langchain_core.callbacks.manager import AsyncCallbackManagerForLLMRun
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from opengradient.client.llm import LLM, X402_PLACEHOLDER_API_KEY
from opengradient.agents.og_langchain import (
    OpenGradientChatModel,
    _extract_content,
    _parse_tool_call,
)


def _patched_headers(self, settlement_mode):
    mode_str = settlement_mode.value if hasattr(settlement_mode, "value") else settlement_mode
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {X402_PLACEHOLDER_API_KEY}",
        "X-SETTLEMENT-TYPE": mode_str,
    }


async def _async_generate(
    self,
    messages: List[Any],
    stop: Optional[List[str]] = None,
    run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
    **kwargs: Any,
) -> ChatResult:
    sdk_messages: List[Dict[str, Any]] = []
    for message in messages:
        if isinstance(message, SystemMessage):
            sdk_messages.append({"role": "system", "content": _extract_content(message.content)})
        elif isinstance(message, HumanMessage):
            sdk_messages.append({"role": "user", "content": _extract_content(message.content)})
        elif isinstance(message, AIMessage):
            msg: Dict[str, Any] = {"role": "assistant", "content": _extract_content(message.content)}
            if message.tool_calls:
                msg["tool_calls"] = [
                    {
                        "id": call["id"],
                        "type": "function",
                        "function": {"name": call["name"], "arguments": json.dumps(call["args"])},
                    }
                    for call in message.tool_calls
                ]
            sdk_messages.append(msg)
        elif isinstance(message, ToolMessage):
            sdk_messages.append(
                {
                    "role": "tool",
                    "content": _extract_content(message.content),
                    "tool_call_id": message.tool_call_id,
                }
            )
        else:
            raise ValueError(f"Unexpected message type: {message}")

    chat_output = await self._llm.chat(
        model=self.model_cid,
        messages=sdk_messages,
        stop_sequence=stop,
        max_tokens=self.max_tokens,
        tools=self._tools,
        x402_settlement_mode=self.x402_settlement_mode,
    )

    finish_reason = chat_output.finish_reason or ""
    chat_response = chat_output.chat_output or {}

    if chat_response.get("tool_calls"):
        tool_calls = [_parse_tool_call(tc) for tc in chat_response["tool_calls"]]
        ai_message = AIMessage(content="", tool_calls=tool_calls)
    else:
        ai_message = AIMessage(content=_extract_content(chat_response.get("content", "")))

    return ChatResult(
        generations=[ChatGeneration(message=ai_message, generation_info={"finish_reason": finish_reason})]
    )


# Apply patches on import
LLM._headers = _patched_headers
OpenGradientChatModel._agenerate = _async_generate  # type: ignore[assignment]
