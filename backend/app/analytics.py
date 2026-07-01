from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from .models import CampaignBrief, Product, Segment


def enrich_campaign(row: dict[str, Any]) -> dict[str, Any]:
    impressions = max(float(row["impressions"]), 1.0)
    clicks = float(row["clicks"])
    conversions = float(row["conversions"])
    spend = max(float(row["spend_sgd"]), 1.0)
    revenue = float(row["revenue_sgd"])
    enriched = dict(row)
    enriched["ctr"] = clicks / impressions
    enriched["cvr"] = conversions / max(clicks, 1.0)
    enriched["roas"] = revenue / spend
    enriched["cpa"] = spend / max(conversions, 1.0)
    return enriched


def summarize_group(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[key])].append(row)

    summaries = []
    for value, group_rows in groups.items():
        summaries.append(
            {
                "name": value,
                "campaigns": len(group_rows),
                "ctr": mean(item["ctr"] for item in group_rows),
                "roas": mean(item["roas"] for item in group_rows),
                "cvr": mean(item["cvr"] for item in group_rows),
                "spend_sgd": sum(float(item["spend_sgd"]) for item in group_rows),
                "revenue_sgd": sum(float(item["revenue_sgd"]) for item in group_rows),
            }
        )
    return sorted(summaries, key=lambda item: (item["roas"], item["ctr"]), reverse=True)


def business_format_name(name: str) -> str:
    mapping = {
        "Hero module": "Email creative",
        "Responsive banner": "Display creative",
        "Feed + carousel": "Social carousel",
        "Short video script": "Short video",
    }
    return mapping.get(name, name)


def analyze_performance(
    campaigns: list[dict[str, Any]],
    products: list[Product],
    segments: list[Segment],
    brief: CampaignBrief,
) -> dict[str, Any]:
    enriched = [enrich_campaign(row) for row in campaigns]
    selected_segment_ids = {brief.primary_segment_id}
    if brief.additional_segment_id:
        selected_segment_ids.add(brief.additional_segment_id)

    relevant = [
        row
        for row in enriched
        if row["market"] == brief.market
        or row["segment_id"] in selected_segment_ids
        or row["channel"] in brief.channels
    ]
    relevant = relevant or enriched

    selected_products = products_for_brief(products, campaigns, brief, relevant)
    selected_product_ids = {product.id for product in selected_products}
    product_rows = [row for row in relevant if row["product_id"] in selected_product_ids] or relevant

    by_channel = summarize_group(product_rows, "channel")
    by_format = summarize_group(product_rows, "format")
    by_copy_style = summarize_group(product_rows, "copy_style")
    by_image_style = summarize_group(product_rows, "image_style")
    by_segment = summarize_group(product_rows, "segment_id")

    top_rows = sorted(product_rows, key=lambda row: (row["roas"], row["ctr"]), reverse=True)[:5]
    baseline_ctr = mean(row["ctr"] for row in product_rows)
    baseline_roas = mean(row["roas"] for row in product_rows)
    baseline_cpa = mean(row["cpa"] for row in product_rows)

    return {
        "selected_products": [product.model_dump() for product in selected_products],
        "selected_segments": [
            segment.model_dump()
            for segment in segments
            if segment.id in selected_segment_ids or segment.id == brief.primary_segment_id
        ],
        "baseline": {
            "ctr": baseline_ctr,
            "roas": baseline_roas,
            "cpa": baseline_cpa,
            "conversion_lift": 0.18 + min(baseline_roas / 30, 0.12),
        },
        "by_channel": by_channel,
        "by_format": by_format,
        "by_copy_style": by_copy_style,
        "by_image_style": by_image_style,
        "by_segment": by_segment,
        "top_creatives": top_rows,
        "recommendations": build_recommendations(by_channel, by_format, by_copy_style, by_image_style),
    }


