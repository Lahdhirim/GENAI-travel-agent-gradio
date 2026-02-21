import os
from openai import OpenAI
from src.agents.base_llm import BaseLLM


class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model_name: str, temperature: float):
        self.client = OpenAI(api_key=api_key)
        self.model = model_name
        self.temperature = temperature

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        return response.choices[0].message.content
