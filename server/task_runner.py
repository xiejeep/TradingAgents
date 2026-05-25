"""Background task runner — wraps TradingAgentsGraph.propagate() and
streams incremental state chunks to a WebSocket client.
"""

from __future__ import annotations

import asyncio
import queue
import threading
import traceback
from typing import Any, Dict, Optional

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.report_saver import save_report_to_disk
from tradingagents.agents.utils.history_index import get_history_index
from tradingagents.agents.utils.rating import parse_rating
from server.models import AnalysisConfig
from server.stream_bridge import StreamBridge


_TASKS: Dict[str, Dict[str, Any]] = {}
_task_counter: int = 0


def run_analysis_sync(
    config: AnalysisConfig,
    msg_queue: queue.Queue,
    task_id: str,
) -> None:
    bridge = StreamBridge()

    try:
        runtime_config = _build_runtime_config(config)

        graph = TradingAgentsGraph(
            selected_analysts=config.analysts,
            debug=False,
            config=runtime_config,
        )

        graph._resolve_pending_entries(config.ticker)

        past_context = graph.memory_log.get_past_context(config.ticker)

        state = graph.propagator.create_initial_state(
            company_name=config.ticker,
            trade_date=config.analysis_date,
            past_context=past_context,
        )
        args = graph.propagator.get_graph_args()

        trace = []
        for chunk in graph.graph.stream(state, **args):
            batch = bridge.convert(chunk)
            for msg in batch:
                msg_queue.put(msg)
            trace.append(chunk)

        final_state = {}
        for chunk in trace:
            final_state.update(chunk)

        graph.curr_state = final_state
        graph.ticker = config.ticker
        graph._log_state(config.analysis_date, final_state)

        decision = graph.process_signal(
            final_state.get("final_trade_decision", "")
        )

        graph.memory_log.store_decision(
            ticker=config.ticker,
            trade_date=config.analysis_date,
            final_trade_decision=final_state["final_trade_decision"],
        )

        rating = parse_rating(decision)

        report_path = save_report_to_disk(
            final_state, config.ticker, runtime_config["results_dir"]
        )

        history = get_history_index(runtime_config["results_dir"])
        history.add_entry(
            ticker=config.ticker,
            analysis_date=config.analysis_date,
            decision=decision,
            rating=rating,
            report_path=str(report_path.resolve()),
        )

        msg_queue.put(bridge.complete_message(decision))

        _TASKS[task_id] = {
            "status": "completed",
            "decision": decision,
            "rating": rating,
            "state": final_state,
            "report_path": str(report_path.resolve()),
        }

    except Exception:
        err_msg = traceback.format_exc()
        msg_queue.put({"type": "error", "data": {"message": err_msg}})
        _TASKS[task_id] = {"status": "error", "error": err_msg}


def start_analysis(config: AnalysisConfig) -> str:
    global _task_counter
    _task_counter += 1
    task_id = f"task_{_task_counter}"

    _TASKS[task_id] = {"status": "running"}

    msg_queue: queue.Queue = queue.Queue()
    _TASKS[task_id]["queue"] = msg_queue

    thread = threading.Thread(
        target=run_analysis_sync,
        args=(config, msg_queue, task_id),
        daemon=True,
    )
    thread.start()
    _TASKS[task_id]["thread"] = thread

    return task_id


async def stream_to_ws(task_id: str, ws_send):
    q: Optional[queue.Queue] = _TASKS.get(task_id, {}).get("queue")
    if q is None:
        await ws_send({"type": "error", "data": {"message": f"Unknown task: {task_id}"}})
        return

    loop = asyncio.get_running_loop()
    while True:
        try:
            msg = await loop.run_in_executor(None, q.get, True, 2.0)
            await ws_send(msg)
            if msg.get("type") in ("complete", "error"):
                break
        except queue.Empty:
            task_info = _TASKS.get(task_id)
            if task_info and task_info.get("status") != "running":
                break
            continue


def get_task_result(task_id: str) -> Optional[Dict[str, Any]]:
    return _TASKS.get(task_id)


def _build_runtime_config(cfg: AnalysisConfig) -> Dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    config["data_vendors"] = {
        "core_stock_apis": cfg.data_vendor,
        "technical_indicators": cfg.data_vendor,
        "fundamental_data": cfg.data_vendor,
        "news_data": cfg.data_vendor,
    }
    config["max_debate_rounds"] = cfg.research_depth
    config["max_risk_discuss_rounds"] = cfg.research_depth
    config["llm_provider"] = cfg.llm_provider
    config["quick_think_llm"] = cfg.shallow_thinker
    config["deep_think_llm"] = cfg.deep_thinker
    config["output_language"] = cfg.output_language
    config["checkpoint_enabled"] = cfg.checkpoint_enabled

    if cfg.backend_url:
        config["backend_url"] = cfg.backend_url
    if cfg.google_thinking_level:
        config["google_thinking_level"] = cfg.google_thinking_level
    if cfg.openai_reasoning_effort:
        config["openai_reasoning_effort"] = cfg.openai_reasoning_effort
    if cfg.anthropic_effort:
        config["anthropic_effort"] = cfg.anthropic_effort

    return config
