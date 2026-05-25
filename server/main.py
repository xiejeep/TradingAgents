"""TradingAgents FastAPI server — REST API + WebSocket streaming.

Start with:
    python server/main.py
    uvicorn server.main:app --reload --port 8000
"""

from __future__ import annotations

import json
import sys
import os
import threading
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.models import AnalysisConfig, TaskCreated, ModelOption
from server.task_runner import start_analysis, stream_to_ws, get_task_result
from server.settings_manager import get_key_status, save_keys
from server.license import get_machine_code, is_activated, save_activation
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.history_index import get_history_index
from tradingagents.agents.utils.report_saver import save_report_to_disk
from tradingagents.agents.utils.pdf_exporter import export_report_file_to_pdf


def _get_frontend_dir() -> Optional[str]:
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", "")
        candidate = os.path.join(base, "frontend", "dist")
        if os.path.isdir(candidate):
            return candidate
    candidate = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    if os.path.isdir(candidate):
        return os.path.realpath(candidate)
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="TradingAgents API", version="0.2.5", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESULTS_DIR = DEFAULT_CONFIG.get("results_dir", str(Path.home() / ".tradingagents" / "logs"))


async def _require_license():
    """FastAPI dependency — blocks endpoints if not activated."""
    if not is_activated():
        raise HTTPException(
            status_code=403,
            detail="Not activated. Use /api/license to activate.",
        )


@app.post("/api/analyze", response_model=TaskCreated)
async def api_analyze(config: AnalysisConfig, _lic=Depends(_require_license)):
    task_id = start_analysis(config)
    return TaskCreated(task_id=task_id)


@app.websocket("/ws/stream/{task_id}")
async def ws_stream(ws: WebSocket, task_id: str):
    await ws.accept()

    async def send_msg(msg: dict) -> None:
        await ws.send_text(json.dumps(msg, ensure_ascii=False, default=str))

    try:
        await stream_to_ws(task_id, send_msg)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await send_msg({"type": "error", "data": {"message": str(e)}})
    finally:
        try:
            await ws.close()
        except Exception:
            pass


@app.get("/api/report/{task_id}")
async def api_report(task_id: str):
    result = get_task_result(task_id)
    if result is None:
        return {"error": f"Unknown task: {task_id}"}
    if result["status"] == "completed":
        state = result.get("state", {})
        return {
            "task_id": task_id,
            "status": "completed",
            "decision": result.get("decision", ""),
            "rating": result.get("rating", ""),
            "report_path": result.get("report_path", ""),
            "market_report": state.get("market_report", ""),
            "sentiment_report": state.get("sentiment_report", ""),
            "news_report": state.get("news_report", ""),
            "fundamentals_report": state.get("fundamentals_report", ""),
            "investment_plan": state.get("investment_plan", ""),
            "trader_investment_plan": state.get("trader_investment_plan", ""),
            "final_trade_decision": state.get("final_trade_decision", ""),
        }
    return {"task_id": task_id, "status": result["status"]}


