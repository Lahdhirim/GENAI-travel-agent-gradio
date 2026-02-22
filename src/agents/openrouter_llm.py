import requests
from types import SimpleNamespace

from src.agents.base_llm import BaseLLM, LLMResult


class OpenRouterLLM(BaseLLM):
    def __init__(self, api_key: str, model_name: str, base_url: str):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url

    @staticmethod
    def _normalize_tool_calls(msg):
        tool_calls = msg.get("tool_calls") or []
        normalized_tool_calls = []

        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name")
            arguments = fn.get("arguments", "{}")

            function = SimpleNamespace(
                name=name,
                arguments=arguments,
            )

            normalized_tc = SimpleNamespace(
                id=tc.get("id"),
                function=function,
            )

            normalized_tool_calls.append(normalized_tc)

        return normalized_tool_calls

    def generate(self, messages: list, tools=None) -> LLMResult:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {"model": self.model_name, "messages": messages, "tools": tools}

        response = requests.post(
            self.base_url, headers=headers, json=payload, timeout=60
        )
        response.raise_for_status()

        choice = response.json()["choices"][0]
        msg = choice["message"]

        return LLMResult(
            message=msg,
            finish_reason=choice.get("finish_reason"),
            tool_calls=self._normalize_tool_calls(msg),
            content=msg.get("content"),
        )
