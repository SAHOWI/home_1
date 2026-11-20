"""Google Gemini LLM provider adapter using the google-genai SDK."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from home_1.llm.base import LLMError, LLMResponse, Message, Role, ToolCall, ToolDefinition


class GeminiProvider:
    """Adapter for Google Gemini models via `google-genai`."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        if not api_key:
            raise LLMError(
                "GEMINI_API_KEY is not set. Add it to your .env file or environment variables."
            )
        try:
            from google import genai
        except ImportError as exc:
            raise LLMError("google-genai is not installed. Run `uv sync` first.") from exc

        self._client = genai.Client(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model(self) -> str:
        return self._model

    def generate(
        self,
        messages: Sequence[Message],
        *,
        system_prompt: str = "",
        tools: Sequence[ToolDefinition] = (),
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        from google.genai import types

        contents = _to_gemini_contents(messages, types)
        gemini_tools = _to_gemini_tools(tools, types) if tools else None

        config = types.GenerateContentConfig(
            system_instruction=system_prompt or None,
            temperature=temperature,
            max_output_tokens=max_tokens,
            tools=gemini_tools,
        )

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            raise LLMError(f"Gemini request failed: {exc}") from exc

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        candidates = getattr(response, "candidates", None) or []
        if candidates and getattr(candidates[0], "content", None):
            parts = getattr(candidates[0].content, "parts", None) or []
            for idx, part in enumerate(parts, start=1):
                if getattr(part, "text", None):
                    text_parts.append(part.text)
                fc = getattr(part, "function_call", None)
                if fc is not None:
                    args = dict(fc.args) if fc.args else {}
                    tool_calls.append(
                        ToolCall(
                            id=getattr(fc, "id", None) or f"gemini_call_{idx}",
                            name=fc.name,
                            arguments=args,
                        )
                    )

        return LLMResponse(
            content="\n".join(text_parts).strip(),
            tool_calls=tuple(tool_calls),
            provider=self.name,
            model=self.model,
        )


def _to_gemini_tools(tools: Sequence[ToolDefinition], types: Any) -> list[Any]:
    declarations = [
        types.FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters_json_schema=tool.parameters,
        )
        for tool in tools
    ]
    return [types.Tool(function_declarations=declarations)]


def _to_gemini_contents(messages: Sequence[Message], types: Any) -> list[Any]:
    contents: list[Any] = []
    pending_tool_parts: list[Any] = []

    def flush_tool_parts() -> None:
        if pending_tool_parts:
            contents.append(types.Content(role="user", parts=list(pending_tool_parts)))
            pending_tool_parts.clear()

    for msg in messages:
        if msg.role == Role.TOOL:
            pending_tool_parts.append(
                types.Part.from_function_response(
                    name=msg.tool_name or "unknown_tool",
                    response={"result": msg.content},
                )
            )
            continue

        flush_tool_parts()

        if msg.role == Role.USER:
            contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=msg.content)])
            )
        elif msg.role == Role.ASSISTANT:
            parts: list[Any] = []
            if msg.content:
                parts.append(types.Part.from_text(text=msg.content))
            for tc in msg.tool_calls:
                parts.append(types.Part.from_function_call(name=tc.name, args=tc.arguments))
            if parts:
                contents.append(types.Content(role="model", parts=parts))

    flush_tool_parts()
    return contents
