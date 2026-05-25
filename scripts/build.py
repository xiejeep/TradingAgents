#!/usr/bin/env python3
"""Build TradingAgents into a standalone Windows .exe.

Usage:
    python scripts/build.py          # build frontend + package
    python scripts/build.py --skip-frontend   # skip npm build (dist already exists)
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"
SERVER_ENTRY = PROJECT_ROOT / "server" / "main.py"
OUTPUT_NAME = "TradingAgents"

LANGCHAIN_PACKAGES = [
    "langchain_core",
    "langchain_openai",
    "langchain_anthropic",
    "langchain_google_genai",
    "langgraph",
]

DATA_PACKAGES = [
    "fpdf",
    "yfinance",
    "akshare",
    "stockstats",
    "redis",
    "backtrader",
    "questionary",
    "rich",
    "fastapi",
    "uvicorn",
    "websockets",
    "aiofiles",
    "starlette",
]

TRADINGAGENTS_MODULES = [
    "tradingagents.agents.analysts.market_analyst",
    "tradingagents.agents.analysts.news_analyst",
    "tradingagents.agents.analysts.sentiment_analyst",
    "tradingagents.agents.analysts.fundamentals_analyst",
    "tradingagents.agents.analysts.social_media_analyst",
    "tradingagents.agents.researchers.bull_researcher",
    "tradingagents.agents.researchers.bear_researcher",
    "tradingagents.agents.risk_mgmt.aggressive_debator",
    "tradingagents.agents.risk_mgmt.conservative_debator",
    "tradingagents.agents.risk_mgmt.neutral_debator",
    "tradingagents.agents.managers.research_manager",
    "tradingagents.agents.managers.portfolio_manager",
    "tradingagents.agents.trader.trader",
    "tradingagents.agents.utils.agent_states",
    "tradingagents.agents.utils.agent_utils",
    "tradingagents.agents.utils.core_stock_tools",
    "tradingagents.agents.utils.fundamental_data_tools",
    "tradingagents.agents.utils.history_index",
    "tradingagents.agents.utils.memory",
    "tradingagents.agents.utils.news_data_tools",
    "tradingagents.agents.utils.pdf_exporter",
    "tradingagents.agents.utils.rating",
    "tradingagents.agents.utils.report_saver",
    "tradingagents.agents.utils.structured",
    "tradingagents.agents.utils.technical_indicators_tools",
    "tradingagents.dataflows.akshare",
    "tradingagents.dataflows.akshare_common",
    "tradingagents.dataflows.akshare_fundamentals",
    "tradingagents.dataflows.akshare_news",
    "tradingagents.dataflows.akshare_stock",
    "tradingagents.dataflows.alpha_vantage",
    "tradingagents.dataflows.alpha_vantage_common",
    "tradingagents.dataflows.alpha_vantage_fundamentals",
    "tradingagents.dataflows.alpha_vantage_indicator",
    "tradingagents.dataflows.alpha_vantage_news",
    "tradingagents.dataflows.alpha_vantage_stock",
    "tradingagents.dataflows.config",
    "tradingagents.dataflows.interface",
    "tradingagents.dataflows.reddit",
    "tradingagents.dataflows.stockstats_utils",
    "tradingagents.dataflows.stocktwits",
    "tradingagents.dataflows.utils",
    "tradingagents.dataflows.y_finance",
    "tradingagents.dataflows.yfinance_news",
    "tradingagents.default_config",
    "tradingagents.graph.analyst_execution",
    "tradingagents.graph.checkpointer",
    "tradingagents.graph.conditional_logic",
    "tradingagents.graph.propagation",
    "tradingagents.graph.reflection",
    "tradingagents.graph.setup",
    "tradingagents.graph.signal_processing",
    "tradingagents.graph.trading_graph",
    "tradingagents.llm_clients.anthropic_client",
    "tradingagents.llm_clients.api_key_env",
    "tradingagents.llm_clients.azure_client",
    "tradingagents.llm_clients.base_client",
    "tradingagents.llm_clients.capabilities",
    "tradingagents.llm_clients.factory",
    "tradingagents.llm_clients.google_client",
    "tradingagents.llm_clients.model_catalog",
    "tradingagents.llm_clients.openai_client",
    "tradingagents.llm_clients.validators",
]


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"\033[36m> {' '.join(cmd)}\033[0m")
    subprocess.run(cmd, check=True, cwd=cwd)


def build_frontend() -> None:
    if not (FRONTEND_DIR / "node_modules").exists():
        print("Installing frontend dependencies...")
        _run(["npm", "install"], cwd=FRONTEND_DIR)

    print("Building frontend...")
    _run(["npm", "run", "build"], cwd=FRONTEND_DIR)

    if not FRONTEND_DIST.is_dir():
        sys.exit(f"Frontend build failed: {FRONTEND_DIST} not found")


def build_exe() -> None:
    print("Packaging with PyInstaller...")

    is_windows = sys.platform == "win32"
    separator = ";" if is_windows else ":"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--clean",
        "--noconfirm",
        "--name", OUTPUT_NAME,
        "--add-data", f"frontend{os.sep}dist{separator}frontend{os.sep}dist",
    ]

    if is_windows:
        python_dll_dir = Path(sys.executable).parent / "DLLs"
        for dll in ("libcrypto-3.dll", "libssl-3.dll"):
            dll_path = python_dll_dir / dll
            if dll_path.is_file():
                cmd.extend(["--add-binary", str(dll_path) + separator + "."])

    for pkg in LANGCHAIN_PACKAGES + DATA_PACKAGES:
        cmd.extend(["--collect-all", pkg])

    for mod in TRADINGAGENTS_MODULES:
        cmd.extend(["--hidden-import", mod])

    cmd.append(str(SERVER_ENTRY))

    _run(cmd, cwd=PROJECT_ROOT)

    exe_name = Path("dist") / (f"{OUTPUT_NAME}.exe" if is_windows else OUTPUT_NAME)
    full_path = PROJECT_ROOT / exe_name
    if full_path.exists():
        size_mb = full_path.stat().st_size / (1024 * 1024)
        print(f"\n\033[32mBuild successful!\033[0m")
        print(f"  Output: {full_path}")
        print(f"  Size: {size_mb:.1f} MB")
    else:
        print(f"\n\033[33mOutput not found at {full_path}\033[0m")


def main() -> None:
    os.chdir(PROJECT_ROOT)

    skip_frontend = "--skip-frontend" in sys.argv

    if not skip_frontend:
        build_frontend()
    elif not FRONTEND_DIST.is_dir():
        sys.exit(f"{FRONTEND_DIST} not found. Run without --skip-frontend to build first.")

    build_exe()


if __name__ == "__main__":
    main()
