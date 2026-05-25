# AGENTS.md — TradingAgents

## Setup
- `uv sync` or `pip install -e .` (package name is `tradingagents`, lowercase)
- Copy `.env.example` to `.env` and set at least one LLM provider key

## Commands
- **Dev server (FastAPI backend):** `python -m server.main` (defaults to `PORT=8000`; frontend proxy expects 8002 — either set `PORT=8002` or update `vite.config.ts`)
- **Frontend dev:** `cd frontend && npm run dev` (port 5173, proxies `/api` and `/ws` to 8002)
- **CLI:** `tradingagents` or `python -m cli.main`
- **Build EXE:** `python scripts/build.py` (PyInstaller; builds frontend first, then packages the server as a single-file Windows .exe; `--skip-frontend` to reuse existing dist)
- **Tests:** `pytest` or `pytest -m "not integration"` (skips external-service tests)
- **Single test file:** `pytest tests/path/to/test_file.py -v`

## Testing
- Framework: pytest with custom markers `unit`, `integration`, `smoke`
- `conftest.py` auto-injects placeholder API keys for all 14+ providers — tests never hang waiting for env
- Use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.smoke` on test functions
- `mock_llm_client` fixture patches `create_llm_client` with a MagicMock

## Architecture
- **`tradingagents/`** — main Python package
  - `agents/` — LLM-powered agents (analysts, researchers, trader, risk debaters, managers)
  - `dataflows/` — vendor abstraction layer (yfinance / Alpha Vantage / AKShare)
  - `graph/` — LangGraph StateGraph orchestration (`trading_graph.py`, `setup.py`, `propagation.py`)
  - `llm_clients/` — provider factory (10+ providers → 4 client classes)
- **`server/`** — FastAPI backend (REST + WebSocket streaming)
- **`frontend/`** — Vue 3 + Vite + Ant Design Vue (separate app, not served by Python)
- **`cli/`** — Typer CLI with interactive wizard
- Python API entrypoint: `TradingAgentsGraph().propagate("NVDA", "2025-01-15")`

## Graph workflow (LangGraph)
```
Market Analyst → Sentiment Analyst → News Analyst → Fundamentals Analyst
→ Bull↔Bear debate → Research Manager → Trader
→ Aggressive↔Conservative↔Neutral risk debate → Portfolio Manager → END
```
- Two LLM instances: `deep_thinking_llm` (Research Manager, Portfolio Manager) and `quick_thinking_llm` (all others)
- SQLite checkpoint/resume supported; enable with `TRADINGAGENTS_CHECKPOINT_ENABLED=true`

## Configuration
- Single source of truth: `tradingagents/default_config.py` `DEFAULT_CONFIG` dict
- Override via `TRADINGAGENTS_*` env vars (auto-coerced to match default type: bool/int/str)
- `.env` is auto-loaded in `tradingagents/__init__.py` — no need for `load_dotenv()` manually
- Key defaults: `llm_provider=deepseek`, `output_language=Chinese`, `max_debate_rounds=1`

## No linting/formatter config
- This repo has **no** ruff, mypy, eslint, or prettier configuration. Do not run those tools without adding config first.

## Persistence
- Decision log: `~/.tradingagents/memory/trading_memory.md` (append-only markdown)
- Checkpoint DBs: `~/.tradingagents/checkpoints/` (SQLite, per analysis task)
- Data cache: `~/.tradingagents/cache/`

## LLM provider notes
- All OpenAI-compatible providers (openai, xai, deepseek, qwen, glm, minimax, ollama, openrouter) share one `OpenAIClient` class
- Provider quirks (tool_choice support, json_schema support, reasoning roundtrip) are declared in `tradingagents/llm_clients/capabilities.py`
- Model catalog in `tradingagents/llm_clients/model_catalog.py` is the source of truth for available models per provider
- OpenRouter models are fetched dynamically; Azure uses free-form deployment names
