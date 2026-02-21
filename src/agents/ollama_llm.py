import requests

from src.agents.base_llm import BaseLLM


class OllamaLLM(BaseLLM):
    def __init__(self, base_url: str, model_name: str):
        self.model = model_name
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
        )
        return response.json()["response"]
