import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma4:latest")

MSSQL_HOST: str = os.getenv("MSSQL_HOST", "localhost")
MSSQL_PORT: int = int(os.getenv("MSSQL_PORT", "1433"))
MSSQL_USER: str = os.getenv("MSSQL_USER", "sa")
MSSQL_PASSWORD: str = os.getenv("MSSQL_PASSWORD", "Rossmann@13June")
MSSQL_DATABASE: str = os.getenv("MSSQL_DATABASE", "Rossmann")

SQL_MAX_ROWS: int = 1000
SQL_TIMEOUT_SECONDS: int = 15
MAX_REPAIR_ATTEMPTS: int = 2
