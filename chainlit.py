# import os
# from pydantic import BaseModel
# import chainlit as cl
# from dotenv import load_dotenv

# from agents import (
#     Agent,
#     RunConfig,
#     OpenAIChatCompletionsModel,
#     Runner,
#     AsyncOpenAI,
#     function_tool,
#     input_guardrail,
#     InputGuardrailTripwireTriggered,
#     RunContextWrapper,
#     TResponseInputItem,
#     GuardrailFunctionOutput,
# )

# # Load .env
# load_dotenv()
# gemini_api_key = os.getenv("GEMINI_API_KEY")

# # Async provider & model setup
# provider = AsyncOpenAI(
#     api_key=gemini_api_key,
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
# )

# model = OpenAIChatCompletionsModel(
#     model="gemini-2.0-flash",
#     openai_client=provider,
# )

# config = RunConfig(
#     model=model,
#     model_provider=provider,
#     tracing_disabled=True,
# )


# # Pydantic Output Schema
# class SensitiveInfoOutput(BaseModel):
#     contains_sensitive_info: bool
#     reasoning: str


# # Guardrail Agent
# guardrail_agent = Agent(
#     name="Sensitive info detector",
#     instructions="Check if the user is providing sensitive personal information like passwords, credit card numbers, or phone numbers. If so, set 'contains_sensitive_info' to true and explain why.",
#     output_type=SensitiveInfoOutput,
# )


# # Guardrail Function
# @input_guardrail
# async def sensitive_info_guardrail(
#     ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
# ) -> GuardrailFunctionOutput:
#     result = await Runner.run(guardrail_agent, input, context=ctx.context)
#     return GuardrailFunctionOutput(
#         output_info=result.final_output,
#         tripwire_triggered=result.final_output.contains_sensitive_info,
#     )


# # Tool function
# @function_tool
# def get_weather(city: str) -> str:
#     return f"The weather in {city} is sunny and 30°C."


# # Hand-off agents
# agent_en = Agent(name="English Agent", instructions="Only respond in English.")
# agent_sp = Agent(name="Spanish Agent", instructions="Only respond in Spanish.")

# # Main Gemini Agent
# agent = Agent(
#     name="Gemini Agent",
#     instructions="You are a helpful assistant. If the user is asking about weather, use the get_weather tool. If input is in Spanish, respond in Spanish. If in English, respond in English. If sensitive info is detected, trigger the guardrail.",
#     model=model,
#     handoffs=[agent_en, agent_sp],
#     tools=[get_weather],
#     input_guardrails=[sensitive_info_guardrail],
# )


# @cl.on_chat_start
# async def on_chat_start():
#     await cl.Message(content="Hello, how can I help you today?").send()


# # 💬 Handle messages
# @cl.on_message
# async def handle_message(message: cl.Message):
#     try:
#         result = await Runner.run(agent, input=message.content, run_config=config)
#         await cl.Message(content=result.final_output).send()
#     except InputGuardrailTripwireTriggered:
#         await cl.Message(content="🔒 Sensitive info detected. Action blocked.").send()
