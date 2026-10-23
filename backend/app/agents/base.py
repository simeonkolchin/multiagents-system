import json
from typing import Any

from app.config import Settings
from app.llm.client import LLMClient
from app.llm.tools import TOOL_SCHEMAS, ToolContext


def _extract_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no json object in response")
    return json.loads(text[start : end + 1])


class Agent:
    def __init__(
        self,
        client: LLMClient,
        settings: Settings,
        system_prompt: str,
        use_tools: bool = True,
    ) -> None:
        self._client = client
        self._settings = settings
        self._system_prompt = system_prompt
        self._use_tools = use_tools

    async def run(
        self, payload: dict[str, Any], context: ToolContext | None = None
    ) -> dict[str, Any]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]
        use_tools = (
            self._use_tools and self._settings.agent_use_tools and context is not None
        )
        tools = TOOL_SCHEMAS if use_tools else None
        response_format = None if use_tools else {"type": "json_object"}

        for _ in range(self._settings.agent_max_tool_turns):
            result = await self._client.chat(
                messages, tools=tools, response_format=response_format
            )
            if result.tool_calls and context is not None:
                messages.append(self._assistant_message(result))
                for call in result.tool_calls:
                    output = context.dispatch(call.name, call.arguments)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": json.dumps(output, ensure_ascii=False),
                        }
                    )
                continue
            try:
                return _extract_json(result.content)
            except (ValueError, json.JSONDecodeError):
                return await self._force_json(messages)
        return await self._force_json(messages)

    async def _force_json(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        forcing = messages + [
            {
                "role": "user",
                "content": "Верни только итоговый валидный JSON по требуемой схеме.",
            }
        ]
        result = await self._client.chat(
            forcing, response_format={"type": "json_object"}
        )
        return _extract_json(result.content)

    def _assistant_message(self, result: Any) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": result.content or None,
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments, ensure_ascii=False),
                    },
                }
                for call in result.tool_calls
            ],
        }
