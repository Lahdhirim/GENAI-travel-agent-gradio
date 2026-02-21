import requests


class OpenRouterLLM:
    def __init__(self, api_key: str, model_name: str, base_url: str):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
        }

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
        }

        response = requests.post(
            self.base_url, headers=headers, json=payload, timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
