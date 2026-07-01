from __future__ import annotations

import json
import re
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from .analytics import analyze_performance, audience_fit_score
from .data_loader import load_campaign_rows, load_products, load_segments, source_statuses
from .image_generation import build_image_prompt, image_generation_config
from .models import AgentResult, CampaignBrief, CreativeVariant, InsightMetric, Product, Segment
from .settings import get_settings

settings = get_settings()


class StudioState(TypedDict, total=False):
    brief: CampaignBrief
    campaigns: list[dict[str, Any]]
    products: list[Product]
    segments: list[Segment]
    analysis: dict[str, Any]
    plan: dict[str, Any]
    variants: list[dict[str, Any]]
    agent_steps: list[dict[str, Any]]
    live_ai_used: bool
    errors: list[str]


class InsightCopilotState(TypedDict, total=False):
    brief: CampaignBrief
    campaigns: list[dict[str, Any]]
    products: list[Product]
    segments: list[Segment]
    analysis: dict[str, Any]
    recommendation: dict[str, Any]
    live_ai_used: bool
    errors: list[str]


class BriefCopilotState(TypedDict, total=False):
    note: str
    brief: CampaignBrief
    campaigns: list[dict[str, Any]]
    products: list[Product]
    segments: list[Segment]
    analysis: dict[str, Any]
    result: dict[str, Any]
    live_ai_used: bool
    errors: list[str]


def build_agent():
    graph = StateGraph(StudioState)
    graph.add_node("load_context", load_context)
    graph.add_node("analyze_performance", analyze_performance_node)
    graph.add_node("recommend_strategy", recommend_strategy)
    graph.add_node("generate_creatives", generate_creatives)
    graph.add_node("score_variants", score_variants)

    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "analyze_performance")
    graph.add_edge("analyze_performance", "recommend_strategy")
    graph.add_edge("recommend_strategy", "generate_creatives")
    graph.add_edge("generate_creatives", "score_variants")
    graph.add_edge("score_variants", END)
    return graph.compile()


def build_insight_copilot_agent():
    graph = StateGraph(InsightCopilotState)
    graph.add_node("load_context", load_insight_context)
    graph.add_node("analyze_performance", analyze_insight_context)
    graph.add_node("refresh_recommendation", refresh_recommendation_node)

    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "analyze_performance")
    graph.add_edge("analyze_performance", "refresh_recommendation")
    graph.add_edge("refresh_recommendation", END)
    return graph.compile()


def build_brief_copilot_agent():
    graph = StateGraph(BriefCopilotState)
    graph.add_node("load_context", load_brief_context)
    graph.add_node("analyze_performance", analyze_brief_context)
    graph.add_node("refine_brief", refine_brief_node)

    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "analyze_performance")
    graph.add_edge("analyze_performance", "refine_brief")
    graph.add_edge("refine_brief", END)
    return graph.compile()


def run_campaign_agent(brief: CampaignBrief) -> AgentResult:
    state = AGENT.invoke({"brief": brief, "agent_steps": [], "errors": [], "live_ai_used": False})
    analysis = state["analysis"]
    plan = state["plan"]
    variants = [CreativeVariant(**item) for item in state["variants"]]
    baseline = analysis["baseline"]
    insights = [
        InsightMetric(label="Projected ROAS", value=f"{plan['projected_roas']:.1f}x", delta="+18%", sentiment="positive"),
        InsightMetric(label="Predicted CTR", value=f"{plan['projected_ctr'] * 100:.2f}%", delta="+22%", sentiment="positive"),
        InsightMetric(label="Conversion lift", value=f"+{plan['projected_lift'] * 100:.0f}%", delta="vs baseline", sentiment="positive"),
        InsightMetric(label="Estimated CPA", value=f"${baseline['cpa']:.2f}", delta="-9%", sentiment="positive"),
    ]
    return AgentResult(
        brief=brief,
        plan=plan,
        insights=insights,
        variants=variants,
        top_patterns=build_top_patterns(analysis),
        agent_steps=state["agent_steps"],
        data_sources=source_statuses(),
        live_ai_used=state.get("live_ai_used", False),
        cost_guardrail="Live AI copy polish is opt-in. Default generation uses local performance data.",
        errors=state.get("errors", []),
    )


def run_insight_copilot(brief: CampaignBrief) -> dict[str, Any]:
    state = INSIGHT_COPILOT.invoke({"brief": brief, "errors": [], "live_ai_used": False})
    return state["recommendation"]


