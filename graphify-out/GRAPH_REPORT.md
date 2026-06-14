# Graph Report - .  (2026-06-14)

## Corpus Check
- Corpus is ~4,120 words - fits in a single context window. You may not need a graph.

## Summary
- 32 nodes · 40 edges · 7 communities (6 shown, 1 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Rossmann DB Infrastructure|Rossmann DB Infrastructure]]
- [[_COMMUNITY_MVP API and Guardrails|MVP API and Guardrails]]
- [[_COMMUNITY_Rossmann Feature Engineering|Rossmann Feature Engineering]]
- [[_COMMUNITY_Agentic RAG Pipeline|Agentic RAG Pipeline]]
- [[_COMMUNITY_Text-to-SQL Core|Text-to-SQL Core]]
- [[_COMMUNITY_Time-Series RAG Research|Time-Series RAG Research]]
- [[_COMMUNITY_DB Init Entry Point|DB Init Entry Point]]

## God Nodes (most connected - your core abstractions)
1. `MVP Architecture — Conversational Analytics over MS SQL` - 13 edges
2. `Rossmann Store Sales — EDA Insights` - 8 edges
3. `LangGraph Agent Loop (Orchestration)` - 5 edges
4. `sqlserver Docker Service` - 4 edges
5. `load_rossmann.sql — Rossmann DB Schema & Bulk Load` - 3 edges
6. `dbo.Store Table` - 3 edges
7. `dbo.Train Table` - 3 edges
8. `init-db Docker Service` - 3 edges
9. `Schema-RAG — Vanna Vector Store (DDL + Q→SQL examples)` - 3 edges
10. `Vanna AI — Text-to-SQL Core` - 3 edges

## Surprising Connections (you probably didn't know these)
- `Agentic RAG for Time Series (multi-agent hierarchy)` --semantically_similar_to--> `LangGraph Agent Loop (Orchestration)`  [INFERRED] [semantically similar]
  notes.md → MVP_Architecture_Conversational_Analytics.md
- `GoodData Analytics RAG (BI semantic graph)` --semantically_similar_to--> `Schema-RAG — Vanna Vector Store (DDL + Q→SQL examples)`  [INFERRED] [semantically similar]
  notes.md → MVP_Architecture_Conversational_Analytics.md
- `TS-RAG / Retrieval-Augmented Forecasting (Phase 2 Roadmap)` --semantically_similar_to--> `TS-RAG — Zero-Shot Forecasting with TSFMs`  [INFERRED] [semantically similar]
  MVP_Architecture_Conversational_Analytics.md → notes.md
- `Rossmann Store Sales — EDA Insights` --references--> `dbo.Store Table`  [INFERRED]
  rossmann-store-sales/EDA_Insights.md → rossmann-store-sales/init/load_rossmann.sql
- `Rossmann Store Sales — EDA Insights` --references--> `dbo.Train Table`  [INFERRED]
  rossmann-store-sales/EDA_Insights.md → rossmann-store-sales/init/load_rossmann.sql

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Rossmann DB Initialization Pipeline** — rossmann_docker_compose, rossmann_initdb_service, init_init_sh, init_load_rossmann_sql [EXTRACTED 1.00]
- **MVP Text-to-SQL Core Flow** — mvp_schema_rag, mvp_vanna_ai, mvp_langgraph_agent, mvp_validate_sql, mvp_grounded_synthesis [EXTRACTED 1.00]
- **Rossmann Feature Engineering Decisions** — eda_ispromo2active, eda_log1p_target, eda_rolling_features, eda_was_closed_yesterday, eda_open0_drop [EXTRACTED 1.00]

## Communities (7 total, 1 thin omitted)

### Community 0 - "Rossmann DB Infrastructure"
Cohesion: 0.43
Nodes (7): init.sh — DB Init Script, load_rossmann.sql — Rossmann DB Schema & Bulk Load, dbo.Store Table, dbo.Train Table, docker-compose.yml — Rossmann SQL Server Stack, init-db Docker Service, sqlserver Docker Service

### Community 1 - "MVP API and Guardrails"
Cohesion: 0.33
Nodes (7): MVP Architecture — Conversational Analytics over MS SQL, FastAPI — /ask /health /feedback, LangSmith / Langfuse Observability, OWASP Top 10 for LLM Applications, Semantic Cache (question→SQL/result), Spider / BIRD Text-to-SQL Benchmarks, validate_sql Guardrail — SELECT-only, TOP n, Timeout

### Community 2 - "Rossmann Feature Engineering"
Cohesion: 0.33
Nodes (6): IsPromo2Active Derived Feature, log1p(Sales) Target Transformation, Drop Open=0 Rows from Training, Rolling Window Features (7d, 30d per store), was_closed_yesterday Lag Feature, Rossmann Store Sales — EDA Insights

### Community 3 - "Agentic RAG Pipeline"
Cohesion: 0.50
Nodes (4): Grounded Synthesis + Citations (data provenance), LangGraph Agent Loop (Orchestration), RAGAS Faithfulness Metrics, Agentic RAG for Time Series (multi-agent hierarchy)

### Community 4 - "Text-to-SQL Core"
Cohesion: 0.67
Nodes (3): Schema-RAG — Vanna Vector Store (DDL + Q→SQL examples), Vanna AI — Text-to-SQL Core, GoodData Analytics RAG (BI semantic graph)

### Community 5 - "Time-Series RAG Research"
Cohesion: 0.67
Nodes (3): TS-RAG / Retrieval-Augmented Forecasting (Phase 2 Roadmap), RAF — Retrieval Augmented Forecasting, TS-RAG — Zero-Shot Forecasting with TSFMs

## Knowledge Gaps
- **13 isolated node(s):** `init.sh script`, `FastAPI — /ask /health /feedback`, `LangSmith / Langfuse Observability`, `Spider / BIRD Text-to-SQL Benchmarks`, `Semantic Cache (question→SQL/result)` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MVP Architecture — Conversational Analytics over MS SQL` connect `MVP API and Guardrails` to `Rossmann Feature Engineering`, `Agentic RAG Pipeline`, `Text-to-SQL Core`, `Time-Series RAG Research`?**
  _High betweenness centrality (0.661) - this node is a cross-community bridge._
- **Why does `Rossmann Store Sales — EDA Insights` connect `Rossmann Feature Engineering` to `Rossmann DB Infrastructure`, `MVP API and Guardrails`?**
  _High betweenness centrality (0.536) - this node is a cross-community bridge._
- **Why does `dbo.Store Table` connect `Rossmann DB Infrastructure` to `Rossmann Feature Engineering`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Rossmann Store Sales — EDA Insights` (e.g. with `MVP Architecture — Conversational Analytics over MS SQL` and `dbo.Store Table`) actually correct?**
  _`Rossmann Store Sales — EDA Insights` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `sqlserver Docker Service` (e.g. with `dbo.Store Table` and `dbo.Train Table`) actually correct?**
  _`sqlserver Docker Service` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `init.sh script`, `FastAPI — /ask /health /feedback`, `LangSmith / Langfuse Observability` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._