@app.get("/api/history")
async def api_history(
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    limit: int = Query(50, ge=1, le=200, description="Maximum entries to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    history = get_history_index(RESULTS_DIR)
    entries = history.list_entries(ticker=ticker, limit=limit, offset=offset)
    return {
        "entries": entries,
        "total": history.total_count(ticker=ticker),
        "limit": limit,
        "offset": offset,
    }


def _read_file(base: Path, *parts: str) -> str:
    path = base.joinpath(*parts)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


@app.get("/api/history/{entry_id}")
async def api_history_detail(entry_id: str):
    history = get_history_index(RESULTS_DIR)
    entry = history.get_entry(entry_id)
    if entry is None:
        return {"error": f"Unknown entry: {entry_id}"}

    report_content = None
    sections = {}
    report_path = entry.get("report_path")
    if report_path:
        rp = Path(report_path)
        complete_report = rp / "complete_report.md"
        if complete_report.exists():
            report_content = complete_report.read_text(encoding="utf-8")

        sections["market_report"] = _read_file(rp, "1_analysts", "market.md")
        sections["sentiment_report"] = _read_file(rp, "1_analysts", "sentiment.md")
        sections["news_report"] = _read_file(rp, "1_analysts", "news.md")
        sections["fundamentals_report"] = _read_file(rp, "1_analysts", "fundamentals.md")
        sections["investment_plan"] = _read_file(rp, "2_research", "manager.md")
        sections["trader_investment_plan"] = _read_file(rp, "3_trading", "trader.md")
        sections["final_trade_decision"] = _read_file(rp, "5_portfolio", "decision.md")

    return {
        "entry": entry,
        "report_content": report_content,
        **sections,
    }


@app.get("/api/history/{entry_id}/pdf")
async def api_history_pdf(entry_id: str):
    history = get_history_index(RESULTS_DIR)
    entry = history.get_entry(entry_id)
    if entry is None:
        return {"error": f"Unknown entry: {entry_id}"}

    report_path = entry.get("report_path")
    if not report_path:
        return {"error": "Report path not available for this entry"}

    report_dir = Path(report_path)
    if not report_dir.exists():
        return {"error": "Report directory not found"}

    try:
        pdf_path = export_report_file_to_pdf(str(report_dir))
        ticker = entry.get("ticker", "report")
        pdf_data = Path(pdf_path).read_bytes()
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{ticker}_analysis_report.pdf"',
            },
        )
    except ImportError as e:
        return {"error": str(e), "hint": "Install fpdf2: pip install fpdf2"}
    except Exception as e:
        return {"error": f"Failed to generate PDF: {e}"}


@app.get("/api/report/{task_id}/pdf")
async def api_report_pdf(task_id: str):
    result = get_task_result(task_id)
    if result is None:
        return {"error": f"Unknown task: {task_id}"}
    if result["status"] != "completed":
        return {"error": f"Task not completed (status: {result['status']})"}

    report_path = result.get("report_path")
    if not report_path:
        return {"error": "Report not saved to disk yet"}

    report_dir = Path(report_path)
    if not report_dir.exists():
        return {"error": "Report directory not found"}

    try:
        pdf_path = export_report_file_to_pdf(str(report_dir))
        ticker = "analysis_report"
        pdf_data = Path(pdf_path).read_bytes()
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{ticker}.pdf"',
            },
        )
    except ImportError as e:
        return {"error": str(e), "hint": "Install fpdf2: pip install fpdf2"}
    except Exception as e:
        return {"error": f"Failed to generate PDF: {e}"}


@app.get("/api/models/{provider}", response_model=None)
async def api_models(provider: str, mode: str = Query("quick")):
    from tradingagents.llm_clients.model_catalog import get_model_options as get_models

    models = get_models(provider, mode)
    return models


@app.get("/api/health")
async def api_health():
    return {"status": "ok"}


@app.get("/api/license")
async def api_license_status():
    return {
        "activated": is_activated(),
        "machine_code": get_machine_code(),
    }


@app.post("/api/license")
async def api_license_activate(payload: dict):
    code = payload.get("code", "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Activation code is required")
    if save_activation(code):
        return {"status": "ok"}
    raise HTTPException(status_code=403, detail="Invalid activation code")



@app.get("/api/settings")
async def api_get_settings():
    return get_key_status()


@app.post("/api/settings")
async def api_save_settings(payload: dict):
    save_keys(payload.get("keys", {}))
    return {"status": "ok"}


_fd = _get_frontend_dir()
if _fd:
    app.mount("/", StaticFiles(directory=_fd, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    def _open_browser() -> None:
        webbrowser.open(f"http://localhost:{port}")

    threading.Timer(1.5, _open_browser).start()

    uvicorn.run(app, host="0.0.0.0", port=port)
