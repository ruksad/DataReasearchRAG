import sys
import json
from app.graph import graph


def run(question: str) -> None:
    print(f"\nQuestion: {question}\n{'─' * 60}")

    result = graph.invoke({"question": question, "attempts": 0, "rows": [], "error": ""})

    print(f"SQL:\n{result.get('sql', 'N/A')}\n")
    rows = result.get("rows", [])
    print(f"Rows returned: {len(rows)}")
    if rows:
        print(json.dumps(rows[:5], indent=2, default=str))
    print(f"\nAnswer:\n{result.get('answer', 'N/A')}")


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What are the top 5 stores by total sales?"
    run(question)
