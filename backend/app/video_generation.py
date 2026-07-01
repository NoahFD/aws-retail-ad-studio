from __future__ import annotations

import base64
import json
import mimetypes
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from .models import CampaignBrief, CreativeVariant, Product, Segment
from .settings import get_settings

settings = get_settings()

DEMO_VIDEO_URL = "/static/generated/videos/demo-seedance-fashion.mp4"


def video_generation_config() -> dict[str, Any]:
    provider = settings.video_provider
    if provider == "aws-nova-reel":
        return {
            "provider": provider,
            "label": "AWS Nova Reel",
            "model": settings.aws_nova_reel_model,
            "status": "AWS Bedrock video adapter ready",
            "live_enabled": settings.video_live_enabled,
            "configured": bool(settings.aws_nova_reel_s3_uri),
        }
    if provider == "demo-cached":
        return {
            "provider": provider,
            "label": "Cached demo video",
            "model": "local-demo-mp4",
            "status": "Cost-safe demo fallback",
            "live_enabled": False,
            "configured": True,
        }
    return {
        "provider": "seedance-ark",
        "label": "Seedance 2.0 via BytePlus Ark",
        "model": settings.seedance_model,
        "status": "Live video adapter ready when Ark model is activated",
        "live_enabled": settings.video_live_enabled,
        "configured": bool(settings.ark_api_key),
    }


def build_video_prompt(
    brief: CampaignBrief,
    variant: CreativeVariant,
    product: Product,
    segment: Segment,
    prompt_note: str | None = None,
    has_reference_image: bool = False,
) -> str:
    presentation = video_presentation_instruction(brief)
    reference_instruction = (
        "Use the provided reference image for the model, garment identity, styling, and opening frame. "
        "Keep the selected product visually consistent throughout the clip. "
        if has_reference_image
        else ""
    )
    marketer_note = f" Marketer asset direction: {prompt_note.strip()}." if prompt_note and prompt_note.strip() else ""
    return (
        f"Create a short vertical retail fashion ad for {variant.channel}. "
        f"Market: {brief.market}. Product: {product.name}, {product.description}. "
        f"Audience: {segment.name}, {segment.age_range}, profile: {segment.profile}. "
        f"Campaign direction: {brief.creative_instruction}.{marketer_note} "
        f"Model presentation: {presentation} "
        f"{reference_instruction}"
        "Use natural motion, premium Southeast Asia city styling, visible fabric texture, warm daylight, "
        "clean social-commerce energy, no logos, no subtitles, no watermark, no unreadable text."
    )


def generate_live_video(
    brief: CampaignBrief,
    variant: CreativeVariant,
    product: Product,
    segment: Segment,
    output_dir: Path,
    prompt_note: str | None = None,
    reference_image_url: str | None = None,
    reference_image_role: str = "reference_image",
) -> dict[str, Any]:
    provider_reference_image = provider_image_reference(reference_image_url, output_dir.parent.parent)
    prompt = build_video_prompt(brief, variant, product, segment, prompt_note, bool(provider_reference_image))
    config = video_generation_config()

    if config["provider"] == "aws-nova-reel":
        return generate_aws_nova_video(prompt, output_dir, reference_image_url=reference_image_url, reference_image_role=reference_image_role)
    if config["provider"] == "demo-cached" or not settings.video_live_enabled:
        return demo_video_result(
            prompt,
            fallback_reason="Using the cached demo clip so the executive walkthrough stays instant and cost-safe.",
            reference_image_url=reference_image_url,
            reference_image_role=reference_image_role,
        )
    return generate_seedance_video(prompt, output_dir, provider_reference_image, reference_image_url, reference_image_role)


