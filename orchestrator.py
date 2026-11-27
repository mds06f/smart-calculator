"""Central orchestrator: a LangGraph StateGraph that splits a user request
into tasks for the specialist agents in agent.py. Independent tasks are
dispatched concurrently; tasks flagged as depending on another task's
result run afterward, with that result given to them as context. Results
are then combined into one final reply.
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

Only create a task when the request genuinely needs one of those three
things done. Greetings, small talk, opinions, jokes, general knowledge
questions, and questions about you (your name, model, who made you, how
you work) are NOT tasks, even if a word like "system" or "time" appears
in them in passing — reply with [] for those.

Reply with ONLY a JSON list of tasks, as {{"agent": "home"|"calculator"|"system",
"task": "...", "depends": true|false}}. Set "depends" to true only when the
task needs the result of another task in this same list (e.g. multiplying
by a switch count that another task looks up); otherwise false. Each task's
instruction must be self-contained, resolving any "it"/"that" from the
conversation below. If no task applies, reply with [].

Conversation so far:
{history}

User request: {request}"""


class Task(TypedDict):
    agent: str
    task: str
    depends: bool


class Result(TypedDict):
    agent: str
    task: str
    result: str


class State(TypedDict, total=False):
    request: str
    history: list
    independent: list[Task]
    dependent: list[Task]
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

    def invoke_specialist(task: Task, context: str = "") -> dict:
        agent = agents.get(task["agent"])
        if agent is None:
            return {**task, "result": f"Unknown agent '{task['agent']}'."}
        messages = []
        if context:
            messages.append({"role": "user", "content": f"Earlier results:\n{context}"})
        messages.append({"role": "user", "content": task["task"]})
        reply = agent.invoke({"messages": messages})
        return {**task, "result": reply["messages"][-1].content}

    def router(state: State) -> dict:
        history = "\n".join(f"{m['role']}: {m['content']}" for m in state.get("history", [])) or "(none)"
        prompt = ROUTER_PROMPT.format(history=history, request=state["request"])
        tasks = _parse_tasks(router_model.invoke(prompt).content)
        return {
            "independent": [t for t in tasks if not t.get("depends")],
            "dependent": [t for t in tasks if t.get("depends")],
            "results": [],
        }

    def dispatch_dependent(state: State):
        if state["dependent"]:
            return [Send("run_dependent", {"task": task, "results": state["results"]}) for task in state["dependent"]]
        return "aggregate"

    def dispatch_independent(state: State):
        if state["independent"]:
            return [Send("run_specialist", {"task": task}) for task in state["independent"]]
        return dispatch_dependent(state)

    def run_specialist(state: State) -> dict:
        return {"results": [invoke_specialist(state["task"])]}

    def run_dependent(state: State) -> dict:
        context = "\n".join(f"- {r['result']}" for r in state["results"])
        return {"results": [invoke_specialist(state["task"], context)]}

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
    graph.add_node("run_dependent", run_dependent)
    graph.add_node("aggregate", aggregate)

    graph.add_edge(START, "router")
    graph.add_conditional_edges("router", dispatch_independent)
    graph.add_conditional_edges("run_specialist", dispatch_dependent)
    graph.add_edge("run_dependent", "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()


def run(request: str, history: list, api_key: str) -> str:
    graph = build_graph(api_key)
    result = graph.invoke({"request": request, "history": history})
    return result["final"]
