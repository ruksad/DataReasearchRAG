import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.home() / ".env")

# ── LLM provider selection ────────────────────────────────────────────────────
# Set LLM_PROVIDER to one of: "ollama" | "anthropic" | "openai"
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")

# Ollama (default)
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma4:latest")

# Anthropic / Claude
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# OpenAI
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

# ── MS SQL Server ─────────────────────────────────────────────────────────────
MSSQL_HOST: str = os.getenv("MSSQL_HOST", "localhost")
MSSQL_PORT: int = int(os.getenv("MSSQL_PORT", "1433"))
MSSQL_USER: str = os.getenv("MSSQL_USER", "sa")
MSSQL_PASSWORD: str = os.getenv("MSSQL_PASSWORD", "Rossmann@13June")
MSSQL_DATABASE: str = os.getenv("MSSQL_DATABASE", "Rossmann")

# ── Agent behaviour ───────────────────────────────────────────────────────────
SQL_MAX_ROWS: int = 1000
SQL_TIMEOUT_SECONDS: int = 15
MAX_REPAIR_ATTEMPTS: int = 2
MAX_HISTORY_TURNS: int = 5  # number of past turns kept in-context
