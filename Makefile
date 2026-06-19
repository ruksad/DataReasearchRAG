# ── Config (override on the command line: make start API_PORT=9000) ──────────
API_PORT  ?= 8000
UI_PORT   ?= 8501
LOG_LEVEL ?= INFO
LLM_PROVIDER ?= ollama
ANTHROPIC_API_KEY ?= someKey
DB_DIR    := rossmann-store-sales

# Internal files used to track background PIDs
_API_PID  := .api.pid

# ── Phony targets ─────────────────────────────────────────────────────────────
.PHONY: help install setup train \
        db-up db-init db-down db-reset db-verify \
        api ui start stop health \
        docker-build docker-setup docker-start docker-stop \
        docker-train docker-down docker-reset docker-logs docker-ps docker-health

# ── Default: print usage ──────────────────────────────────────────────────────
help:
	@echo ""
	@echo "DataResearchRAG — Makefile targets"
	@echo ""
	@echo "  First-time setup"
	@echo "    make setup        install → db-up → db-init → train"
	@echo "    make install      pip install -r requirements.txt"
	@echo "    make train        load DDL/glossary/examples into ChromaDB"
	@echo "                      (re-run whenever training/ files change)"
	@echo ""
	@echo "  Database  (MS SQL Server in Docker)"
	@echo "    make db-up        start the SQL Server container"
	@echo "    make db-init      first run: create DB and bulk-load CSVs"
	@echo "    make db-verify    check row counts (Store=1115, Train≈1017209)"
	@echo "    make db-down      stop the container (data persists)"
	@echo "    make db-reset     stop + delete volume — ALL DATA LOST"
	@echo ""
	@echo "  Run"
	@echo "    make start        API in background + Streamlit in foreground"
	@echo "    make api          FastAPI only   → http://localhost:$(API_PORT)"
	@echo "    make ui           Streamlit only → http://localhost:$(UI_PORT)"
	@echo "    make stop         kill running API and UI processes"
	@echo "    make health       curl /health on the API"
	@echo ""
	@echo "  Overridable vars:  API_PORT=$(API_PORT)  UI_PORT=$(UI_PORT)  LOG_LEVEL=$(LOG_LEVEL)"
	@echo ""
	@echo "  Docker (full-stack — Ollama runs on host)"
	@echo "    make docker-setup    build image → init DB → train Vanna (first time)"
	@echo "    make docker-start    start API + UI  (SQL Server must already be up)"
	@echo "    make docker-stop     stop API + UI   (SQL Server keeps running)"
	@echo "    make docker-down     stop all containers  (data volume preserved)"
	@echo "    make docker-reset    stop all + delete volumes + wipe chroma_db/"
	@echo "    make docker-train    re-run Vanna training inside Docker"
	@echo "    make docker-logs     tail API + UI logs"
	@echo "    make docker-ps       show container status"
	@echo "    make docker-health   curl /health"
	@echo "    make docker-build    rebuild the app image (after code changes)"
	@echo ""

# ── Dependencies ──────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

# ── Database ──────────────────────────────────────────────────────────────────
db-up:
	@echo ">>> Starting SQL Server..."
	docker compose -f $(DB_DIR)/docker-compose.yml start sqlserver 2>/dev/null || \
	docker compose -f $(DB_DIR)/docker-compose.yml up -d sqlserver
	@echo "    Waiting for SQL Server to accept connections..."
	@sleep 5
	@echo "    SQL Server ready."

db-init:
	@echo ">>> Initialising database (create schema + bulk-load CSVs)..."
	docker compose -f $(DB_DIR)/docker-compose.yml up --abort-on-container-exit init-db
	@echo "    Database initialised."

db-verify:
	@echo ">>> Verifying row counts..."
	docker exec -it sqlserver-rossmann /opt/mssql-tools18/bin/sqlcmd \
	  -S localhost -U sa -P 'Rossmann@13June' -C \
	  -Q "USE Rossmann; \
	      SELECT COUNT(*) AS store_rows FROM dbo.Store; \
	      SELECT COUNT(*) AS train_rows FROM dbo.Train;"

db-down:
	@echo ">>> Stopping SQL Server (data persists in volume)..."
	docker compose -f $(DB_DIR)/docker-compose.yml stop sqlserver

db-reset:
	@echo ">>> WARNING: this will DELETE all data in the Docker volume."
	@read -p "    Type 'yes' to continue: " ans && [ "$$ans" = "yes" ]
	docker compose -f $(DB_DIR)/docker-compose.yml down -v
	@echo "    Volume removed. Run 'make db-up db-init' to recreate."

# ── Vanna / ChromaDB training ─────────────────────────────────────────────────
train:
	@echo ">>> Training Vanna (DDL + glossary + Q→SQL examples → ChromaDB)..."
	python training/train.py
	@echo "    Training complete."