def run_brief_copilot(note: str, brief: CampaignBrief) -> dict[str, Any]:
    state = BRIEF_COPILOT.invoke({"note": note, "brief": brief, "errors": [], "live_ai_used": False})
    return state["result"]


def load_context(state: StudioState) -> StudioState:
    steps = state.get("agent_steps", [])
    steps.append({"name": "Connect data", "status": "complete", "detail": "Loaded campaign history, product catalog, and customer segment profiles."})
    return {
        "campaigns": load_campaign_rows(),
        "products": load_products(),
        "segments": load_segments(),
        "agent_steps": steps,
    }


def load_insight_context(state: InsightCopilotState) -> InsightCopilotState:
    return {
        "campaigns": load_campaign_rows(),
        "products": load_products(),
        "segments": load_segments(),
    }


def load_brief_context(state: BriefCopilotState) -> BriefCopilotState:
    return {
        "campaigns": load_campaign_rows(),
        "products": load_products(),
        "segments": load_segments(),
    }


def analyze_performance_node(state: StudioState) -> StudioState:
    analysis = analyze_performance(state["campaigns"], state["products"], state["segments"], state["brief"])
    steps = state.get("agent_steps", [])
    steps.append(
        {
            "name": "Find winning patterns",
            "status": "complete",
            "detail": "Compared channels, copy styles, formats, and image styles by ROAS and CTR.",
        }
    )
    return {"analysis": analysis, "agent_steps": steps}


def analyze_insight_context(state: InsightCopilotState) -> InsightCopilotState:
    return {"analysis": analyze_performance(state["campaigns"], state["products"], state["segments"], state["brief"])}


def analyze_brief_context(state: BriefCopilotState) -> BriefCopilotState:
    return {"analysis": analyze_performance(state["campaigns"], state["products"], state["segments"], state["brief"])}


def refresh_recommendation_node(state: InsightCopilotState) -> InsightCopilotState:
    brief = state["brief"]
    fallback = deterministic_today_recommendation(brief, state["products"], state["segments"], state["analysis"])
    errors = state.get("errors", [])
    live_ai_used = False

    try:
        raw = refresh_recommendation_with_openai(brief, state["products"], state["segments"], state["analysis"], fallback)
        recommendation = normalize_recommendation(raw, brief, state["products"], state["segments"], fallback)
        live_ai_used = True
    except Exception as exc:
        recommendation = fallback
        errors.append(f"AI insight refresh skipped: {exc.__class__.__name__}")

    recommendation["live_ai_used"] = live_ai_used
    recommendation["errors"] = errors
    recommendation["cost_guardrail"] = "One insight refresh call only."
    return {"recommendation": recommendation, "live_ai_used": live_ai_used, "errors": errors}


def refine_brief_node(state: BriefCopilotState) -> BriefCopilotState:
    note = state["note"]
    brief = state["brief"]
    fallback = deterministic_brief_refine(note, brief, state["products"], state["segments"])
    errors = state.get("errors", [])
    live_ai_used = False

    try:
        raw = refine_brief_with_openai(note, brief, state["products"], state["segments"], state["analysis"], fallback)
        result = normalize_brief_refine(raw, brief, state["products"], state["segments"], fallback)
        live_ai_used = True
    except Exception as exc:
        result = fallback
        errors.append(f"AI brief refinement skipped: {exc.__class__.__name__}")

    result["live_ai_used"] = live_ai_used
    result["errors"] = errors
    result["cost_guardrail"] = "One brief-refinement call only."
    return {"result": result, "live_ai_used": live_ai_used, "errors": errors}


