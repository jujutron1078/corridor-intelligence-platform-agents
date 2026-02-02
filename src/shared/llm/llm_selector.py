from langchain.agents.middleware.types import ModelRequest
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import wrap_model_call, ModelResponse

default_llm = init_chat_model(
    "openai:gpt-5.2",
)


@wrap_model_call
async def dynamic_model_selector(request: ModelRequest, handler) -> ModelResponse:
    """
    Dynamic model selector based on the request.
    Converts the preferred_llm string from context into an actual model object.
    Format: 'provider:model' — e.g. openai:gpt-5.2, google_genai:gemini-2.0-flash-exp.
    Temperature is taken from context.llm_temperature (default 0.0).
    Google Gemini: set GOOGLE_API_KEY. Use gemini-2.0-flash-thinking-exp for reasoning-heavy tasks.
    """
    context = request.runtime.context
    preferred_llm = context.preferred_llm
    llm_temperature = context.llm_temperature

    request.model = init_chat_model(preferred_llm, temperature=llm_temperature)
    return await handler(request)