# DataResearchRAG

Conversational analytics agent that answers natural-language questions over the Rossmann Store Sales dataset using Text-to-SQL. Ask a question in plain English; the agent writes T-SQL, runs it against MS SQL Server, and returns a grounded answer with the exact query and result rows it used.

**Stack:** LangGraph · LangChain · MS SQL Server (Docker) · Ollama / Anthropic / OpenAI

---

## Prerequisites

- Python 3.12+
- Docker + Docker Compose
- Ollama running locally (default) **or** an Anthropic/OpenAI API key

---

## 1. Clone and install dependencies

```bash
git clone <repo-url>
cd DataReasearchRAG
pip install -r requirements.txt
```

---

## 2. Configure environment variables

The app loads variables from `~/.env` (your home directory). Copy the example and fill in the values you need:

```bash
cp .env.example ~/.env
```

### Minimal config (Ollama — no API key needed)

```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:latest
```

### Switch to Claude (Anthropic)

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6
```

### Switch to OpenAI

```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

> `langchain-anthropic` or `langchain-openai` must be installed when using those providers:
> ```bash
> pip install langchain-anthropic   # for Anthropic
> pip install langchain-openai      # for OpenAI
> ```

---

## 3. Start the database

```bash
cd rossmann-store-sales

# First run: start SQL Server and bulk-load the CSVs into the Rossmann DB
docker compose up -d sqlserver
docker compose up --abort-on-container-exit init-db

# Subsequent runs: just start the server (data persists in the Docker volume)
docker compose start sqlserver
```

**Verify the data loaded:**

```bash
docker exec -it sqlserver-rossmann /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Rossmann@13June' -C \
  -Q "USE Rossmann; SELECT COUNT(*) AS store_rows FROM dbo.Store; SELECT COUNT(*) AS train_rows FROM dbo.Train;"
```

Expected: `store_rows = 1115`, `train_rows ≈ 1017209`.

**Stop the server:**

```bash
docker compose stop sqlserver

# Stop and delete all data (volume)
docker compose down -v
```

---

## 4. Run the agent

```bash
# From the repo root
python main.py "What are the top 5 stores by total sales?"
python main.py "Which day of the week has the highest average sales?"
python main.py "How does promo affect sales across different store types?"
```

**Override the LLM provider inline (without editing ~/.env):**

```bash
LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... python main.py "Which store type has the highest average sales?"
LLM_PROVIDER=openai   OPENAI_API_KEY=sk-...       python main.py "Which store type has the highest average sales?"
LLM_PROVIDER=ollama   OLLAMA_MODEL=llama3.2        python main.py "Which store type has the highest average sales?"
```

---

## Database schema (quick reference)

| Table | Rows | Key columns |
|---|---|---|
| `dbo.Store` | 1,115 | `Store` (PK), `StoreType` (a/b/c/d), `Assortment`, `CompetitionDistance`, `Promo2` |
| `dbo.Train` | ~1M | `Store`, `Date`, `Sales`, `[Open]`, `Promo`, `DayOfWeek`, `StateHoliday` |

Join: `dbo.Train.Store = dbo.Store.Store`

---

## Project structure

```
app/
  config.py          # env-based settings
  llm.py             # LLM provider factory (ollama / anthropic / openai)
  db.py              # SQLAlchemy engine + query runner
  schema.py          # DDL context fed to the LLM
  graph_state.py     # LangGraph AgentState
  graph.py           # LangGraph graph (nodes + edges)
  nodes/
    generate_sql.py  # LLM → T-SQL (repair-aware)
    validate_sql.py  # SELECT-only guardrail + TOP injection
    execute.py       # runs SQL against MS SQL
    synthesize.py    # LLM → grounded answer
rossmann-store-sales/
  docker-compose.yml
  init/              # SQL init scripts + shell loader
  *.csv              # Rossmann dataset files
main.py              # CLI entry point
requirements.txt
.env.example
```
