import sys
import uuid
import json
from app.graph import graph


def _new_session() -> str:
    return str(uuid.uuid4())


def _print_citation(citation: dict) -> None:
    if not citation:
        return
    cols = ", ".join(citation.get("columns", []))
    sql_oneline = " ".join(citation.get("sql", "").split())
    print(f"\n{'─' * 2} Citation {'─' * 49}")
    print(f"Source   : {citation.get('source', '')}")
    print(f"Executed : {citation.get('executed_at', '')}")
    print(f"Rows     : {citation.get('row_count', 0)}  |  Columns: {cols}")
    print(f"SQL      : {sql_oneline}")
    print(f"{'─' * 60}")


def run(question: str, history: list[dict] | None = None, session_id: str | None = None) -> dict:
    """Run one turn and return the full result state."""
    print(f"\nQuestion: {question}\n{'─' * 60}")

    result = graph.invoke({
        "question": question,
        "attempts": 0,
        "rows": [],
        "error": "",
        "history": history or [],
        "session_id": session_id or _new_session(),
    })

    print(f"SQL:\n{result.get('sql', 'N/A')}\n")
    rows = result.get("rows", [])
    print(f"Rows returned: {len(rows)}")
    if rows:
        print(json.dumps(rows[:5], indent=2, default=str))
    print(f"\nAnswer:\n{result.get('answer', 'N/A')}")
    _print_citation(result.get("citation") or {})

    return result


def chat() -> None:
    """Interactive multi-turn session — history and session_id are carried across questions."""
    session_id = _new_session()
    print("DataResearchRAG — conversational analytics")
    print(f"Session: {session_id}")
    print("Type your question and press Enter. Type 'exit' or Ctrl-C to quit.\n")

    history: list[dict] = []
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break

        result = run(question, history=history, session_id=session_id)
        history = result.get("history") or history


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run(" ".join(sys.argv[1:]))
    else:
        chat()
