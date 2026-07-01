from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import DataSourceStatus, Product, Segment

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


@lru_cache(maxsize=1)
def load_campaign_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with (DATA_DIR / "campaign_performance.csv").open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            numeric_fields = ["spend_sgd", "impressions", "clicks", "conversions", "revenue_sgd"]
            for field in numeric_fields:
                row[field] = float(row[field])
            rows.append(row)
    return rows


@lru_cache(maxsize=1)
def load_products() -> list[Product]:
    raw = json.loads((DATA_DIR / "product_catalog.json").read_text(encoding="utf-8"))
    return [Product(**item) for item in raw]


@lru_cache(maxsize=1)
def load_segments() -> list[Segment]:
    raw = json.loads((DATA_DIR / "customer_segments.json").read_text(encoding="utf-8"))
    return [Segment(**item) for item in raw]


def source_statuses() -> list[DataSourceStatus]:
    campaigns = load_campaign_rows()
    products = load_products()
    segments = load_segments()
    return [
        DataSourceStatus(
            name="Connected data",
            type="All systems synced",
            status="connected",
            records=len(campaigns) + len(products) + len(segments),
            freshness="Updated 15 min ago",
            aws_target="EventBridge + Step Functions",
        ),
        DataSourceStatus(
            name="Sales & Orders",
            type="Campaign history",
            status="connected",
            records=len(campaigns),
            freshness="Updated 15 min ago",
            aws_target="Amazon S3 + AWS Glue Data Catalog",
        ),
        DataSourceStatus(
            name="Product Catalog",
            type="Images + details",
            status="connected",
            records=len(products),
            freshness="Updated 15 min ago",
            aws_target="Amazon S3 + DynamoDB or Aurora PostgreSQL",
        ),
        DataSourceStatus(
            name="Customer Segments",
            type="Audience profiles",
            status="connected",
            records=len(segments),
            freshness="Updated 15 min ago",
            aws_target="Amazon Personalize / Clean Rooms / DynamoDB",
        ),
        DataSourceStatus(
            name="Ad Platforms",
            type="Meta, TikTok, Google",
            status="connected",
            records=3,
            freshness="Synthetic connectors",
            aws_target="Amazon AppFlow + API Gateway",
        ),
        DataSourceStatus(
            name="Creative Library",
            type="Approved assets",
            status="connected",
            records=12840,
            freshness="Demo asset registry",
            aws_target="Amazon S3 + CloudFront",
        ),
    ]
