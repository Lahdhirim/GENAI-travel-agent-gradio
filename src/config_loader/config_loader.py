import json
from pydantic import BaseModel, Field
from typing import Literal


class OpenAIConfig(BaseModel):
    api_key_env: str = Field(
        ..., description="Environment variable name for OpenAI API key"
    )
    model_name: str = Field(..., description="OpenAI model name")
    temperature: float = Field(0.6, description="Temperature for OpenAI responses")


class OllamaConfig(BaseModel):
    base_url: str = Field(..., description="Base URL of Ollama server")
    model_name: str = Field(..., description="Ollama model name")


class OpenRouterConfig(BaseModel):
    api_key_env: str = Field(
        ..., description="Environment variable name for OpenRouter API key"
    )
    base_url: str = Field(..., description="Base URL for Openrouter endpoint")
    model_name: str = Field(..., description="OpenRouter model name")


class Config(BaseModel):
    destinations_filename: str = Field(
        ..., description="Excel file containing destinations details"
    )
    llm_backend: Literal["openai", "ollama", "openrouter"]
    openai_config: OpenAIConfig
    ollama_config: OllamaConfig
    openrouter_config: OpenRouterConfig
    system_prompt: str = Field(
        ..., description="System prompt for the travel assistant"
    )


def config_loader(config_path: str) -> Config:
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return Config(**data)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find config file: {config_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in config file: {config_path}")
