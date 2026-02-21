from openai import OpenAI

from src.agents.base_llm import BaseLLM, LLMResult


class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model_name: str, temperature: float):
        self.client = OpenAI(api_key=api_key)
        self.model = model_name
        self.temperature = temperature

    def generate(self, messages: list, tools: None) -> LLMResult:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            tools=tools,
        )

        choice = response.choices[0]
        msg = choice.message

        return LLMResult(
            message=msg,
            finish_reason=choice.finish_reason,
            tool_calls=getattr(msg, "tool_calls", None),
            content=msg.content,
        )
