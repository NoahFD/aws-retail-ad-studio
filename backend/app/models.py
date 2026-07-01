from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Channel = Literal["Meta", "TikTok", "Display", "Email"]
Objective = Literal["Sales", "Traffic", "Awareness", "Retention"]
ImageProvider = Literal["gpt-image-2", "aws-bedrock-ready"]
ModelPresentation = Literal["female_model", "male_model", "product_only"]


class CampaignBrief(BaseModel):
    campaign_name: str = "Maya Style Refresh - Week 3"
    objective: Objective = "Sales"
    market: str = "Singapore"
    primary_segment_id: str = "seg_urban_professionals"
    additional_segment_id: str | None = "seg_style_enthusiasts"
    channels: list[Channel] = Field(default_factory=lambda: ["Meta", "TikTok", "Display", "Email"])
    product_ids: list[str] = Field(default_factory=list)
    budget_sgd: int = 1500
    trend_window: str = "Next 14 days"
    tone: str = "Confident, premium, useful"
    strategy_id: str = "trend_window"
    creative_instruction: str = "Show confident SEA styling, readable products, and concise premium copy."
    image_provider: ImageProvider = "gpt-image-2"
    model_presentation: ModelPresentation = "female_model"
    use_live_ai: bool = False
    generation_mode: Literal["generate", "optimize"] = "generate"


class Product(BaseModel):
    id: str
    name: str
    category: str
    price_sgd: float
    description: str
    image_url: str
    tags: list[str]
    margin: float
    inventory_score: int


class Segment(BaseModel):
    id: str
    name: str
    age_range: str
    markets: list[str]
    size_millions: float
    profile: str
    preferred_channels: list[Channel]
    copy_preferences: list[str]
    price_sensitivity: str
    creative_notes: str


class DataSourceStatus(BaseModel):
    name: str
    type: str
    status: Literal["connected", "warning", "offline"]
    records: int
    freshness: str
    aws_target: str


class InsightMetric(BaseModel):
    label: str
    value: str
    delta: str
    sentiment: Literal["positive", "neutral", "negative"] = "neutral"


class CreativeVariant(BaseModel):
    id: str
    channel: Channel
    format: str
    product_id: str
    segment_id: str
    headline: str
    body: str
    cta: str
    visual_direction: str
    image_style: str
    copy_style: str
    predicted_ctr: float
    predicted_roas: float
    predicted_lift: float
    confidence: int
    rationale: str
    image_prompt: str | None = None
    image_provider: str | None = None
    rank: int | None = None


class AgentResult(BaseModel):
    brief: CampaignBrief
    plan: dict
    insights: list[InsightMetric]
    variants: list[CreativeVariant]
    top_patterns: list[dict]
    agent_steps: list[dict]
    data_sources: list[DataSourceStatus]
    live_ai_used: bool = False
    cost_guardrail: str
    errors: list[str] = Field(default_factory=list)
