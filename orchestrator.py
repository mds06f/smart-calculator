"""Central orchestrator: a LangGraph StateGraph that splits a user request
into tasks for the specialist agents in agent.py, runs independent tasks in
parallel and dependent ones in sequential stages, then combines their
results into one final reply.
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

Reply with ONLY a JSON list of stages. Each stage is a list of tasks that can
run in parallel, as {{"agent": "home"|"calculator"|"system", "task": "..."}}.
Each task's instruction must be self-contained, resolving any "it"/"that"
from the conversation below. Put a task in a later stage only if it needs
the result of an earlier stage. If no task applies, reply with [].

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
    history: str
    plan: list
    stage: int
    results: Annotated[list, operator.add]
    task: Task
    final: str


def _format_history(history: list) -> str:
    return "\n".join(f"{m['role']}: {m['content']}" for m in history) or "(none)"


def _parse_plan(reply: str) -> list:
    reply = reply.strip()
    if reply.startswith("```"):
        reply = reply.strip("`").removeprefix("json").strip()
    try:
        plan = json.loads(reply)
    except ValueError:
        return []
    return plan if isinstance(plan, list) else []


def build_graph(api_key: str):
    agents = build_agents(api_key)
    router_model = get_model(api_key)

    def router(state: State) -> dict:
        prompt = ROUTER_PROMPT.format(
            history=_format_history(state.get("history", [])),
            request=state["request"],
        )
        reply = router_model.invoke(prompt).content
        return {"plan": _parse_plan(reply), "stage": 0, "results": []}

    def route_stage(state: State):
        plan = state["plan"]
        stage = state["stage"]
        if stage >= len(plan):
            return "aggregate"
        return [
            Send("run_specialist", {"task": task, "results": state["results"]})
            for task in plan[stage]
        ]

    def run_specialist(state: State) -> dict:
        task = state["task"]
        agent = agents.get(task["agent"])
        if agent is None:
            return {"results": [{**task, "result": f"Unknown agent '{task['agent']}'."}]}
        messages = []
        if state["results"]:
            context = "\n".join(f"- {r['result']}" for r in state["results"])
            messages.append({"role": "user", "content": f"Earlier results:\n{context}"})
        messages.append({"role": "user", "content": task["task"]})
        reply = agent.invoke({"messages": messages})
        return {"results": [{**task, "result": reply["messages"][-1].content}]}

    def advance(state: State) -> dict:
        return {"stage": state["stage"] + 1}

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
    graph.add_node("advance", advance)
    graph.add_node("aggregate", aggregate)

    graph.add_edge(START, "router")
    graph.add_conditional_edges("router", route_stage)
    graph.add_edge("run_specialist", "advance")
    graph.add_conditional_edges("advance", route_stage)
    graph.add_edge("aggregate", END)

    return graph.compile()


def run(request: str, history: list, api_key: str) -> str:
    graph = build_graph(api_key)
    result = graph.invoke({"request": request, "history": history})
    return result["final"]
