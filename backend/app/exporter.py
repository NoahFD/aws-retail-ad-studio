from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .data_loader import load_products
from .models import AgentResult, CampaignBrief, CreativeVariant


def export_campaign_package(
    brief: CampaignBrief,
    result: AgentResult,
    selected_variant_id: str | None,
    generated_images: dict[str, dict[str, Any]],
    generated_videos: dict[str, dict[str, Any]] | None,
    output_dir: Path,
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    slug = slugify(brief.campaign_name)
    filename = f"{slug}-{timestamp}.zip"
    output_dir.mkdir(parents=True, exist_ok=True)
    package_path = output_dir / filename
    selected_variant = selected_export_variant(result.variants, selected_variant_id)
    products_by_id = {product.id: product for product in load_products()}
    bundled_assets = [
        *collect_catalog_assets(result.variants, products_by_id, output_dir.parent),
        *collect_generated_assets(generated_images, generated_videos or {}, output_dir.parent),
    ]
    manifest_assets = [
        {key: value for key, value in asset.items() if key != "_local_path"}
        for asset in bundled_assets
    ]

    manifest = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "campaign_name": brief.campaign_name,
        "storage_target": "local-backend",
        "aws_ready_target": f"s3://retail-creative-exports/{filename}",
        "brief": brief.model_dump(),
        "plan": result.plan,
        "insights": [item.model_dump() for item in result.insights],
        "selected_variant": selected_variant.model_dump() if selected_variant else None,
        "generated_images": generated_images,
        "generated_videos": generated_videos or {},
        "bundled_assets": manifest_assets,
        "top_patterns": result.top_patterns,
        "data_sources": [item.model_dump() for item in result.data_sources],
        "cost_guardrail": result.cost_guardrail,
        "aws_handoff_note": (
            "Prototype writes this package to backend/static/exports. In AWS, write the same zip bytes "
            "to Amazon S3, store manifest metadata in DynamoDB or Aurora, and return a presigned URL."
        ),
    }

    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        archive.writestr("variants.csv", variants_csv(result.variants))
        archive.writestr("README.txt", export_readme(brief, selected_variant, filename))
        for asset in bundled_assets:
            archive.write(asset["_local_path"], asset["file"])

    return {
        "export_id": package_path.stem,
        "filename": filename,
        "download_url": f"/static/exports/{filename}",
        "storage_target": "Local backend folder: backend/static/exports",
        "aws_ready_target": f"s3://retail-creative-exports/{filename}",
        "file_size_bytes": package_path.stat().st_size,
        "cost_guardrail": "Export uses existing catalog/generated assets only. No AI call was made.",
    }


def collect_catalog_assets(
    variants: list[CreativeVariant],
    products_by_id: dict[str, Any],
    static_root: Path,
) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    seen_product_ids: set[str] = set()
    for variant in variants:
        if variant.product_id in seen_product_ids:
            continue
        product = products_by_id.get(variant.product_id)
        if not product:
            continue
        local_path = local_static_path(product.image_url, static_root)
        if not local_path or not local_path.is_file():
            continue
        seen_product_ids.add(variant.product_id)
        archive_name = f"assets/catalog/{slugify(product.id)}-{local_path.name}"
        assets.append(
            {
                "product_id": product.id,
                "type": "catalog_reference_image",
                "source_url": product.image_url,
                "file": archive_name,
                "bytes": local_path.stat().st_size,
                "_local_path": local_path,
            }
        )
    return assets


def collect_generated_assets(
    generated_images: dict[str, dict[str, Any]],
    generated_videos: dict[str, dict[str, Any]],
    static_root: Path,
) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for variant_id, payload in generated_images.items():
        add_static_asset(assets, static_root, variant_id, "image", payload.get("image_url"), "assets/images")
    for variant_id, payload in generated_videos.items():
        add_static_asset(assets, static_root, variant_id, "video", payload.get("video_url"), "assets/videos")
    return assets


def add_static_asset(
    assets: list[dict[str, Any]],
    static_root: Path,
    variant_id: str,
    asset_type: str,
    url: str | None,
    archive_dir: str,
) -> None:
    if not url:
        return
    local_path = local_static_path(url, static_root)
    if not local_path or not local_path.is_file():
        return
    archive_name = f"{archive_dir}/{slugify(variant_id)}-{local_path.name}"
    assets.append(
        {
            "variant_id": variant_id,
            "type": asset_type,
            "source_url": url,
            "file": archive_name,
            "bytes": local_path.stat().st_size,
            "_local_path": local_path,
        }
    )


def local_static_path(url: str, static_root: Path) -> Path | None:
    path = url.split("?", 1)[0]
    if not path.startswith("/static/"):
        return None
    return static_root / path.removeprefix("/static/")


def selected_export_variant(variants: list[CreativeVariant], selected_variant_id: str | None) -> CreativeVariant | None:
    if selected_variant_id:
        selected = next((variant for variant in variants if variant.id == selected_variant_id), None)
        if selected:
            return selected
    return variants[0] if variants else None


def variants_csv(variants: list[CreativeVariant]) -> str:
    fieldnames = [
        "rank",
        "id",
        "channel",
        "format",
        "product_id",
        "segment_id",
        "headline",
        "body",
        "cta",
        "predicted_roas",
        "predicted_ctr",
        "predicted_lift",
        "confidence",
        "rationale",
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for variant in variants:
        row = variant.model_dump()
        writer.writerow({field: row.get(field, "") for field in fieldnames})
    return buffer.getvalue()


def export_readme(brief: CampaignBrief, selected_variant: CreativeVariant | None, filename: str) -> str:
    selected = selected_variant.headline if selected_variant else "No selected creative"
    return "\n".join(
        [
            "SEA Creative Hub Campaign Export",
            "",
            f"Campaign: {brief.campaign_name}",
            f"Market: {brief.market}",
            f"Platforms: {', '.join(brief.channels)}",
            f"Selected creative: {selected}",
            "",
            "Files",
            "- manifest.json: full brief, plan, insights, selected creative, and source metadata",
            "- variants.csv: ranked creative variants for media or agency handoff",
            "- assets/catalog: product reference images used by the ranked previews",
            "- assets/images: generated creative images included for local review",
            "- assets/videos: generated videos included when a live video was created",
            "- README.txt: this summary",
            "",
            "AWS-ready path",
            f"- Local prototype file: backend/static/exports/{filename}",
            f"- Future S3 object: s3://retail-creative-exports/{filename}",
            "- Future services: S3 for package storage, DynamoDB/Aurora for metadata, presigned URL for download",
        ]
    )


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "campaign-export"