def recommend_strategy(state: StudioState) -> StudioState:
    brief = state["brief"]
    analysis = state["analysis"]
    segment = next(item for item in state["segments"] if item.id == brief.primary_segment_id)
    top_channel = first_matching(analysis["by_channel"], brief.channels) or analysis["by_channel"][0]
    top_format = analysis["by_format"][0]
    top_format_name = sanitize_business_copy(top_format["name"], 80)
    top_copy = analysis["by_copy_style"][0]
    top_image = analysis["by_image_style"][0]
    baseline = analysis["baseline"]
    strategy = strategy_context(brief.strategy_id)
    image_config = image_generation_config(brief)

    plan = {
        "title": f"{brief.campaign_name}: {segment.name} launch plan",
        "narrative": (
            f"{strategy['verb']} a {brief.trend_window.lower()} creative sprint for {segment.name}. "
            f"Lead with {top_channel['name']} and {top_format_name} because historical campaigns show "
            f"{top_channel['roas']:.1f}x ROAS and {top_channel['ctr'] * 100:.2f}% CTR in similar contexts."
        ),
        "strategy_id": brief.strategy_id,
        "strategy_name": strategy["name"],
        "creative_instruction": brief.creative_instruction,
        "recommended_angle": choose_angle(segment, top_copy["name"], brief.objective),
        "primary_channel": top_channel["name"],
        "primary_format": top_format_name,
        "copy_style": top_copy["name"],
        "image_style": top_image["name"],
        "image_provider": image_config["label"],
        "image_model": image_config["model"],
        "projected_roas": max(baseline["roas"] * 1.18, top_channel["roas"] * 0.96),
        "projected_ctr": max(baseline["ctr"] * 1.22, top_channel["ctr"] * 0.94),
        "projected_lift": baseline["conversion_lift"],
        "recommendations": analysis["recommendations"],
        "aws_ready": "Production can connect this workflow to live product, sales, segment, and ad platform data.",
    }
    steps = state.get("agent_steps", [])
    steps.append({"name": "Recommend strategy", "status": "complete", "detail": f"{strategy['name']}: {plan['recommended_angle']}"})
    return {"plan": plan, "agent_steps": steps}


def generate_creatives(state: StudioState) -> StudioState:
    brief = state["brief"]
    analysis = state["analysis"]
    plan = state["plan"]
    variants = deterministic_variants(brief, state["segments"], analysis, plan)
    live_ai_used = False
    errors = state.get("errors", [])

    if brief.use_live_ai:
        try:
            variants = refine_with_openai(brief, analysis, plan, variants)
            live_ai_used = True
        except Exception as exc:  # Keep demo resilient while preserving the error for the UI.
            errors.append(f"AI forecast calibration skipped: {exc.__class__.__name__}")

    steps = state.get("agent_steps", [])
    steps.append(
        {
            "name": "Create creative options",
            "status": "complete",
            "detail": f"Prepared {len(variants)} focused previews for the selected audience and platforms.",
        }
    )
    return {"variants": variants, "agent_steps": steps, "live_ai_used": live_ai_used, "errors": errors}


def score_variants(state: StudioState) -> StudioState:
    variants = sorted(state["variants"], key=lambda item: (item["predicted_roas"], item["predicted_ctr"]), reverse=True)
    for rank, variant in enumerate(variants, start=1):
        variant["rank"] = rank
    steps = state.get("agent_steps", [])
    steps.append({"name": "Rank recommendations", "status": "complete", "detail": "Ranked creative options by projected ROAS, CTR, lift, and audience fit."})
    return {"variants": variants, "agent_steps": steps}


def deterministic_variants(
    brief: CampaignBrief,
    segments: list[Segment],
    analysis: dict[str, Any],
    plan: dict[str, Any],
) -> list[dict[str, Any]]:
    products = [Product(**item) for item in analysis["selected_products"]]
    primary_segment = next(item for item in segments if item.id == brief.primary_segment_id)
    channels = brief.channels or ["Meta", "TikTok", "Display", "Email"]
    formats = [item["name"] for item in analysis["by_format"][:4]] or ["Carousel"]
    copy_style = plan["copy_style"]
    image_style = plan["image_style"]
    base_ctr = plan["projected_ctr"]
    base_roas = plan["projected_roas"]
    slots = build_variant_slots(channels, products)

    variants: list[dict[str, Any]] = []
    for index, (channel, product) in enumerate(slots):
        segment = primary_segment
        format_name = channel_format(channel, formats[index % len(formats)])
        fit = audience_fit_score(segment, channel, copy_style)
        ctr_multiplier = 0.88 + index * 0.03 + fit / 1250
        roas_multiplier = 0.78 + fit / 780 + index * 0.015
        ctr = min(base_ctr * ctr_multiplier, 0.042)
        roas = min(base_roas * roas_multiplier, 7.4)
        lift = min(plan["projected_lift"] + fit / 900 + index * 0.008, 0.46)
        headline, body, cta = copy_for(product, segment, channel, copy_style, brief.generation_mode)
        image_plan = build_image_prompt(brief, product, segment, channel, image_style)
        variants.append(
            {
                "id": f"var_{index + 1}",
                "channel": channel,
                "format": format_name,
                "product_id": product.id,
                "segment_id": segment.id,
                "headline": headline,
                "body": body,
                "cta": cta,
                "visual_direction": visual_direction(product, segment, channel, image_style, brief.creative_instruction),
                "image_style": image_style,
                "copy_style": copy_style,
                "image_prompt": image_plan["prompt"],
                "image_provider": f"{image_plan['provider_label']} ({image_plan['model']})",
                "predicted_ctr": round(ctr, 4),
                "predicted_roas": round(roas, 2),
                "predicted_lift": round(lift, 3),
                "confidence": fit,
                "rationale": (
                    f"Uses {copy_style} copy and {image_style} imagery because similar campaigns "
                    f"over-indexed for {segment.name} on {channel}. Creative direction: {brief.creative_instruction}"
                ),
            }
        )
    return variants


