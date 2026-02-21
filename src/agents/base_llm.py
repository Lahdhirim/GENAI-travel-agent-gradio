from abc import ABC, abstractmethod


class LLMResult:
    def __init__(self, message=None, finish_reason=None, tool_calls=None, content=None):
        self.message = message
        self.finish_reason = finish_reason
        self.tool_calls = tool_calls
        self.content = content


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, messages: list, tools=None) -> LLMResult:
        pass
