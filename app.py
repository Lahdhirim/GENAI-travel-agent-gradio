import gradio as gr
import os
from dotenv import load_dotenv, find_dotenv

from src.utils.logger_config import logger
from src.config_loader.config_loader import config_loader
from src.agents.travel_assistant import TravelAssistant
from src.agents.openai_llm import OpenAILLM
from src.agents.openrouter_llm import OpenRouterLLM
from src.utils.app_utils import numpy_to_base64, path_to_base64, make_html

# Set up logging
with open("logs/app.log", "w") as log_file:
    pass
logger.info("Logging setup complete")

# Load API keys from .env file
load_dotenv(find_dotenv(), override=True)
logger.info("Env loaded")

# Load configuration file
config_path = "config/config.json"
config = config_loader(config_path=config_path)
logger.info(f"Configuration loaded from: {config_path}")

# Initialize Agent
backend = config.llm_backend

if backend == "openai":
    logger.info(f"OpenAI {config.openai_config.model_name} LLM is selected")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing.\n"
            "Create a .env file with:\n"
            "OPENAI_API_KEY=sk-xxxx\n"
            "Or export it in your environment."
        )
    logger.info("OPENAI API key loaded")

    llm = OpenAILLM(
        api_key=api_key,
        model_name=config.openai_config.model_name,
        temperature=config.openai_config.temperature,
    )

elif backend == "openrouter":
    logger.info(f"OpenRouter {config.openrouter_config.model_name} LLM is selected")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is missing.\n"
            "Create a .env file with:\n"
            "OPENROUTER_API_KEY=sk-xxxx\n"
            "Or export it in your environment."
        )
    logger.info("OpenRouter API key loaded")

    llm = OpenRouterLLM(
        api_key=api_key,
        model_name=config.openrouter_config.model_name,
        base_url=config.openrouter_config.base_url,
    )

else:
    logger.error(f"Unknown LLM backend: {backend}")
    raise ValueError(f"Unknown LLM backend: {backend}")


# Initialize travel assistant
travel_assistant = TravelAssistant(
    llm=llm,
    system_prompt=config.system_prompt,
    destinations_excel_path=config.destinations_filename,
)
logger.info(f"Travel Agent initialized")

# Gradio Interface
DEFAULT_IMAGE_PATH = "assets/travel_assistant.png"
DEFAULT_B64 = path_to_base64(DEFAULT_IMAGE_PATH)

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=2):
            history = gr.Chatbot(type="messages")
            message = gr.Textbox()

        with gr.Column(scale=1):
            plot_output = gr.HTML(value=make_html(DEFAULT_B64), label="Output Plot")

    def chat_with_plot(message, history, current_b64):
        response, fig = travel_assistant.chat(message, history)

        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response},
        ]

        if fig is not None:
            new_b64 = numpy_to_base64(fig)
        else:
            new_b64 = current_b64

        return history, make_html(new_b64), "", new_b64

    current_b64_state = gr.State(DEFAULT_B64)

    message.submit(
        chat_with_plot,
        inputs=[message, history, current_b64_state],
        outputs=[history, plot_output, message, current_b64_state],
    )

demo.launch(inbrowser=True)
