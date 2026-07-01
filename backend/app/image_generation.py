from __future__ import annotations

import base64
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from openai import OpenAI

from .models import CampaignBrief, CreativeVariant, Product, Segment
from .settings import get_settings

settings = get_settings()


def image_generation_config(brief: CampaignBrief | None = None) -> dict[str, str]:
    provider = brief.image_provider if brief else settings.image_provider
    if provider == "aws-bedrock-ready":
        return {
            "provider": "aws-bedrock-ready",
            "label": "AWS Bedrock-ready adapter",
            "model": settings.aws_bedrock_image_model,
            "status": "Adapter placeholder for production swap",
        }
    return {
        "provider": "gpt-image-2",
        "label": "GPT Image 2",
        "model": settings.openai_image_model,
        "status": "Default prototype image model",
    }


def build_image_prompt(
    brief: CampaignBrief,
    product: Product,
    segment: Segment,
    channel: str,
    image_style: str,
    prompt_note: str | None = None,
) -> dict[str, str]:
    config = image_generation_config(brief)
    marketer_note = f" Marketer asset direction: {prompt_note.strip()}." if prompt_note and prompt_note.strip() else ""
    presentation = image_presentation_instruction(brief)
    prompt = (
        f"Create a polished SEA fashion retail ad image for {channel}. "
        f"Product: {product.name}, {product.description} "
        f"Audience: {segment.name} ({segment.age_range}) in {', '.join(segment.markets)}. "
        f"Model presentation: {presentation} "
        f"Style: {image_style}, premium but practical, readable product, clean space for native UI text. "
        f"Creative direction from marketer: {brief.creative_instruction}.{marketer_note} "
        "No real brand names, no watermark, no unreadable text."
    )
    return {
        "provider": config["provider"],
        "provider_label": config["label"],
        "model": config["model"],
        "prompt": prompt,
    }


def generate_live_image(
    brief: CampaignBrief,
    variant: CreativeVariant,
    product: Product,
    segment: Segment,
    output_dir: Path,
    prompt_note: str | None = None,
) -> dict[str, str]:
    if brief.image_provider == "aws-bedrock-ready":
        raise RuntimeError("AWS Bedrock image adapter is configured as a future provider swap for this prototype.")

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    image_plan = build_image_prompt(brief, product, segment, variant.channel, variant.image_style, prompt_note)
    model = settings.openai_image_model or image_plan["model"]
    size = settings.openai_image_size or ("1024x1536" if variant.channel == "TikTok" else "1536x1024")
    quality = settings.openai_image_quality
    product_reference = static_file_from_url(product.image_url, output_dir.parent)
    product_lock = (
        "Use the attached product catalog image as the source of truth. "
        "Preserve the exact retail item: garment type, color, fabric texture, sleeve length, neckline, buttons, print, silhouette, and fit. "
        "Do not replace it with a different shirt, dress, trousers, or outfit. "
        "Use the catalog model only as a garment reference; do not preserve the person's identity. "
        "You may change the model, pose, background, crop, lighting, and platform composition only if the selected product remains clearly the same. "
    )
    prompt = (
        f"{product_lock if product_reference else ''}{image_plan['prompt']} "
        f"Ad format: {variant.format}. Headline direction: {variant.headline}. "
        "Create the visual only; leave final ad text to the application UI."
    )

    client = OpenAI(api_key=settings.openai_api_key)
    if product_reference:
        with product_reference.open("rb") as source_image:
            response = client.images.edit(
                model=model,
                image=source_image,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
                output_format="png",
            )
        generation_mode = "catalog_reference_edit"
        source_image_url = product.image_url
    else:
        response = client.images.generate(
            model=model,
            prompt=f"{prompt} Product identity must match: {product.name}, {product.description}.",
            size=size,
            quality=quality,
            n=1,
            output_format="png",
        )
        generation_mode = "text_to_image_fallback"
        source_image_url = ""

    image_base64 = response.data[0].b64_json
    image_url = response.data[0].url
    if image_base64:
        image_bytes = base64.b64decode(image_base64)
    elif image_url:
        with urllib.request.urlopen(image_url, timeout=60) as remote:
            image_bytes = remote.read()
    else:
        raise RuntimeError("Image generation did not return image data")

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:10]}.png"
    path = output_dir / filename
    path.write_bytes(image_bytes)

    return {
        "image_url": f"/static/generated/{filename}",
        "provider": image_plan["provider_label"],
        "model": model,
        "size": size,
        "quality": quality,
        "prompt": prompt,
        "prompt_note": prompt_note or "",
        "generation_mode": generation_mode,
        "source_image_url": source_image_url,
        "model_presentation": brief.model_presentation,
    }


def image_presentation_instruction(brief: CampaignBrief) -> str:
    if brief.model_presentation == "male_model":
        return "adult male fashion model, non-identifiable, natural SEA retail styling, product remains the hero."
    if brief.model_presentation == "product_only":
        return "product-only flat lay, hanger, mannequin, or clean studio still life; no person, no face, no body parts."
    return "adult female fashion model, non-identifiable, natural SEA retail styling, product remains the hero."


def static_file_from_url(image_url: str, static_root: Path) -> Path | None:
    parsed = urlparse(image_url)
    path = parsed.path if parsed.scheme else image_url
    if not path.startswith("/static/"):
        return None
    candidate = static_root / path.removeprefix("/static/")
    if candidate.is_file():
        return candidate
    return None