def build_insight_engine(
    campaigns: list[dict[str, Any]],
    products: list[Product],
    segments: list[Segment],
    brief: CampaignBrief,
) -> dict[str, Any]:
    analysis = analyze_performance(campaigns, products, segments, brief)
    channel = analysis["by_channel"][0]
    format_row = analysis["by_format"][0]
    format_name = business_format_name(format_row["name"])
    copy_style = analysis["by_copy_style"][0]
    image_style = analysis["by_image_style"][0]
    baseline = analysis["baseline"]
    top_product = Product(**analysis["selected_products"][0])
    primary_segment = next((segment for segment in segments if segment.id == brief.primary_segment_id), segments[0])

    return {
        "last_refresh": "15 min ago",
        "cadence": "Every 15 min when connected to ad platforms",
        "next_refresh": "In 11 min",
        "summary": (
            "The engine scores recent campaign performance, catalog readiness, and segment fit, "
            "then proposes a starting strategy before the marketer briefs the campaign."
        ),
        "baseline": {
            "roas": round(baseline["roas"], 1),
            "ctr": round(baseline["ctr"] * 100, 2),
            "cpa": round(baseline["cpa"], 2),
        },
        "cards": [
            {
                "id": "trend_window",
                "title": "Catch the trend window",
                "tag": "Recommended",
                "recommendation": f"Start with {channel['name']} because it is the strongest performance signal, then adapt the concept across selected platforms.",
                "expected_gain": "+28% conversion lift",
                "confidence": 92,
                "evidence": [
                    f"{channel['name']} is leading at {channel['roas']:.1f}x ROAS.",
                    f"{format_name} is the strongest creative format at {format_row['ctr'] * 100:.2f}% CTR.",
                    f"{primary_segment.name} is a {primary_segment.size_millions:.1f}M audience across {', '.join(primary_segment.markets[:2])}.",
                ],
                "brief_hint": "Move fast with trend-led hooks, readable product shots, and two TikTok-style variants.",
            },
            {
                "id": "product_winner",
                "title": "Scale best-selling products",
                "tag": "Sales lift",
                "recommendation": f"Lead with {top_product.name} and adjacent catalog pieces with high inventory readiness.",
                "expected_gain": "+18% ROAS vs baseline",
                "confidence": min(96, max(76, top_product.inventory_score)),
                "evidence": [
                    f"{top_product.name} has {top_product.inventory_score}/100 inventory readiness.",
                    f"Margin signal is {top_product.margin * 100:.0f}%, useful for paid media scaling.",
                    f"Use {image_style['name']} visuals because that style is over-indexing.",
                ],
                "brief_hint": "Prioritize full-product visibility, soft editorial lighting, and clear shop CTA.",
            },
            {
                "id": "creative_fatigue",
                "title": "Refresh fatigued creative",
                "tag": "Optimization",
                "recommendation": "Keep the winning audience, but change pose, crop, and copy angle for the next iteration.",
                "expected_gain": "-9% estimated CPA",
                "confidence": 84,
                "evidence": [
                    "Similar campaigns improved when format and image style changed together.",
                    f"{copy_style['name']} copy is still performing, so refresh the visual before changing the offer.",
                    "Use one polished variant first to keep demo generation fast.",
                ],
                "brief_hint": "Less posed model, more natural movement, cleaner background, stronger product detail.",
            },
        ],
    }


def products_for_brief(
    products: list[Product],
    campaigns: list[dict[str, Any]],
    brief: CampaignBrief,
    relevant_rows: list[dict[str, Any]],
) -> list[Product]:
    if brief.product_ids:
        selected = [product for product in products if product.id in set(brief.product_ids)]
        if selected:
            return selected[:4]

    performance_by_product = summarize_group([enrich_campaign(row) for row in campaigns], "product_id")
    score_by_id = {item["name"]: item["roas"] * 0.65 + item["ctr"] * 70 for item in performance_by_product}
    relevant_product_ids = {row["product_id"] for row in relevant_rows}

    ranked = sorted(
        products,
        key=lambda product: (
            product.id in relevant_product_ids,
            score_by_id.get(product.id, 0) + product.margin * 1.8 + product.inventory_score / 100,
        ),
        reverse=True,
    )
    return ranked[:4]


def build_recommendations(
    by_channel: list[dict[str, Any]],
    by_format: list[dict[str, Any]],
    by_copy_style: list[dict[str, Any]],
    by_image_style: list[dict[str, Any]],
) -> list[str]:
    recommendations = []
    if by_channel:
        recommendations.append(f"Use {by_channel[0]['name']} as the benchmark channel; it has the strongest blended CTR/ROAS signal.")
    if by_format:
        recommendations.append(f"Lead with {business_format_name(by_format[0]['name'])} formats for the opening test batch.")
    if by_copy_style:
        recommendations.append(f"Use {by_copy_style[0]['name']} copy for the highest-intent segment.")
    if by_image_style:
        recommendations.append(f"Favor {by_image_style[0]['name']} visuals where the channel supports image-led creative.")
    return recommendations


def audience_fit_score(segment: Segment, channel: str, copy_style: str) -> int:
    score = 66
    if channel in segment.preferred_channels:
        score += 12
    if copy_style in segment.copy_preferences:
        score += 10
    if segment.price_sensitivity == "Medium":
        score += 4
    if segment.price_sensitivity == "High" and copy_style in {"value-led", "promo-urgency"}:
        score += 8
    return max(40, min(score, 96))