# ── Application ───────────────────────────────────────────────────────────────
api:
	LOG_LEVEL=$(LOG_LEVEL) LLM_PROVIDER=$(LLM_PROVIDER)  ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY) uvicorn app.api:app \
	  --host 0.0.0.0 --port $(API_PORT) --reload

ui:
	streamlit run ui/streamlit_app.py \
	  --server.port $(UI_PORT) \
	  --server.address 0.0.0.0

start:
	@echo ">>> Starting FastAPI on port $(API_PORT) (background)..."
	LOG_LEVEL=$(LOG_LEVEL) uvicorn app.api:app \
	  --host 0.0.0.0 --port $(API_PORT) \
	  > /tmp/dataresearchrag-api.log 2>&1 & echo $$! > $(_API_PID)
	@echo "    API PID $$(cat $(_API_PID)) — logs: /tmp/dataresearchrag-api.log"
	@echo ">>> Waiting for API to be ready..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
	  curl -sf http://localhost:$(API_PORT)/health > /dev/null && break; \
	  echo "    ... ($$i/10)"; sleep 2; \
	done
	@curl -sf http://localhost:$(API_PORT)/health > /dev/null \
	  && echo "    API is up." \
	  || echo "    WARNING: API did not respond — check /tmp/dataresearchrag-api.log"
	@echo ">>> Starting Streamlit on port $(UI_PORT) (foreground — Ctrl-C to stop)..."
	@echo "    Open http://localhost:$(UI_PORT)"
	streamlit run ui/streamlit_app.py \
	  --server.port $(UI_PORT) \
	  --server.address 0.0.0.0
	@$(MAKE) stop

stop:
	@echo ">>> Stopping API..."
	@if [ -f $(_API_PID) ]; then \
	  kill $$(cat $(_API_PID)) 2>/dev/null && echo "    API stopped." || echo "    API was not running."; \
	  rm -f $(_API_PID); \
	else \
	  pkill -f "uvicorn app.api:app" 2>/dev/null && echo "    API stopped." || echo "    API was not running."; \
	fi
	@echo ">>> Stopping Streamlit..."
	@pkill -f "streamlit run ui/streamlit_app.py" 2>/dev/null \
	  && echo "    Streamlit stopped." || echo "    Streamlit was not running."

health:
	@curl -sf http://localhost:$(API_PORT)/health \
	  && echo "" \
	  || (echo "API not reachable at http://localhost:$(API_PORT)" && exit 1)

# ── First-time local setup (chains the above) ────────────────────────────────
setup: install db-up db-init train
	@echo ""
	@echo "=========================================="
	@echo "  Setup complete. Run 'make start' to launch."
	@echo "=========================================="

# ─────────────────────────────────────────────────────────────────────────────
# Docker targets  (full-stack: SQL Server + API + Streamlit, Ollama on host)
# ─────────────────────────────────────────────────────────────────────────────

docker-build:
	@echo ">>> Building app image..."
	docker compose build

docker-setup: docker-build
	@echo ">>> Starting SQL Server..."
	docker compose up -d sqlserver
	@echo ">>> Waiting for SQL Server to be healthy..."
	@until docker compose ps sqlserver | grep -q "healthy"; do \
	  printf "."; sleep 3; \
	done; echo ""
	@echo ">>> Initialising database (first run only)..."
	docker compose --profile init run --rm init-db
	@echo ">>> Training Vanna (loads DDL/glossary/examples into ChromaDB)..."
	docker compose --profile train run --rm train
	@echo ""
	@echo "=========================================="
	@echo "  Docker setup complete."
	@echo "  Run 'make docker-start' to launch the app."
	@echo "=========================================="

docker-start:
	@echo ">>> Starting API and UI..."
	docker compose up -d api ui
	@echo ""
	@echo "  API  → http://localhost:8000"
	@echo "  UI   → http://localhost:8501"

docker-stop:
	@echo ">>> Stopping API and UI (SQL Server keeps running)..."
	docker compose stop api ui

docker-down:
	@echo ">>> Stopping all containers (data volume preserved)..."
	docker compose down

docker-reset:
	@echo ">>> WARNING: this will DELETE all data and the ChromaDB volume."
	@read -p "    Type 'yes' to continue: " ans && [ "$$ans" = "yes" ]
	docker compose down -v
	rm -rf chroma_db/
	@echo "    Reset complete. Run 'make docker-setup' to start fresh."

docker-train:
	@echo ">>> Re-training Vanna inside Docker..."
	docker compose --profile train run --rm train
	@echo "    Training complete."

docker-logs:
	docker compose logs -f api ui

docker-ps:
	docker compose ps

docker-health:
	@curl -sf http://localhost:8000/health \
	  && echo "" \
	  || (echo "API not reachable at http://localhost:8000" && exit 1)
