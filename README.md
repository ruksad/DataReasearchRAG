# DataResearchRAG

Conversational analytics agent that answers natural-language questions over the Rossmann Store Sales dataset using Text-to-SQL. Ask a question in plain English; the agent writes T-SQL, runs it against MS SQL Server, and returns a grounded answer with the exact query and result rows it used.

**Stack:** LangGraph · LangChain · Vanna AI (Schema-RAG) · ChromaDB · MS SQL Server (Docker) · Ollama / Anthropic / OpenAI

---

## Prerequisites

- Docker + Docker Compose
- Ollama running locally with Gemma pulled (`ollama pull gemma4:latest`) **or** an Anthropic/OpenAI API key
- Python 3.12+ *(local/CLI mode only — not needed for Docker)*

---

## Quickstart — Docker (recommended)

Everything runs in containers. Ollama stays on your host machine.

```bash
git clone <repo-url>
cd DataReasearchRAG

# 1. Copy config and fill in any API keys if not using Ollama
cp .env.example .env

# 2. First-time setup: build image → init DB → train Vanna (~5 min)
make docker-setup

# 3. Launch the app
make docker-start
```

Open **http://localhost:8501**.

To stop:
```bash
make docker-stop     # pause (data preserved)
make docker-down     # stop all containers (data preserved)
```

---

## Quickstart — Local

Run the API and UI directly on your machine (Python + Docker for the DB only).

```bash
git clone <repo-url>
cd DataReasearchRAG

# 1. Install Python dependencies
make install

# 2. Copy config
cp .env.example ~/.env   # edit ~/.env if needed

# 3. First-time setup: start DB → init schema → train Vanna
make setup

# 4. Launch API + Streamlit UI
make start
```

Open **http://localhost:8501**.

---

## Makefile reference

Run `make help` to see all targets.

### Setup targets

| Target | What it does |
|---|---|
| `make docker-setup` | **Docker first-time**: build image → init DB → train Vanna |
| `make setup` | **Local first-time**: install deps → start DB → init DB → train Vanna |
| `make install` | `pip install -r requirements.txt` |
| `make train` | Re-run Vanna training locally (after editing `training/`) |
| `make docker-train` | Re-run Vanna training inside Docker |

### Run targets

| Target | What it does |
|---|---|
| `make docker-start` | Start API + UI containers → http://localhost:8501 |
| `make docker-stop` | Stop API + UI (SQL Server keeps running) |
| `make docker-down` | Stop all containers (data volume preserved) |
| `make docker-reset` | Stop all + delete volumes + wipe `chroma_db/` *(irreversible)* |
| `make start` | Local: API in background + Streamlit in foreground |
| `make api` | Local: FastAPI only → http://localhost:8000 |
| `make ui` | Local: Streamlit only → http://localhost:8501 |
| `make stop` | Kill local API and Streamlit processes |

### Database targets *(local mode)*

| Target | What it does |
|---|---|
| `make db-up` | Start the SQL Server container |
| `make db-init` | One-time: create schema + bulk-load CSVs |
| `make db-verify` | Check row counts (Store=1115, Train≈1017209) |
| `make db-down` | Stop the container (data persists) |
| `make db-reset` | Delete volume — **all data lost** |

### Utility targets

| Target | What it does |
|---|---|
| `make docker-logs` | Tail API + UI container logs |
| `make docker-ps` | Show container status |
| `make docker-health` | `curl /health` against the API |
| `make health` | Same, for local mode |

### Overridable variables

```bash
make start    API_PORT=9000 UI_PORT=9501 LOG_LEVEL=DEBUG
make docker-start                         # uses defaults: 8000, 8501, INFO
```

---

## Configuration

### Docker

The `docker-compose.yml` reads from a `.env` file at the project root. Copy the example and fill in what you need:

```bash
cp .env.example .env
```

Docker networking overrides are baked into `docker-compose.yml` — you don't need to change `MSSQL_HOST` or `OLLAMA_BASE_URL` for Docker; they are set automatically.

### Local

The app reads from `~/.env` (home directory):

```bash
cp .env.example ~/.env
```

**Minimal config — Ollama (default, no API key needed):**
```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:latest
```

**Switch to Claude (Anthropic):**
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6
```

**Switch to OpenAI:**
```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

---

## Logging

All components log to stdout. Default level is `INFO`.

