# DataResearchRAG

Conversational analytics agent that answers natural-language questions over the Rossmann Store Sales dataset using Text-to-SQL. Ask a question in plain English; the agent writes T-SQL, runs it against MS SQL Server, and returns a grounded answer with the exact query and result rows it used.

**Stack:** LangGraph · LangChain · Vanna AI (Schema-RAG) · ChromaDB · MS SQL Server (Docker) · Ollama / Anthropic / OpenAI

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

## 4. Train Vanna — Schema-RAG (run once)

Vanna is the SQL generation layer. Before running the agent, you must train it by loading three artefacts into ChromaDB (the local vector store):

| Artefact | File | What it teaches Vanna |
|---|---|---|
| DDL | `training/ddl.sql` | Table structures, column names, data types |
| Glossary | `training/glossary.md` | Business terms → SQL definitions (e.g. "open day" = `[Open] = 1`) |
| Q→SQL examples | `training/examples.jsonl` | ~20 question→SQL pairs for retrieval |

```bash
# From the repo root — run once, or re-run to add new examples
python training/train.py
```

**When to re-run:**
- You add new Q→SQL pairs to `training/examples.jsonl`
- You add new business terms to `training/glossary.md`
- You change the DB schema and update `training/ddl.sql`
- You delete `chroma_db/` and need to rebuild from scratch

Training takes ~30 seconds on first run (downloads the ChromaDB embedding model `all-MiniLM-L6-v2`). Subsequent runs are fast.

### How Vanna stores data in ChromaDB

ChromaDB stores each training artefact as a **document + embedding** pair. The embedding is a 384-dimensional vector computed from the text — this is what enables semantic search ("find examples similar to this question").

What's actually stored (from a live collection inspect):

```json
{
  "documents": [
    "{\"question\": \"Top 5 stores by total sales\", \"sql\": \"SELECT TOP 5 Store, SUM(Sales) AS TotalSales FROM dbo.Train WHERE [Open] = 1 GROUP BY Store ORDER BY TotalSales DESC\"}",
    "{\"question\": \"Average sales by store type\", \"sql\": \"SELECT s.StoreType, AVG(t.Sales) AS AvgSales FROM dbo.Train t JOIN dbo.Store s ON t.Store = s.Store WHERE t.[Open] = 1 GROUP BY s.StoreType ORDER BY AvgSales DESC\"}",
    "... (20 Q→SQL pairs, DDL, glossary)"
  ],
  "embeddings": "[ 384 floats per document — not human-readable ]",
  "metadatas": [{ "training_data_type": "sql" }, ...]
}
```

At query time, the user's question is embedded and the **top-k most similar documents** are retrieved and injected into the LLM prompt — so the model sees the relevant schema fragments and the closest Q→SQL examples, not the full training corpus.

### Inspect what's stored in ChromaDB

**Python (quickest):**

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

**Via ChromaDB HTTP server:**

```bash
# Start the server (if not already running)
chroma run --path ./chroma_db --port 8001

# List collections
curl http://localhost:8001/api/v2/tenants/default_tenant/databases/default_database/collections

# Get all documents in a collection (replace <collection-id> from the list above)
curl -X POST \
  http://localhost:8001/api/v2/tenants/default_tenant/databases/default_database/collections/<collection-id>/get \
  -H "Content-Type: application/json" \
  -d '{"include": ["documents", "metadatas"]}'
```

> The `embeddings` field is null by default in the API response. Add `"embeddings"` to the `include` array to see the raw vectors — 384 floats per document that are not human-readable.

---

## 5. Conversation history

Every completed turn is persisted to `dbo.Conversations` in MS SQL automatically — no extra setup needed. The table is created by `init-db` on first run.

**Schema:**

```sql
dbo.Conversations (Id, SessionId, TurnOrder, Question, SqlQuery, Answer, [RowCount], CreatedAt)
```

Each CLI session gets a UUID `SessionId` printed at startup. Query a session in DBeaver or sqlcmd:

```sql
-- All turns in a session
SELECT TurnOrder, Question, LEFT(Answer, 120) AS Answer, [RowCount], CreatedAt
FROM dbo.Conversations
WHERE SessionId = '<uuid-from-console>'
ORDER BY TurnOrder;

-- Latest 10 turns across all sessions
SELECT TOP 10 SessionId, TurnOrder, LEFT(Question, 60) AS Question, CreatedAt
FROM dbo.Conversations ORDER BY CreatedAt DESC;
```

