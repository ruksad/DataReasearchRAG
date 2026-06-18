import re
from vanna.chromadb import ChromaDB_VectorStore
from app import config

_CHROMA_PATH = "chroma_db"
_vanna_instance = None

# Matches a SELECT/WITH/CREATE statement that spans to end-of-string (no semicolon required)
_SQL_RE = re.compile(
    r"(?:```(?:sql)?\s*)?"           # optional opening fence
    r"((?:SELECT|WITH|CREATE\s+TABLE)\b.*?)"  # the SQL
    r"(?:;?\s*```|;?\s*$)",          # optional closing fence or end-of-string
    re.IGNORECASE | re.DOTALL,
)


def _extract_sql(llm_response: str) -> str:
    """
    Robust SQL extractor that handles:
    - SQL with or without a trailing semicolon
    - Markdown code fences (```sql ... ```)
    - T-SQL bracket notation like [Open] and [Date]
    Falls back to returning the raw response if no pattern matches.
    """
    match = _SQL_RE.search(llm_response)
    if match:
        return match.group(1).strip().rstrip(";").strip()
    return llm_response.strip()


def _make_vanna():
    provider = config.LLM_PROVIDER.lower()

    if provider == "ollama":
        from vanna.ollama import Ollama

        class VannaOllama(ChromaDB_VectorStore, Ollama):
            def __init__(self):
                ChromaDB_VectorStore.__init__(self, config={"path": _CHROMA_PATH})
                Ollama.__init__(self, config={
                    "ollama_host": config.OLLAMA_BASE_URL,
                    "model": config.OLLAMA_MODEL,
                })

            def extract_sql(self, llm_response: str) -> str:
                return _extract_sql(llm_response)

        return VannaOllama()

    if provider == "anthropic":
        from vanna.anthropic import Anthropic_Chat

        class VannaAnthropic(ChromaDB_VectorStore, Anthropic_Chat):
            def __init__(self):
                ChromaDB_VectorStore.__init__(self, config={"path": _CHROMA_PATH})
                Anthropic_Chat.__init__(self, config={
                    "api_key": config.ANTHROPIC_API_KEY,
                    "model": config.ANTHROPIC_MODEL,
                })

            def extract_sql(self, llm_response: str) -> str:
                return _extract_sql(llm_response)

        return VannaAnthropic()

    if provider == "openai":
        from vanna.openai import OpenAI_Chat

        class VannaOpenAI(ChromaDB_VectorStore, OpenAI_Chat):
            def __init__(self):
                ChromaDB_VectorStore.__init__(self, config={"path": _CHROMA_PATH})
                OpenAI_Chat.__init__(self, config={
                    "api_key": config.OPENAI_API_KEY,
                    "model": config.OPENAI_MODEL,
                })

            def extract_sql(self, llm_response: str) -> str:
                return _extract_sql(llm_response)

        return VannaOpenAI()

    raise ValueError(
        f"Unknown LLM_PROVIDER '{config.LLM_PROVIDER}'. "
        "Choose from: ollama, anthropic, openai"
    )


def get_vanna():
    """Return the shared Vanna instance (initialised once per process)."""
    global _vanna_instance
    if _vanna_instance is None:
        _vanna_instance = _make_vanna()
    return _vanna_instance
