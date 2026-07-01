from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agent import run_brief_copilot, run_campaign_agent, run_insight_copilot
from .analytics import build_insight_engine
from .data_loader import BASE_DIR, load_campaign_rows, load_products, load_segments, source_statuses
from .exporter import export_campaign_package
from .image_generation import generate_live_image, image_generation_config
from .models import AgentResult, CampaignBrief, CreativeVariant
from .settings import get_settings
from .video_generation import generate_live_video, video_generation_config

settings = get_settings()

app = FastAPI(
    title="AI-Powered Retail Ad Studio",
    version="0.1.0",
    description="Prototype backend for data-informed retail creative generation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class ImageGenerationRequest(BaseModel):
    brief: CampaignBrief
    variant: CreativeVariant
    prompt_note: str | None = None


class VideoGenerationRequest(BaseModel):
    brief: CampaignBrief
    variant: CreativeVariant
    prompt_note: str | None = None
    reference_image_url: str | None = None
    reference_image_role: str = "reference_image"


class InsightRefreshRequest(BaseModel):
    brief: CampaignBrief


class BriefRefineRequest(BaseModel):
    brief: CampaignBrief
    note: str


class ExportCampaignRequest(BaseModel):
    brief: CampaignBrief
    result: AgentResult
    selected_variant_id: str | None = None
    generated_images: dict[str, dict[str, Any]] = Field(default_factory=dict)
    generated_videos: dict[str, dict[str, Any]] = Field(default_factory=dict)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "openai_configured": bool(settings.openai_api_key),
        "ark_configured": bool(settings.ark_api_key),
        "model": settings.openai_model,
        "image_generation": image_generation_config(),
        "video_generation": video_generation_config(),
        "data_path": str(BASE_DIR / "data"),
    }


@app.get("/api/bootstrap")
def bootstrap() -> dict:
    campaigns = load_campaign_rows()
    products = load_products()
    segments = load_segments()
    default_brief = CampaignBrief(product_ids=[product.id for product in products[:4]])
    insight_engine = build_insight_engine(campaigns, products, segments, default_brief)
    return {
        "products": [product.model_dump() for product in products],
        "segments": [segment.model_dump() for segment in segments],
        "data_sources": [source.model_dump() for source in source_statuses()],
        "campaign_count": len(campaigns),
        "default_brief": default_brief.model_dump(),
        "insight_engine": insight_engine,
        "aws_mapping": {
            "current": "Local CSV/JSON/static images for portable demo",
            "future": [
                "Amazon S3",
                "AWS Glue",
                "DynamoDB or Aurora",
                "Amazon Bedrock/OpenAI image adapter",
                "Amazon Nova Reel video generation",
                "ECS/App Runner",
                "CloudFront",
            ],
        },
        "video_generation": video_generation_config(),
    }


@app.post("/api/generate")
def generate(brief: CampaignBrief) -> dict:
    result = run_campaign_agent(brief)
    return result.model_dump()


@app.post("/api/refresh-insight")
def refresh_insight(request: InsightRefreshRequest) -> dict:
    return run_insight_copilot(request.brief)


@app.post("/api/refine-brief")
def refine_brief(request: BriefRefineRequest) -> dict:
    return run_brief_copilot(request.note, request.brief)


@app.post("/api/generate-image")
def generate_image(request: ImageGenerationRequest) -> dict:
    products = load_products()
    segments = load_segments()
    product = next((item for item in products if item.id == request.variant.product_id), None)
    segment = next((item for item in segments if item.id == request.variant.segment_id), None)
    if not product or not segment:
        raise HTTPException(status_code=404, detail="Product or segment not found for selected creative")

    try:
        image = generate_live_image(request.brief, request.variant, product, segment, static_dir / "generated", request.prompt_note)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        **image,
        "cost_guardrail": "Generated one selected creative image only using the selected catalog product as reference.",
    }


@app.post("/api/generate-video")
def generate_video(request: VideoGenerationRequest) -> dict:
    products = load_products()
    segments = load_segments()
    product = next((item for item in products if item.id == request.variant.product_id), None)
    segment = next((item for item in segments if item.id == request.variant.segment_id), None)
    if not product or not segment:
        raise HTTPException(status_code=404, detail="Product or segment not found for selected creative")

    return generate_live_video(
        request.brief,
        request.variant,
        product,
        segment,
        static_dir / "generated" / "videos",
        prompt_note=request.prompt_note,
        reference_image_url=request.reference_image_url,
        reference_image_role=request.reference_image_role,
    )


@app.post("/api/export-campaign")
def export_campaign(request: ExportCampaignRequest) -> dict:
    return export_campaign_package(
        request.brief,
        request.result,
        request.selected_variant_id,
        request.generated_images,
        request.generated_videos,
        static_dir / "exports",
    )


@app.get("/api/files")
def files() -> dict:
    data_dir = BASE_DIR / "data"
    return {
        "data": sorted(path.name for path in data_dir.iterdir() if path.is_file()),
        "product_images": sorted(path.name for path in (BASE_DIR / "static" / "products").iterdir() if path.is_file()),
    }