def generate_seedance_video(
    prompt: str,
    output_dir: Path,
    provider_reference_image: str | None = None,
    reference_image_url: str | None = None,
    reference_image_role: str = "reference_image",
) -> dict[str, Any]:
    if not settings.ark_api_key:
        return demo_video_result(
            prompt,
            fallback_reason="Seedance is selected, but ARK_API_KEY is not configured. Demo clip shown.",
            reference_image_url=reference_image_url,
            reference_image_role=reference_image_role,
        )

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    if provider_reference_image:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": provider_reference_image},
                "role": reference_image_role,
            }
        )

    payload = {
        "model": settings.seedance_model,
        "content": content,
        "ratio": settings.seedance_ratio,
        "resolution": settings.seedance_resolution,
        "duration": settings.seedance_duration_seconds,
        "watermark": False,
        "generate_audio": False,
    }
    status_code, created = ark_request_json("POST", "/contents/generations/tasks", payload)
    if status_code < 200 or status_code >= 300:
        provider_error = summarize_provider_error(created)
        if provider_reference_image and is_reference_image_policy_block(provider_error):
            retry_prompt = privacy_safe_video_prompt(reference_safe_text_prompt(prompt))
            return generate_seedance_video(
                retry_prompt,
                output_dir,
                provider_reference_image=None,
                reference_image_url=None,
                reference_image_role="text_prompt_retry",
            )
        return demo_video_result(
            prompt,
            provider="Seedance 2.0 via BytePlus Ark",
            model=settings.seedance_model,
            fallback_reason=provider_error,
            reference_image_url=reference_image_url,
            reference_image_role=reference_image_role,
        )

    task_id = created.get("id") or created.get("task_id")
    if not task_id:
        return demo_video_result(
            prompt,
            provider="Seedance 2.0 via BytePlus Ark",
            model=settings.seedance_model,
            fallback_reason="Seedance accepted the request but did not return a task id. Demo clip shown.",
            reference_image_url=reference_image_url,
            reference_image_role=reference_image_role,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = output_dir / f"seedance-{task_id}.json"
    metadata_path.write_text(json.dumps({"request": payload, "created": created}, indent=2), encoding="utf-8")

    deadline = time.time() + settings.seedance_poll_seconds
    latest: dict[str, Any] = created
    while time.time() < deadline:
        status_code, latest = ark_request_json("GET", f"/contents/generations/tasks/{task_id}")
        metadata_path.write_text(json.dumps({"request": payload, "created": created, "latest": latest}, indent=2), encoding="utf-8")
        if status_code < 200 or status_code >= 300:
            return demo_video_result(
                prompt,
                provider="Seedance 2.0 via BytePlus Ark",
                model=settings.seedance_model,
                task_id=task_id,
                fallback_reason=summarize_provider_error(latest),
                reference_image_url=reference_image_url,
                reference_image_role=reference_image_role,
            )
        status = str(latest.get("status") or latest.get("state") or "").lower()
        if status in {"succeeded", "success", "completed", "complete"}:
            video_url = extract_video_url(latest)
            if not video_url:
                return demo_video_result(
                    prompt,
                    provider="Seedance 2.0 via BytePlus Ark",
                    model=settings.seedance_model,
                    task_id=task_id,
                    fallback_reason="Seedance completed but the response did not include a video URL. Demo clip shown.",
                    reference_image_url=reference_image_url,
                    reference_image_role=reference_image_role,
                )
            path = download_video(video_url, output_dir, f"seedance-{task_id}.mp4")
            return {
                "video_url": f"/static/generated/videos/{path.name}",
                "provider": "Seedance 2.0 via BytePlus Ark",
                "model": settings.seedance_model,
                "status": "ready",
                "task_id": task_id,
                "live_provider_used": True,
                "fallback_reason": None,
                "duration_seconds": settings.seedance_duration_seconds,
                "ratio": settings.seedance_ratio,
                "resolution": settings.seedance_resolution,
                "prompt": prompt,
                "reference_image_url": reference_image_url,
                "reference_image_role": reference_image_role,
                "model_presentation": reference_presentation_from_prompt(prompt),
                "aws_ready_target": f"s3://retail-creative-videos/{path.name}",
                "cost_guardrail": "Generated one selected video only after the marketer clicked the button.",
            }
        if status in {"failed", "cancelled", "canceled", "expired"}:
            failure_reason = f"{latest.get('error', {}).get('code', '')}: {latest.get('error', {}).get('message', '')}"
            if status == "failed" and reference_image_role != "safety_retry" and is_output_video_policy_block(failure_reason):
                return generate_seedance_video(
                    privacy_safe_video_prompt(reference_safe_text_prompt(prompt)),
                    output_dir,
                    provider_reference_image=None,
                    reference_image_url=None,
                    reference_image_role="safety_retry",
                )
            return demo_video_result(
                prompt,
                provider="Seedance 2.0 via BytePlus Ark",
                model=settings.seedance_model,
                task_id=task_id,
                fallback_reason=f"Seedance task ended with status {status}. Demo clip shown.",
                reference_image_url=reference_image_url,
                reference_image_role=reference_image_role,
            )
        time.sleep(3)

    return demo_video_result(
        prompt,
        provider="Seedance 2.0 via BytePlus Ark",
        model=settings.seedance_model,
        task_id=task_id,
        status="processing",
        fallback_reason="Seedance job started but was still rendering during the demo window. Cached preview shown while it completes.",
        reference_image_url=reference_image_url,
        reference_image_role=reference_image_role,
    )


def generate_aws_nova_video(
    prompt: str,
    output_dir: Path,
    reference_image_url: str | None = None,
    reference_image_role: str = "reference_image",
) -> dict[str, Any]:
    if not settings.aws_nova_reel_s3_uri:
        return demo_video_result(
            prompt,
            provider="AWS Nova Reel",
            model=settings.aws_nova_reel_model,
            fallback_reason="AWS Nova Reel is selected, but AWS_NOVA_REEL_S3_URI is not configured. Demo clip shown.",
            reference_image_url=reference_image_url,
            reference_image_role=reference_image_role,
        )

    try:
        import boto3
    except ImportError:
        return demo_video_result(
            prompt,
            provider="AWS Nova Reel",
            model=settings.aws_nova_reel_model,
            fallback_reason="boto3 is not installed in this environment. Demo clip shown.",
            reference_image_url=reference_image_url,
            reference_image_role=reference_image_role,
        )

    model_input = {
        "taskType": "TEXT_VIDEO",
        "textToVideoParams": {"text": prompt},
        "videoGenerationConfig": {
            "durationSeconds": 6,
            "fps": 24,
            "dimension": "1280x720",
            "seed": int(datetime.now(timezone.utc).timestamp()) % 2147483647,
        },
    }
    try:
        client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        response = client.start_async_invoke(
            modelId=settings.aws_nova_reel_model,
            modelInput=model_input,
            outputDataConfig={"s3OutputDataConfig": {"s3Uri": settings.aws_nova_reel_s3_uri}},
        )
    except Exception as exc:
        return demo_video_result(
            prompt,
            provider="AWS Nova Reel",
            model=settings.aws_nova_reel_model,
            fallback_reason=f"AWS Nova Reel request was not started: {exc.__class__.__name__}. Demo clip shown.",
            reference_image_url=reference_image_url,
            reference_image_role=reference_image_role,
        )

    return demo_video_result(
        prompt,
        provider="AWS Nova Reel",
        model=settings.aws_nova_reel_model,
        task_id=response.get("invocationArn"),
        status="processing",
        fallback_reason="AWS Nova Reel async job started. Demo clip shown while Bedrock writes the result to S3.",
        aws_ready_target=settings.aws_nova_reel_s3_uri,
        reference_image_url=reference_image_url,
        reference_image_role=reference_image_role,
    )


def demo_video_result(
    prompt: str,
    provider: str | None = None,
    model: str | None = None,
    task_id: str | None = None,
    status: str = "demo_ready",
    fallback_reason: str = "Cached demo video shown.",
    aws_ready_target: str | None = None,
    reference_image_url: str | None = None,
    reference_image_role: str = "reference_image",
) -> dict[str, Any]:
    return {
        "video_url": DEMO_VIDEO_URL,
        "provider": provider or "Cached demo video",
        "model": model or "local-demo-mp4",
        "status": status,
        "task_id": task_id,
        "live_provider_used": False,
        "fallback_reason": fallback_reason,
        "duration_seconds": settings.seedance_duration_seconds,
        "ratio": settings.seedance_ratio,
        "resolution": settings.seedance_resolution,
        "prompt": prompt,
        "reference_image_url": reference_image_url,
        "reference_image_role": reference_image_role,
        "model_presentation": reference_presentation_from_prompt(prompt),
        "aws_ready_target": aws_ready_target or "s3://retail-creative-videos/demo-seedance-fashion.mp4",
        "cost_guardrail": "No live video cost was used for this fallback preview.",
    }


def video_presentation_instruction(brief: CampaignBrief) -> str:
    if brief.model_presentation == "male_model":
        return "adult male model, privacy-safe framing, face not emphasized, product and movement are the focus."
    if brief.model_presentation == "product_only":
        return "product-only motion using hanger, mannequin, flat lay, fabric movement, or close product detail; no person or face."
    return "adult female model, privacy-safe framing, face not emphasized, product and movement are the focus."


def reference_presentation_from_prompt(prompt: str) -> str:
    marker = "Model presentation: "
    if marker not in prompt:
        return "not_specified"
    return prompt.split(marker, 1)[1].split("Use natural motion", 1)[0].strip()


def provider_image_reference(reference_image_url: str | None, static_root: Path) -> str | None:
    if not reference_image_url:
        return None
    parsed = urlparse(reference_image_url)
    if parsed.scheme == "data":
        return reference_image_url
    if parsed.scheme in {"http", "https"} and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        return reference_image_url

    path = parsed.path if parsed.scheme else reference_image_url
    if not path.startswith("/static/"):
        return None
    local_path = static_root / path.removeprefix("/static/")
    if not local_path.is_file():
        return None

    mime_type = mimetypes.guess_type(local_path.name)[0] or "image/png"
    encoded = base64.b64encode(local_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def ark_request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    base = settings.seedance_base_url.rstrip("/")
    url = f"{base}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {settings.ark_api_key}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}


def extract_video_url(payload: dict[str, Any]) -> str | None:
    candidates: list[Any] = [
        payload.get("video_url"),
        payload.get("url"),
        payload.get("output"),
        payload.get("result"),
        payload.get("content"),
    ]
    if isinstance(payload.get("results"), list):
        candidates.extend(payload["results"])
    if isinstance(payload.get("data"), list):
        candidates.extend(payload["data"])

    for candidate in candidates:
        url = url_from_candidate(candidate)
        if url:
            return url
    return None


def url_from_candidate(candidate: Any) -> str | None:
    if isinstance(candidate, str) and candidate.startswith("http"):
        return candidate
    if isinstance(candidate, dict):
        for key in ("video_url", "url", "download_url"):
            value = candidate.get(key)
            if isinstance(value, str) and value.startswith("http"):
                return value
            if isinstance(value, dict):
                nested = url_from_candidate(value)
                if nested:
                    return nested
        for value in candidate.values():
            nested = url_from_candidate(value)
            if nested:
                return nested
    if isinstance(candidate, list):
        for item in candidate:
            nested = url_from_candidate(item)
            if nested:
                return nested
    return None


def download_video(video_url: str, output_dir: Path, filename: str | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / (filename or f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:10]}.mp4")
    request = urllib.request.Request(video_url, method="GET")
    with urllib.request.urlopen(request, timeout=180) as response:
        path.write_bytes(response.read())
    return path


def summarize_provider_error(payload: dict[str, Any]) -> str:
    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        code = error.get("code")
        message = error.get("message")
        if code and message:
            return f"{code}: {message}"
        if message:
            return str(message)
    if isinstance(payload, dict) and payload.get("raw"):
        return str(payload["raw"])[:240]
    return "Live video provider was not ready. Demo clip shown."


def is_reference_image_policy_block(message: str) -> bool:
    lowered = message.lower()
    return "inputimagesensitivecontentdetected" in lowered or "privacyinformation" in lowered


def is_output_video_policy_block(message: str) -> bool:
    lowered = message.lower()
    return "outputvideosensitivecontentdetected" in lowered or "sensitive" in lowered


def reference_safe_text_prompt(prompt: str) -> str:
    return (
        prompt.replace(
            "Use the provided reference image for the model, garment identity, styling, and opening frame. "
            "Keep the selected product visually consistent throughout the clip. ",
            "",
        )
        + " The visual reference image could not be sent to the video provider; recreate the same selected product from text direction only."
    )


def privacy_safe_video_prompt(prompt: str) -> str:
    return (
        f"{prompt} Privacy-safe rendering requirement: product-first fashion video, crop below the chin or show the model from behind/side, "
        "no clear face, no identifiable person, no close-up of eyes or facial details. Focus on the selected garment, fabric texture, "
        "construction details, silhouette, styling motion, and a clean bright retail lifestyle background."
    )