```bash
# Docker
LOG_LEVEL=DEBUG make docker-start
make docker-logs

# Local
LOG_LEVEL=DEBUG make start
LOG_LEVEL=DEBUG make api
```

Or set `LOG_LEVEL=DEBUG` in your `.env` / `~/.env` to apply it everywhere.

---

## CLI mode

Skip the UI and talk to the agent directly from the terminal:

```bash
# Single question
python main.py "What are the top 5 stores by total sales?"

# Interactive multi-turn chat (history carried across questions)
python main.py
```

---

## Vanna — Schema-RAG training

Vanna is the SQL generation layer. It learns from three artefacts stored in ChromaDB:

| Artefact | File | Purpose |
|---|---|---|
| DDL | `training/ddl.sql` | Table structures, column names, data types |
| Glossary | `training/glossary.md` | Business terms → SQL definitions |
| Q→SQL examples | `training/examples.jsonl` | ~20 question→SQL pairs |

Training runs automatically during `make setup` / `make docker-setup`. Re-run it after editing any `training/` file:

```bash
make train          # local
make docker-train   # Docker
```

Training takes ~30 seconds on first run (downloads the `all-MiniLM-L6-v2` embedding model). The `chroma_db/` folder is a bind mount in Docker — vectors persist on your host and survive `docker compose down`.

### Inspect ChromaDB contents

```bash
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
for col in client.list_collections():
    print(f'Collection: {col.name}')
    results = col.get(include=['documents', 'metadatas'])
    for doc, meta in zip(results['documents'], results['metadatas']):
        print(f'  [{meta}] {doc[:120]}')
"
```

---

## Conversation history

Every turn is persisted to `dbo.Conversations` in MS SQL automatically. Query it in DBeaver or sqlcmd:

```sql
-- Latest 10 turns across all sessions
SELECT TOP 10 SessionId, TurnOrder, LEFT(Question, 60) AS Question, CreatedAt
FROM dbo.Conversations ORDER BY CreatedAt DESC;

-- Full session
SELECT TurnOrder, Question, LEFT(Answer, 120) AS Answer, [RowCount], Rating, CreatedAt
FROM dbo.Conversations
WHERE SessionId = '<uuid>'
ORDER BY TurnOrder;
```

---

## Database schema

| Table | Rows | Key columns |
|---|---|---|
| `dbo.Store` | 1,115 | `Store` (PK), `StoreType` (a/b/c/d), `Assortment`, `CompetitionDistance`, `Promo2` |
| `dbo.Train` | ~1M | `Store`, `Date`, `Sales`, `[Open]`, `Promo`, `DayOfWeek`, `StateHoliday` |

Join: `dbo.Train.Store = dbo.Store.Store`

---

## Project structure

```
app/
  config.py          # env-based settings (LLM provider, DB, LOG_LEVEL)
  logging_config.py  # setup_logging() — called once at startup
  llm.py             # LLM provider factory (ollama / anthropic / openai)
  db.py              # SQLAlchemy engine + query runner
  vanna_setup.py     # Vanna factory — ChromaDB + LLM provider mixin
  memory.py          # persist_turn() → dbo.Conversations
  graph_state.py     # LangGraph AgentState
  graph.py           # LangGraph graph (nodes + edges)
  api.py             # FastAPI — /health, /ask, /feedback
  nodes/
    generate_sql.py  # Vanna → T-SQL (history-aware, repair-aware)
    validate_sql.py  # SELECT-only guardrail + TOP injection
    execute.py       # runs SQL against MS SQL
    synthesize.py    # LLM → grounded answer; persists turn
ui/
  streamlit_app.py   # Streamlit chat UI — wired to FastAPI
training/
  ddl.sql            # table DDL loaded into ChromaDB
  glossary.md        # business term definitions
  examples.jsonl     # Q→SQL training pairs
  train.py           # one-time training script
chroma_db/           # ChromaDB vector store (local, gitignored)
rossmann-store-sales/
  docker-compose.yml # legacy: standalone DB compose (used by local make targets)
  init/              # SQL init scripts + shell runner
  *.csv              # Rossmann dataset files
Dockerfile           # app image (api, ui, train share one image)
docker-compose.yml   # full-stack compose (sqlserver + api + ui + one-shot services)
Makefile             # all workflow targets — run 'make help'
main.py              # CLI entry point
requirements.txt
.env.example
```
