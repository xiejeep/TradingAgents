from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AnalysisConfig(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    analysis_date: str = Field(..., description="Analysis date YYYY-MM-DD")
    data_vendor: str = Field(default="yfinance", description="yfinance | alpha_vantage | akshare")
    output_language: str = Field(default="Chinese")
    analysts: List[str] = Field(
        default_factory=lambda: ["market", "social", "news", "fundamentals"],
        description="Selected analyst keys",
    )
    research_depth: int = Field(default=1, ge=1, le=5, description="1=shallow, 3=medium, 5=deep")
    llm_provider: str = Field(default="deepseek")
    backend_url: Optional[str] = Field(default=None)
    shallow_thinker: str = Field(default="deepseek-v4-flash")
    deep_thinker: str = Field(default="deepseek-v4-pro")
    google_thinking_level: Optional[str] = Field(default=None)
    openai_reasoning_effort: Optional[str] = Field(default=None)
    anthropic_effort: Optional[str] = Field(default=None)
    checkpoint_enabled: bool = Field(default=False)


class TaskCreated(BaseModel):
    task_id: str


class StreamMessage(BaseModel):
    type: str
    data: Optional[Dict] = None
    content: Optional[str] = None


class ModelOption(BaseModel):
    provider: str
    models: List[Dict[str, str]]