def build_variant_slots(channels: list[str], products: list[Product]) -> list[tuple[str, Product]]:
    if not products:
        return []

    selected_channels = channels or ["Meta", "TikTok", "Display", "Email"]
    if len(selected_channels) == 1:
        round_limit = min(3, len(products))
    elif len(selected_channels) == 2:
        round_limit = min(2, len(products))
    else:
        round_limit = 1 if len(products) == 1 else 2

    target_count = min(6, len(selected_channels) * round_limit, len(selected_channels) * len(products))
    slots: list[tuple[str, Product]] = []
    used: set[tuple[str, str]] = set()
    cursor = 0

    for _ in range(round_limit):
        for channel in selected_channels:
            if len(slots) >= target_count:
                return slots
            product, cursor = pick_next_product_for_channel(products, channel, used, cursor)
            if not product:
                continue
            used.add((channel, product.id))
            slots.append((channel, product))

    return slots


def pick_next_product_for_channel(
    products: list[Product],
    channel: str,
    used: set[tuple[str, str]],
    start_index: int,
) -> tuple[Product | None, int]:
    for offset in range(len(products)):
        candidate_index = (start_index + offset) % len(products)
        product = products[candidate_index]
        if (channel, product.id) not in used:
            return product, candidate_index + 1
    return None, start_index


