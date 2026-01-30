from langchain.agents import create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    TodoListMiddleware,
    SummarizationMiddleware,
)
from langgraph.checkpoint.memory import InMemorySaver

from src.agents.grant_writer.context.context import Context
from src.agents.grant_writer.middleware.inject_context import inject_context
from src.agents.grant_writer.prompts.prompt import agent_prompt
from src.agents.grant_writer.tools.read_company_info import read_company_info
from src.agents.grant_writer.tools.write_document.tool import write_document
from src.shared.llm.llm_selector import default_llm, dynamic_model_selector
from src.agents.grant_writer.tools.think_tool.tool import think_tool
from src.agents.grant_writer.tools.read_file.tool import read_file
from src.agents.grant_writer.tools.delete_file.tool import delete_file
from src.agents.grant_writer.tools.edit_document.tool import edit_file
from src.agents.grant_writer.state.state import GrantWriterState

agent = create_agent(
    model=default_llm,
    tools=[
        think_tool,
        write_document,
        read_company_info,
        read_file,
        delete_file,
        edit_file,
    ],
    context_schema=Context,
    state_schema=GrantWriterState,
    middleware=[
        inject_context,
        agent_prompt,
        dynamic_model_selector,
        TodoListMiddleware(),
        SummarizationMiddleware(
            model="openai:gpt-5.2",
            max_tokens_before_summary=40000,
            messages_to_keep=10,
        ),
    ],
)