> **Existing installs:** if you ran `init-db` before this feature was added, create the table manually:
> ```bash
> docker exec -i sqlserver-rossmann /opt/mssql-tools18/bin/sqlcmd \
>   -S localhost -U sa -P 'Rossmann@13June' -C \
>   -i rossmann-store-sales/init/create_conversations.sql
> ```

---

## 6. Run the application

### Option A — Web UI (recommended)

Two terminal windows, both from the repo root:

```bash
# Terminal 1 — FastAPI backend (port 8000)
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Streamlit frontend (port 8501)
streamlit run ui/streamlit_app.py
```

Then open **http://localhost:8501** in your browser.

The sidebar lets you configure the API URL (default `http://localhost:8000`), start a new session, and see sample questions. Each answer shows an expandable SQL block, result table, and citation. Use 👍/👎 to rate any answer — the rating is stored in `dbo.Conversations.Rating`.

**Verify the API is up:**

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

**Ask a question directly via the API:**

```bash
curl -s -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Top 5 stores by total sales"}' | python -m json.tool
```

---

### Option B — CLI (single question or interactive chat)

```bash
# Single question
python main.py "What are the top 5 stores by total sales?"
python main.py "Which day of the week has the highest average sales?"
python main.py "How does promo affect sales across different store types?"

# Interactive multi-turn chat (carries history across questions)
python main.py
```

**Override the LLM provider inline (without editing ~/.env):**

```bash
LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... python main.py "Which store type has the highest average sales?"
LLM_PROVIDER=openai   OPENAI_API_KEY=sk-...       python main.py "Which store type has the highest average sales?"
LLM_PROVIDER=ollama   OLLAMA_MODEL=llama3.2        python main.py "Which store type has the highest average sales?"
```

---

### Logging

All components log to stdout. The default level is `INFO`. To change it:

```bash
# Verbose (shows SQL previews, Vanna internals, per-query timing)
LOG_LEVEL=DEBUG uvicorn app.api:app --port 8000 --reload
LOG_LEVEL=DEBUG python main.py

# Quiet (warnings and errors only)
LOG_LEVEL=WARNING uvicorn app.api:app --port 8000
```

Or set `LOG_LEVEL=DEBUG` in `~/.env` to apply it everywhere.

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
  config.py          # env-based settings (LLM provider, DB, LOG_LEVEL)
  logging_config.py  # setup_logging() — called once at startup
  llm.py             # LLM provider factory (ollama / anthropic / openai)
  db.py              # SQLAlchemy engine + query runner
  vanna_setup.py     # Vanna factory — ChromaDB + LLM provider mixin
  memory.py          # persist_turn() → dbo.Conversations
  graph_state.py     # LangGraph AgentState (question, sql, rows, history, session_id, …)
  graph.py           # LangGraph graph (nodes + edges)
  api.py             # FastAPI — /health, /ask, /feedback
  nodes/
    generate_sql.py  # Vanna → T-SQL (history-aware, repair-aware)
    validate_sql.py  # SELECT-only guardrail + TOP injection
    execute.py       # runs SQL against MS SQL
    synthesize.py    # LLM → grounded answer; persists turn to dbo.Conversations
ui/
  streamlit_app.py   # Streamlit chat UI — wired to FastAPI /ask and /feedback
training/
  ddl.sql            # table DDL loaded into ChromaDB
  glossary.md        # business term definitions loaded into ChromaDB
  examples.jsonl     # Q→SQL training pairs (one JSON object per line)
  train.py           # one-time training script
chroma_db/           # ChromaDB vector store (local, gitignored)
rossmann-store-sales/
  docker-compose.yml
  init/
    load_rossmann.sql         # creates Rossmann DB, dbo.Store, dbo.Train; bulk-loads CSVs
    create_conversations.sql  # creates dbo.Conversations (idempotent)
    init.sh                   # runs both scripts in order
  *.csv              # Rossmann dataset files
main.py              # CLI entry point
requirements.txt
.env.example
```
