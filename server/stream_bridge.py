"""Convert LangGraph graph.stream() chunks into StreamMessage dicts for WebSocket.

Each chunk from graph.stream(stream_mode="values") is the accumulated
AgentState at that node. We diff consecutive chunks to detect what
changed and emit typed messages the Flutter client can render.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


class StreamBridge:
    REPORT_SECTIONS = [
        "market_report",
        "sentiment_report",
        "news_report",
        "fundamentals_report",
    ]

    REPORT_LABELS = {
        "market_report": "行情分析师",
        "sentiment_report": "情绪分析师",
        "news_report": "新闻分析师",
        "fundamentals_report": "基本面分析师",
    }

    def __init__(self) -> None:
        self._prev: Dict[str, Any] = {}
        self._sent_sections: set[str] = set()

    def convert(self, chunk: Dict[str, Any]) -> list[Dict[str, Any]]:
        msgs: list[Dict[str, Any]] = []

        # 1. Report sections
        for key in self.REPORT_SECTIONS:
            content = (chunk.get(key) or "").strip()
            if content:
                sections_key = f"_{key}"
                prev_content = (self._prev.get(sections_key) or "").strip()
                if content != prev_content:
                    self._prev[sections_key] = content
                    if key not in self._sent_sections and len(content) > 20:
                        self._sent_sections.add(key)
                        msgs.append({
                            "type": "report_section_start",
                            "data": {
                                "section": key,
                                "label": self.REPORT_LABELS.get(key, key),
                            },
                        })
                    msgs.append({
                        "type": "report_update",
                        "data": {"section": key, "content": content},
                    })

        # 2. Debate states
        for debate_key in ("investment_debate_state", "risk_debate_state"):
            state = chunk.get(debate_key, {})
            if state:
                prev_state = self._prev.get(debate_key, {})
                prev_json = prev_state.copy() if prev_state else {}
                if state != prev_json:
                    self._prev[debate_key] = state.copy()
                    msgs.append({
                        "type": "debate_update",
                        "data": {"key": debate_key, "state": state},
                    })

        # 3. Decision signals
        for final_key in ("investment_plan", "trader_investment_plan", "final_trade_decision"):
            content = (chunk.get(final_key) or "").strip()
            if content:
                prev_content = (self._prev.get(final_key) or "").strip()
                if content != prev_content:
                    self._prev[final_key] = content
                    msgs.append({
                        "type": "decision_update",
                        "data": {"key": final_key, "content": content},
                    })

        # 4. Agent status messages — extract from chunk messages
        raw_messages = chunk.get("messages", [])
        if raw_messages:
            prev_msg_count = self._prev.get("_msg_count", 0)
            new_msgs = raw_messages[prev_msg_count:]
            self._prev["_msg_count"] = len(raw_messages)
            for msg in new_msgs:
                msg_type, content = self._classify_message(msg)
                if msg_type and content:
                    msgs.append({
                        "type": "agent_message",
                        "data": {
                            "agent_type": msg_type,
                            "content": str(content)[:2000],
                            "timestamp": datetime.now().isoformat(),
                        },
                    })

        # 5. Tool call detection — check messages for tool_call attributes
        for msg in raw_messages:
            tool_calls = getattr(msg, "tool_calls", None) or []
            for tc in tool_calls:
                if isinstance(tc, dict):
                    name = tc.get("name", "")
                    args = tc.get("args", {})
                else:
                    name = getattr(tc, "name", "")
                    args = getattr(tc, "args", {})
                if name:
                    msgs.append({
                        "type": "tool_call",
                        "data": {
                            "name": name,
                            "args": {k: str(v) for k, v in (args or {}).items()},
                            "timestamp": datetime.now().isoformat(),
                        },
                    })

        return msgs

    @staticmethod
    def _classify_message(msg: Any) -> tuple[Optional[str], Optional[str]]:
        from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

        if isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, list):
                content = " ".join(
                    c.get("text", "") if isinstance(c, dict) else str(c)
                    for c in content
                )
            return "ai", str(content) if content else None
        if isinstance(msg, HumanMessage):
            return "human", str(msg.content) if msg.content else None
        if isinstance(msg, ToolMessage):
            return "tool", str(msg.content)[:500] if msg.content else None
        return None, None

    def complete_message(self, decision: str) -> Dict[str, Any]:
        return {
            "type": "complete",
            "data": {"decision": decision},
            "timestamp": datetime.now().isoformat(),
        }
