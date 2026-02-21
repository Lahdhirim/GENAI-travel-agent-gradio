import requests

from src.agents.base_llm import BaseLLM


class OllamaLLM(BaseLLM):
    def __init__(self, base_url: str, model_name: str):
        self.model = model_name
        self.base_url = base_url

    def generate(self, messages: list) -> str:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model, "messages": messages, "stream": False},
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
