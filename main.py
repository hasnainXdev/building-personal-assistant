from agents import (
    Agent,
    RunConfig,
    OpenAIChatCompletionsModel,
    Runner,
)
from openai import AsyncOpenAI 
from dotenv import load_dotenv
import os

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

provider = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider,
)

config = RunConfig(
    model=model,
    model_provider=provider,
    tracing_disabled=True,
)

agent = Agent(
    name="Gemini Agent",
    instructions=(
        "you're a helpful assistant,"
    ),
)


result = Runner.run_sync(
    agent, run_config=config, input="helow, how are you?"
)

print(result.final_output)
