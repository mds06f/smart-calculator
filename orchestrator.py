"""Central orchestrator: a LangGraph StateGraph that splits a user request
into tasks for the specialist agents in agent.py, dispatches them all
concurrently, and combines their results into one final reply.
"""

import json
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from agent import build_agents, get_model

ROUTER_PROMPT = """You split a user request into tasks for three specialist agents:
- "home": lists/controls smart switches (lights, fans)
- "calculator": does arithmetic
- "system": reports the current date/time or system info

Reply with ONLY a JSON list of tasks, as {{"agent": "home"|"calculator"|"system",
"task": "..."}}. Each task's instruction must be self-contained, resolving
any "it"/"that" from the conversation below. If no task applies, reply
with [].

Conversation so far:
{history}

User request: {request}"""


class Task(TypedDict):
    agent: str
    task: str


class Result(TypedDict):
    agent: str
    task: str
    result: str


class State(TypedDict, total=False):
    request: str
    history: list
    tasks: list[Task]
    results: Annotated[list[Result], operator.add]
    task: Task
    final: str


def _parse_tasks(reply: str) -> list:
    reply = reply.strip()
    if reply.startswith("```"):
        reply = reply.strip("`").removeprefix("json").strip()
    try:
        tasks = json.loads(reply)
    except ValueError:
        return []
    return tasks if isinstance(tasks, list) else []


def build_graph(api_key: str):
    agents = build_agents(api_key)
    router_model = get_model(api_key)

    def router(state: State) -> dict:
        history = "\n".join(f"{m['role']}: {m['content']}" for m in state.get("history", [])) or "(none)"
        prompt = ROUTER_PROMPT.format(history=history, request=state["request"])
        reply = router_model.invoke(prompt).content
        return {"tasks": _parse_tasks(reply), "results": []}

    def dispatch(state: State):
        if not state["tasks"]:
            return "aggregate"
        return [Send("run_specialist", {"task": task}) for task in state["tasks"]]

    def run_specialist(state: State) -> dict:
        task = state["task"]
        agent = agents.get(task["agent"])
        if agent is None:
            return {"results": [{**task, "result": f"Unknown agent '{task['agent']}'."}]}
        reply = agent.invoke({"messages": [{"role": "user", "content": task["task"]}]})
        return {"results": [{**task, "result": reply["messages"][-1].content}]}

    def aggregate(state: State) -> dict:
        results = state["results"]
        if not results:
            return {"final": "Invalid operation/expression"}
        if len(results) == 1:
            return {"final": results[0]["result"]}
        combined = "\n".join(f"- {r['result']}" for r in results)
        reply = router_model.invoke(f"Combine these results into one short reply for the user:\n{combined}")
        return {"final": reply.content}

    graph = StateGraph(State)
    graph.add_node("router", router)
    graph.add_node("run_specialist", run_specialist)
    graph.add_node("aggregate", aggregate)

    graph.add_edge(START, "router")
    graph.add_conditional_edges("router", dispatch)
    graph.add_edge("run_specialist", "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()


def run(request: str, history: list, api_key: str) -> str:
    graph = build_graph(api_key)
    result = graph.invoke({"request": request, "history": history})
    return result["final"]
