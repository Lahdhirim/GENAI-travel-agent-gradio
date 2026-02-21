from abc import ABC, abstractmethod


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, messages: list) -> str:
        pass
