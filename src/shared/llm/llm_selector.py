from langchain.agents.middleware.types import ModelRequest
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import wrap_model_call, ModelResponse

default_llm = init_chat_model(
    "openai:gpt-5.2",
    model_kwargs={"parallel_tool_calls": False},
)


@wrap_model_call
async def dynamic_model_selector(request: ModelRequest, handler) -> ModelResponse:
    """
    Dynamic model selector based on the request.
    Converts the preferred_llm string from context into an actual model object.
    """
    preferred_llm = request.runtime.context.preferred_llm
    
    # Convert the model string (e.g., "openai:gpt-4o-mini") to an actual model object
    request.model = init_chat_model(
        preferred_llm,
        model_kwargs={"parallel_tool_calls": False},
    )

    return await handler(request)