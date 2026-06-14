from langchain_core.messages import SystemMessage, HumanMessage
from app.llm import get_llm
from app.schema import SCHEMA_CONTEXT
from app.graph_state import AgentState

_SYSTEM = f"""You are a SQL expert for MS SQL Server. Generate a single valid T-SQL SELECT query.

Schema:
{SCHEMA_CONTEXT}

Rules:
- Return ONLY the raw SQL — no markdown, no code fences, no explanation.
- Use only SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, ALTER, EXEC, MERGE, or TRUNCATE.
- Always filter Open=1 when aggregating Sales to exclude closed-day zeros.
- Use TOP 100 when retrieving row samples; omit TOP for aggregations.
- All string literals use single quotes."""

_llm = get_llm()


def generate_sql(state: AgentState) -> dict:
    if state.get("error") and state.get("attempts", 0) > 0:
        user_content = (
            f"Question: {state['question']}\n\n"
            f"Previous SQL that failed:\n{state['sql']}\n\n"
            f"Error returned by the database:\n{state['error']}\n\n"
            "Fix the SQL so it runs correctly. Return only the corrected SQL."
        )
    else:
        user_content = f"Question: {state['question']}"

    messages = [SystemMessage(content=_SYSTEM), HumanMessage(content=user_content)]
    response = _llm.invoke(messages)
    sql = response.content.strip().strip("```sql").strip("```").strip()

    return {
        "sql": sql,
        "error": "",
        "attempts": state.get("attempts", 0) + 1,
    }
