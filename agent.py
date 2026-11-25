"""Three specialist LangChain agents, each scoped to one group of tools.
The orchestrator decides which of these to call and with what task.
"""

from langchain.agents import create_agent
from langchain_groq import ChatGroq

from tools import calculate, change_switch, get_current_time, get_switches, get_system_info

MODEL = "openai/gpt-oss-20b"

# Appended to every specialist's prompt as a safety net, in case the
# orchestrator's router ever misroutes a non-task message to an agent.
NO_CHITCHAT_GUARD = """You never make normal conversation. Do not greet
back, chat, answer questions about yourself (name, model, who made you,
how you are), tell jokes, or give opinions. If the task doesn't call for
one of your tools, reply with exactly: Invalid operation/expression"""

HOME_PROMPT = f"""You manage smart home switches with get_switches and
change_switch. Always use a tool instead of answering from memory.

{NO_CHITCHAT_GUARD}"""

CALCULATOR_PROMPT = f"""You do arithmetic with the calculate tool.
Break a multi-operation expression (e.g. "9+50-12") into one calculate call
per operation, following BODMAS/order of operations (^ before * and /,
before + and -). Never ask which operation to do first.

{NO_CHITCHAT_GUARD}"""

SYSTEM_INFO_PROMPT = f"""You report the current date/time and system info
using get_current_time and get_system_info. Always use a tool instead of
answering from memory.

{NO_CHITCHAT_GUARD}"""


def get_model(api_key: str) -> ChatGroq:
    return ChatGroq(model=MODEL, api_key=api_key, temperature=0)


def build_agents(api_key: str) -> dict:
    model = get_model(api_key)
    return {
        "home": create_agent(model, tools=[get_switches, change_switch], system_prompt=HOME_PROMPT),
        "calculator": create_agent(model, tools=[calculate], system_prompt=CALCULATOR_PROMPT),
        "system": create_agent(model, tools=[get_current_time, get_system_info], system_prompt=SYSTEM_INFO_PROMPT),
    }
