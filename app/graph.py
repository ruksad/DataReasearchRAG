from langgraph.graph import StateGraph, END
from app.graph_state import AgentState
from app.nodes.generate_sql import generate_sql
from app.nodes.validate_sql import validate_sql
from app.nodes.execute import execute
from app.nodes.synthesize import synthesize
from app import config


def _route_after_execute(state: AgentState) -> str:
    """Retry SQL generation on error, up to MAX_REPAIR_ATTEMPTS total."""
    if state.get("error") and state.get("attempts", 0) < config.MAX_REPAIR_ATTEMPTS:
        return "generate_sql"
    return "synthesize"


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("generate_sql", generate_sql)
    builder.add_node("validate_sql", validate_sql)
    builder.add_node("execute", execute)
    builder.add_node("synthesize", synthesize)

    builder.set_entry_point("generate_sql")
    builder.add_edge("generate_sql", "validate_sql")
    builder.add_edge("validate_sql", "execute")
    builder.add_conditional_edges("execute", _route_after_execute, {
        "generate_sql": "generate_sql",
        "synthesize": "synthesize",
    })
    builder.add_edge("synthesize", END)

    return builder.compile()


graph = build_graph()
