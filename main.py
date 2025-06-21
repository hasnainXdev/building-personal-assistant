from agents import (
    Agent,
    RunConfig,
    OpenAIChatCompletionsModel,
    Runner,
    AsyncOpenAI,
    function_tool,
    input_guardrail,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    TResponseInputItem,
    GuardrailFunctionOutput,
)
from pydantic import BaseModel
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


class SensitiveInfoOutput(BaseModel):
    contains_sensitive_info: bool
    reasoning: str


# 🔒 Guardrail agent that analyzes input and decides if it’s sensitive
guardrail_agent = Agent(
    name="Sensitive info detector",
    instructions="Check if the user is providing sensitive personal information like passwords, credit card numbers, or phone numbers. If so, set 'contains_sensitive_info' to true and explain why.",
    output_type=SensitiveInfoOutput,
)


# 🛡️ Guardrail function to trigger if sensitive info is found
@input_guardrail
async def sensitive_info_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.contains_sensitive_info,
    )


# 🛠️ Basic Function tool to get weather information
@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny and 30°C."


agent_en = Agent(
    name="English Agent",
    instructions="only respond in English",
)

agent_sp = Agent(
    name="Spanish Agent",
    instructions="only respond in Spanish",
)

agent = Agent(
    name="Gemini Agent",
    instructions=(
        "You are an helpful assistant. check if the user is asking for weather information, use the get_weather tool to answer, and if user ask in spanish, respond in Spanish. or if user ask in English, respond in English. if user provides sensitive information like passwords, credit card numbers, or phone numbers, trigger the sensitive_info_guardrail."
    ),
    model=model,
    handoffs=[agent_en, agent_sp],
    tools=[get_weather],
    input_guardrails=[sensitive_info_guardrail],
)


def main():
    try:
        result = Runner.run_sync(agent, run_config=config, input="hola")
        print(result.final_output)
        print(
            "Guardrail didn't trip - Output Accepted"
        )  # this line is for just debugging.
    except InputGuardrailTripwireTriggered:
        print("🔒 Sensitive info guardrail tripped, Output Rejected")


main()
# Note: Make sure to set the GEMINI_API_KEY environment variable before running this script.
