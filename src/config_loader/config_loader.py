import json
from pydantic import BaseModel, Field
from typing import Literal, Optional


class OpenAIConfig(BaseModel):
    model_name: str = Field(..., description="OpenAI model name")
    temperature: Optional[float] = Field(
        default=0.0, description="Temperature for OpenAI model responses"
    )


class OpenRouterConfig(BaseModel):
    base_url: str = Field(..., description="Base URL for Openrouter endpoint")
    model_name: str = Field(..., description="OpenRouter model name")
    temperature: Optional[float] = Field(
        default=0.0, description="Temperature for Openrouter model responses"
    )


class Config(BaseModel):
    destinations_filename: str = Field(
        ..., description="Excel file containing destinations details"
    )
    llm_backend: Literal["openai", "openrouter"] = Field(
        ..., description="LLM provider choice"
    )
    openai_config: OpenAIConfig
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