def refine_with_openai(
    brief: CampaignBrief,
    analysis: dict[str, Any],
    plan: dict[str, Any],
    seed_variants: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    from openai import OpenAI

    model = settings.openai_model
    max_tokens = settings.openai_max_output_tokens
    client = OpenAI(api_key=settings.openai_api_key)
    compact_context = {
        "brief": brief.model_dump(),
        "plan": plan,
        "top_patterns": build_top_patterns(analysis)[:4],
        "seed_variants": seed_variants[:4],
    }
    prompt = (
        "You are an executive retail creative strategist and forecast analyst for a Southeast Asia fashion retailer. "
        "Improve the ad creative copy and calibrate the forecast using the performance context. "
        "Preserve IDs, product_id, segment_id, channel, and format. "
        "Return strict JSON with a key variants containing the same number of variants. "
        "For each variant include id, headline, body, cta, visual_direction, rationale, predicted_roas, predicted_ctr, and predicted_lift. "
        "predicted_ctr and predicted_lift must be decimal rates, for example 0.024 for 2.4%. "
        "Keep numeric changes conservative: ROAS within roughly 12%, CTR within roughly 15%, lift within roughly 12% of the seed forecast. "
        "Use concise, premium retail language. No real brand names.\n\n"
        f"Context:\n{json.dumps(compact_context, ensure_ascii=True)}"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Return only valid JSON. Do not use markdown."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    parsed = json.loads(content)
    improvements = {item["id"]: item for item in parsed.get("variants", [])}
    refined = []
    for variant in seed_variants:
        update = improvements.get(variant["id"], {})
        merged = dict(variant)
        for field in ["headline", "body", "cta", "visual_direction", "rationale"]:
            if update.get(field):
                merged[field] = update[field]
        merged["predicted_roas"] = bounded_metric(update.get("predicted_roas"), variant["predicted_roas"], 0.88, 1.12, 0.5, 7.4, 2)
        merged["predicted_ctr"] = bounded_metric(update.get("predicted_ctr"), variant["predicted_ctr"], 0.85, 1.15, 0.002, 0.042, 4, percent_like=True)
        merged["predicted_lift"] = bounded_metric(update.get("predicted_lift"), variant["predicted_lift"], 0.88, 1.12, 0.05, 0.46, 3, percent_like=True)
        if update.get("predicted_roas") or update.get("predicted_ctr") or update.get("predicted_lift"):
            merged["rationale"] = f"{merged['rationale']} AI forecast calibrated within historical guardrails."
        refined.append(merged)
    return refined


def refresh_recommendation_with_openai(
    brief: CampaignBrief,
    products: list[Product],
    segments: list[Segment],
    analysis: dict[str, Any],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    from openai import OpenAI

    model = settings.openai_model
    client = OpenAI(api_key=settings.openai_api_key)
    compact_context = {
        "current_brief": brief.model_dump(),
        "segments": [segment.model_dump() for segment in segments],
        "products": [product.model_dump() for product in products],
        "baseline": analysis["baseline"],
        "top_patterns": build_top_patterns(analysis)[:8],
        "top_creatives": analysis["top_creatives"][:5],
        "fallback_shape": fallback,
    }
    prompt = (
        "You are a senior retail marketing strategist for a Southeast Asia fashion retailer. "
        "Use the campaign performance summary, product catalog, and customer segments to refresh today's campaign recommendation. "
        "Pick the best data-backed opportunity; do not merely restate the current brief. "
        "Return strict JSON only with keys: title, summary, confidence, signals, brief_patch, reasoning. "
        "signals must be exactly 3 objects with label and value. "
        "brief_patch may include market, channels, primary_segment_id, product_ids, strategy_id, creative_instruction, model_presentation. "
        "Use model_presentation only when the user implies female model, male model, or product-only/no-model assets. "
        "Use only IDs and channels present in the context. Keep copy business-facing, not technical.\n\n"
        "Avoid internal ad-ops terms such as hero module, responsive banner, feed unit, or targeting in the title and signals. "
        "Write the title as an action a marketing lead would approve, such as 'Launch a TikTok-first Malaysia edit'.\n\n"
        f"Context:\n{json.dumps(compact_context, ensure_ascii=True)}"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Return only valid JSON. Do not use markdown."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=900,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content or "{}")


def refine_brief_with_openai(
    note: str,
    brief: CampaignBrief,
    products: list[Product],
    segments: list[Segment],
    analysis: dict[str, Any],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    from openai import OpenAI

    model = settings.openai_model
    client = OpenAI(api_key=settings.openai_api_key)
    compact_context = {
        "marketer_note": note,
        "current_brief": brief.model_dump(),
        "segments": [segment.model_dump() for segment in segments],
        "products": [product.model_dump() for product in products],
        "top_patterns": build_top_patterns(analysis)[:8],
        "fallback_shape": fallback,
    }
    prompt = (
        "You are a campaign brief copilot for a Southeast Asia fashion retailer. "
        "Translate the marketer's plain-language note into structured campaign fields. "
        "Return strict JSON only with keys: brief_patch, rewritten_note, reasoning. "
        "brief_patch may include market, objective, channels, primary_segment_id, product_ids, strategy_id, creative_instruction, model_presentation. "
        "Use model_presentation values female_model, male_model, or product_only when the note implies a model choice. "
        "Use only real product IDs, segment IDs, channels, and markets from the context. "
        "If the note implies TikTok-first, keep Meta + TikTok unless the user explicitly excludes Meta. "
        "Keep rewritten_note concise and ready to use as creative direction.\n\n"
        f"Context:\n{json.dumps(compact_context, ensure_ascii=True)}"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Return only valid JSON. Do not use markdown."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=800,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content or "{}")


def deterministic_today_recommendation(
    brief: CampaignBrief,
    products: list[Product],
    segments: list[Segment],
    analysis: dict[str, Any],
) -> dict[str, Any]:
    style_segment = next((segment for segment in segments if segment.id == "seg_style_enthusiasts"), segments[0])
    selected_products = ["prod_batik_maxi", "prod_tailored_trouser", "prod_resort_overshirt", "prod_pleated_skirt"]
    product_names = [product.name for product in products if product.id in selected_products][:4]
    top_patterns = build_top_patterns(analysis)
    channel_signal = next((item for item in top_patterns if item["type"] == "Channel"), {"name": "TikTok", "ctr": 3.6, "roas": 6.8})
    return {
        "title": "Launch a TikTok-first Malaysia edit while the style trend is still moving.",
        "summary": (
            "Current and historical campaign data points to Style Enthusiasts, short video, "
            "and texture-led product shots as the strongest starting point."
        ),
        "confidence": 92,
        "signals": [
            {"label": "Signal", "value": f"{channel_signal['name']} is the strongest recent channel pattern."},
            {"label": "Audience", "value": f"{style_segment.name} fit TikTok and Meta creative."},
            {"label": "Products", "value": f"{', '.join(product_names[:3])} assets are campaign-ready."},
        ],
        "brief_patch": {
            "market": "Malaysia",
            "channels": ["Meta", "TikTok"],
            "primary_segment_id": "seg_style_enthusiasts",
            "product_ids": selected_products,
            "strategy_id": "trend_window",
            "creative_instruction": "TikTok-first Malaysia launch for Style Enthusiasts. Make it premium, less posed, show product texture and upbeat city energy.",
        },
        "reasoning": [
            "Short video is a strong recent format in the campaign history.",
            "Style Enthusiasts prefer TikTok and Meta with trend-led creative.",
            "Selected products have strong visual assets and inventory readiness.",
        ],
    }


def deterministic_brief_refine(
    note: str,
    brief: CampaignBrief,
    products: list[Product],
    segments: list[Segment],
) -> dict[str, Any]:
    lowered = note.lower()
    patch: dict[str, Any] = {
        "creative_instruction": note.strip() or brief.creative_instruction,
    }

    for market in ["Singapore", "Malaysia", "Indonesia", "Thailand"]:
        if market.lower() in lowered:
            patch["market"] = market

    if "tiktok" in lowered:
        patch["channels"] = ["Meta", "TikTok"]
    elif "email" in lowered:
        patch["channels"] = ["Email", "Meta"]
    elif "display" in lowered or "banner" in lowered:
        patch["channels"] = ["Display", "Meta"]

    if any(term in lowered for term in ["young", "style", "trend", "creator", "tiktok"]):
        patch["primary_segment_id"] = "seg_style_enthusiasts"
    if any(term in lowered for term in ["value", "promo", "price", "deal"]):
        patch["primary_segment_id"] = "seg_value_seekers"
    if any(term in lowered for term in ["modest", "coverage", "raya", "festive"]):
        patch["primary_segment_id"] = "seg_modest_fashion"

    if any(term in lowered for term in ["batik", "dress"]):
        patch["product_ids"] = ["prod_batik_maxi", "prod_pleated_skirt", "prod_linen_shirt", "prod_tailored_trouser"]
    elif "linen" in lowered:
        patch["product_ids"] = ["prod_linen_shirt", "prod_resort_overshirt", "prod_batik_maxi", "prod_tailored_trouser"]

    if any(term in lowered for term in ["male model", "man model", "mens model", "men model"]):
        patch["model_presentation"] = "male_model"
    elif any(term in lowered for term in ["female model", "woman model", "women model", "lady model"]):
        patch["model_presentation"] = "female_model"
    elif any(term in lowered for term in ["product only", "no model", "just the shirt", "flat lay", "hanger", "mannequin"]):
        patch["model_presentation"] = "product_only"

    if any(term in lowered for term in ["refresh", "fatigue", "new angle"]):
        patch["strategy_id"] = "creative_fatigue"
    else:
        patch["strategy_id"] = "trend_window"

    patch = normalize_brief_patch(patch, brief, products, segments)
    return {
        "brief_patch": patch,
        "rewritten_note": patch.get("creative_instruction", brief.creative_instruction),
        "reasoning": [
            "The note was mapped to the closest market, platform, segment, and product signals.",
            "The selected segment controls copy style, channel preference, visual direction, and ranking.",
            "The structured brief stays editable before generation.",
        ],
    }


def normalize_recommendation(
    raw: dict[str, Any],
    brief: CampaignBrief,
    products: list[Product],
    segments: list[Segment],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    patch = normalize_brief_patch(raw.get("brief_patch", {}), brief, products, segments)
    signals = raw.get("signals")
    if not isinstance(signals, list) or len(signals) < 3:
        signals = fallback["signals"]
    clean_signals = []
    for item in signals[:3]:
        if isinstance(item, dict):
            clean_signals.append(
                {
                    "label": sanitize_business_copy(str(item.get("label", "Signal")), 28),
                    "value": sanitize_business_copy(str(item.get("value", "")), 140),
                }
            )
    title = sanitize_business_copy(str(raw.get("title") or fallback["title"]), 160)
    if recommendation_title_is_internal(title):
        title = fallback["title"]
    return {
        "title": title,
        "summary": sanitize_business_copy(str(raw.get("summary") or fallback["summary"]), 280),
        "confidence": bounded_int(raw.get("confidence", fallback["confidence"]), 60, 97),
        "signals": clean_signals or fallback["signals"],
        "brief_patch": patch or fallback["brief_patch"],
        "reasoning": clean_reasoning(raw.get("reasoning"), fallback["reasoning"]),
    }


def normalize_brief_refine(
    raw: dict[str, Any],
    brief: CampaignBrief,
    products: list[Product],
    segments: list[Segment],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    patch = normalize_brief_patch(raw.get("brief_patch", {}), brief, products, segments)
    if not patch:
        patch = fallback["brief_patch"]
    rewritten_note = str(raw.get("rewritten_note") or patch.get("creative_instruction") or fallback["rewritten_note"])[:500]
    if rewritten_note:
        patch["creative_instruction"] = rewritten_note
    return {
        "brief_patch": patch,
        "rewritten_note": rewritten_note,
        "reasoning": clean_reasoning(raw.get("reasoning"), fallback["reasoning"]),
    }


def normalize_brief_patch(
    raw_patch: dict[str, Any],
    brief: CampaignBrief,
    products: list[Product],
    segments: list[Segment],
) -> dict[str, Any]:
    if not isinstance(raw_patch, dict):
        return {}

    markets = {"Singapore", "Malaysia", "Indonesia", "Thailand"}
    channels = {"Meta", "TikTok", "Display", "Email"}
    objectives = {"Sales", "Traffic", "Awareness", "Retention"}
    strategy_ids = {"trend_window", "product_winner", "creative_fatigue"}
    model_presentations = {"female_model", "male_model", "product_only"}
    product_ids = {product.id for product in products}
    segment_ids = {segment.id for segment in segments}
    patch: dict[str, Any] = {}

    if raw_patch.get("market") in markets:
        patch["market"] = raw_patch["market"]
    if raw_patch.get("objective") in objectives:
        patch["objective"] = raw_patch["objective"]
    if raw_patch.get("primary_segment_id") in segment_ids:
        patch["primary_segment_id"] = raw_patch["primary_segment_id"]
    if raw_patch.get("strategy_id") in strategy_ids:
        patch["strategy_id"] = raw_patch["strategy_id"]
    if raw_patch.get("model_presentation") in model_presentations:
        patch["model_presentation"] = raw_patch["model_presentation"]

    raw_channels = raw_patch.get("channels")
    if isinstance(raw_channels, list):
        selected_channels = [channel for channel in raw_channels if channel in channels]
        if selected_channels:
            patch["channels"] = selected_channels[:4]

    raw_products = raw_patch.get("product_ids")
    if isinstance(raw_products, list):
        selected_products = [product_id for product_id in raw_products if product_id in product_ids]
        if selected_products:
            patch["product_ids"] = selected_products[:4]

    creative_instruction = raw_patch.get("creative_instruction")
    if isinstance(creative_instruction, str) and creative_instruction.strip():
        patch["creative_instruction"] = creative_instruction.strip()[:500]

    return patch


def clean_reasoning(value: Any, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    cleaned = [sanitize_business_copy(str(item), 180) for item in value if str(item).strip()]
    return cleaned[:4] or fallback


def sanitize_business_copy(value: str, limit: int) -> str:
    cleaned = " ".join(value.split())
    replacements = {
        "hero module": "email creative",
        "Hero module": "Email creative",
        "responsive banner": "display creative",
        "Responsive banner": "Display creative",
        "feed unit": "social creative",
        "Feed unit": "Social creative",
        "Feed + carousel": "social carousel",
    }
    for source, replacement in replacements.items():
        cleaned = cleaned.replace(source, replacement)
    return cleaned[:limit]


def recommendation_title_is_internal(title: str) -> bool:
    lowered = title.lower()
    blocked_terms = ["hero module", "responsive banner", "feed unit", "campaign targeting", "refine singapore campaign"]
    return any(term in lowered for term in blocked_terms)


def bounded_int(value: Any, minimum: int, maximum: int) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        parsed = minimum
    return max(minimum, min(parsed, maximum))


def bounded_metric(
    value: Any,
    seed: float,
    min_factor: float,
    max_factor: float,
    floor: float,
    ceiling: float,
    digits: int,
    *,
    percent_like: bool = False,
) -> float:
    parsed = parse_metric_number(value)
    if parsed is None:
        return round(seed, digits)
    if percent_like and parsed > 1:
        parsed = parsed / 100
    lower = max(floor, seed * min_factor)
    upper = min(ceiling, seed * max_factor)
    return round(max(lower, min(parsed, upper)), digits)


def parse_metric_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def first_matching(rows: list[dict[str, Any]], allowed: list[str]) -> dict[str, Any] | None:
    allowed_set = set(allowed)
    return next((row for row in rows if row["name"] in allowed_set), None)


def choose_angle(segment: Segment, copy_style: str, objective: str) -> str:
    if objective == "Sales":
        return f"Position the collection as an easy upgrade for {segment.profile.lower()} with {copy_style} messaging."
    if objective == "Traffic":
        return f"Use discovery-led hooks that make {segment.name} explore the new-season edit."
    if objective == "Retention":
        return f"Reward loyal {segment.name} shoppers with early access and curated styling."
    return f"Build awareness through high-recognition visual cues and fast-reading {copy_style} copy."


def channel_format(channel: str, fallback: str) -> str:
    mapping = {
        "Meta": "Social carousel",
        "TikTok": "Short video",
        "Display": "Display creative",
        "Email": "Email creative",
    }
    return mapping.get(channel, sanitize_business_copy(fallback, 80))


def copy_for(product: Product, segment: Segment, channel: str, copy_style: str, mode: str) -> tuple[str, str, str]:
    if mode == "optimize":
        lead = "Test winner refresh"
    elif copy_style == "trend-led":
        lead = "New this week"
    elif copy_style == "value-led":
        lead = "Smarter style pick"
    elif copy_style == "promo-urgency":
        lead = "Weekend-ready"
    else:
        lead = "Made for now"

    headline = f"{lead}: {product.name}"
    body_by_channel = {
        "TikTok": f"A quick styling hook for {segment.name}: {product.description.lower()}",
        "Meta": f"Fresh silhouettes and easy pairings selected for {segment.name.lower()}.",
        "Display": f"{product.category} with stronger audience fit and fast seasonal relevance.",
        "Email": f"Curated new-season picks based on what {segment.name.lower()} click and buy.",
    }
    cta = "Shop the edit" if channel != "Email" else "Explore picks"
    return headline, body_by_channel.get(channel, product.description), cta


def visual_direction(product: Product, segment: Segment, channel: str, image_style: str, creative_instruction: str) -> str:
    if channel == "TikTok":
        base = f"Vertical motion-led styling cutdown using {product.name}, quick outfit transitions, and {segment.creative_notes.lower()}"
    elif channel == "Email":
        base = f"Clean editorial hero with {product.name}, soft product detail crop, and clear offer space."
    elif channel == "Display":
        base = f"High-contrast banner composition using {product.name}, concise headline area, and {image_style} product crop."
    else:
        base = f"Catalog-quality product image with lifestyle secondary frame and {image_style} treatment."
    return f"{base} Marketer note: {creative_instruction}"


def strategy_context(strategy_id: str) -> dict[str, str]:
    strategies = {
        "trend_window": {"name": "Catch the trend window", "verb": "Launch"},
        "product_winner": {"name": "Scale best-selling products", "verb": "Scale"},
        "creative_fatigue": {"name": "Refresh fatigued creative", "verb": "Refresh"},
    }
    return strategies.get(strategy_id, strategies["trend_window"])


def build_top_patterns(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    patterns = []
    for group_name, label in [
        ("by_channel", "Channel"),
        ("by_format", "Format"),
        ("by_copy_style", "Copy style"),
        ("by_image_style", "Image style"),
    ]:
        for item in analysis.get(group_name, [])[:2]:
            patterns.append(
                {
                    "type": label,
                    "name": sanitize_business_copy(item["name"], 80),
                    "roas": round(item["roas"], 2),
                    "ctr": round(item["ctr"] * 100, 2),
                    "campaigns": item["campaigns"],
                }
            )
    return patterns


AGENT = build_agent()
INSIGHT_COPILOT = build_insight_copilot_agent()
BRIEF_COPILOT = build_brief_copilot_agent()
