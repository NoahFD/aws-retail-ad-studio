from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGE_WIDTH, PAGE_HEIGHT = A4

INK = colors.HexColor("#17212b")
MUTED = colors.HexColor("#5c6670")
LINE = colors.HexColor("#d8dee6")
BLUE = colors.HexColor("#2455a6")
TEAL = colors.HexColor("#1d8a8a")
GREEN = colors.HexColor("#2f7d4f")
AMBER = colors.HexColor("#b66a00")
FILL = colors.HexColor("#f6f8fb")
PANEL = colors.HexColor("#eef5ff")


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=MUTED,
            spaceAfter=7,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.8,
            leading=13,
            textColor=BLUE,
            spaceBefore=7,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.3,
            leading=11.3,
            textColor=INK,
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.3,
            leading=9.3,
            textColor=MUTED,
        ),
        "box": ParagraphStyle(
            "Box",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=INK,
            alignment=TA_CENTER,
        ),
        "table_head": ParagraphStyle(
            "TableHead",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8,
            textColor=colors.white,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=6.8,
            leading=8.1,
            textColor=INK,
        ),
    }


class Rule(Flowable):
    def __init__(self, width: float, color=LINE, thickness: float = 0.7):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness

    def wrap(self, availWidth, availHeight):
        return min(self.width, availWidth), self.height

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 17 * mm, PAGE_WIDTH - doc.rightMargin, 17 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 11 * mm, "AI-Powered Retail Ad Studio")
    canvas.drawRightString(PAGE_WIDTH - doc.rightMargin, 11 * mm, f"Page {doc.page}")
    canvas.restoreState()


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def bullets(items: list[str], style: ParagraphStyle, bullet_font_size: float = 5.8) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(item, style), leftIndent=7, bulletFontSize=bullet_font_size) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=10,
        bulletIndent=2,
        spaceBefore=1,
        spaceAfter=4,
    )


def box(label: str, style: ParagraphStyle, fill=FILL) -> Table:
    table = Table([[Paragraph(label, style)]], colWidths=[37 * mm], rowHeights=[14 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), fill),
                ("BOX", (0, 0), (-1, -1), 0.7, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def arrow(style: ParagraphStyle) -> Paragraph:
    return Paragraph("&#8594;", style)


def architecture_pdf() -> None:
    s = styles()
    output = DOCS / "architecture.pdf"
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
        title="Architecture Overview",
        author="AI-Powered Retail Ad Studio",
    )

    flow: list = [
        para("Architecture Overview", s["title"]),
        para(
            "A one-page view of the local prototype and the AWS-ready migration path.",
            s["subtitle"],
        ),
        Rule(178 * mm),
        Spacer(1, 4),
    ]

    row1 = [box("Marketing user", s["box"], PANEL), arrow(s["box"]), box("React + Vite campaign console", s["box"], PANEL), arrow(s["box"]), box("FastAPI backend", s["box"], PANEL)]
    row2 = [box("LangGraph campaign agent", s["box"]), arrow(s["box"]), box("Analytics + scoring", s["box"]), arrow(s["box"]), box("Ranked ad previews", s["box"])]
    row3 = [box("CSV/JSON/product assets", s["box"]), arrow(s["box"]), box("Image/video provider adapters", s["box"]), arrow(s["box"]), box("Campaign export ZIP", s["box"])]
    row4 = [box("Future S3 + Glue + DynamoDB/Aurora", s["box"], colors.HexColor("#f3fbf6")), arrow(s["box"]), box("Bedrock/OpenAI + Nova Reel/Seedance", s["box"], colors.HexColor("#f3fbf6")), arrow(s["box"]), box("S3 export + presigned URL", s["box"], colors.HexColor("#f3fbf6"))]
    diagram = Table(
        [row1, row2, row3, row4],
        colWidths=[39 * mm, 7 * mm, 39 * mm, 7 * mm, 39 * mm],
        rowHeights=[17 * mm, 17 * mm, 17 * mm, 17 * mm],
        hAlign="LEFT",
    )
    diagram.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    flow += [diagram, Spacer(1, 5)]

    left = [
        para("How Data Flows", s["h2"]),
        bullets(
            [
                "The frontend loads bootstrap data and renders the working campaign brief.",
                "FastAPI sends marketer actions to LangGraph workflows for analysis, recommendation, generation, and scoring.",
                "Optional AI steps refresh recommendations, refine the brief, polish copy, generate selected images, or create one selected video.",
                "The export endpoint packages manifest data, variants CSV, catalog references, and generated media into a local ZIP.",
            ],
            s["body"],
        ),
        para("Key Runtime Services", s["h2"]),
        bullets(
            [
                "React/Vite UI for brief controls, ranked previews, rationale, media actions, and export.",
                "FastAPI backend for APIs, static files, provider adapters, and campaign packaging.",
                "LangGraph agent with load, analyze, recommend, generate, and score stages.",
                "Analytics layer for CTR, CVR, ROAS, CPA, segment fit, and forecasted lift.",
            ],
            s["body"],
        ),
    ]

    right = [
        para("AWS Migration Path", s["h2"]),
        architecture_mapping_table(s),
        Spacer(1, 5),
        para("Design Rationale", s["h2"]),
        para(
            "The prototype is intentionally portable and low-cost while preserving production boundaries: UI, API, agent orchestration, analytics, provider integrations, and export storage are separate. This lets the same workflow run locally now and move to AWS-managed data, media, model, and hosting services later.",
            s["body"],
        ),
    ]

    columns = Table([[left, right]], colWidths=[86 * mm, 86 * mm], hAlign="LEFT")
    columns.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    flow.append(columns)
    doc.build(flow, onFirstPage=header_footer, onLaterPages=header_footer)


def architecture_mapping_table(s: dict[str, ParagraphStyle]) -> Table:
    data = [
        [para("Prototype", s["table_head"]), para("AWS-ready target", s["table_head"])],
        [para("Local CSV/JSON", s["table_cell"]), para("S3, Glue, DynamoDB/Aurora", s["table_cell"])],
        [para("FastAPI process", s["table_cell"]), para("App Runner, ECS, or Lambda container", s["table_cell"])],
        [para("React static build", s["table_cell"]), para("S3 + CloudFront or Amplify", s["table_cell"])],
        [para("Local exports", s["table_cell"]), para("S3 object + presigned URL", s["table_cell"])],
        [para("OpenAI/Seedance adapters", s["table_cell"]), para("Secrets Manager + Bedrock/provider layer", s["table_cell"])],
    ]
    table = Table(data, colWidths=[38 * mm, 46 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FILL]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def build_approach_pdf() -> None:
    s = styles()
    output = DOCS / "build-approach.pdf"
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=16 * mm,
        bottomMargin=20 * mm,
        title="Build Approach and Considerations",
        author="AI-Powered Retail Ad Studio",
    )

    story: list = [
        para("Build Approach and Considerations", s["title"]),
        para(
            "How the prototype was approached, what was prioritized, and what tradeoffs were made under the time constraint.",
            s["subtitle"],
        ),
        Rule(176 * mm),
        section(
            "Approach",
            [
                "I prioritized the executive demo story first: a marketing manager should move from connected retail data to an exportable campaign package in one session.",
                "The first screen is the working product rather than a landing page. The prototype needed to prove the workflow, not just describe it.",
                "The main build priority was an honest end-to-end loop: real frontend, real backend, structured data, generated assets, explainable scoring, and practical export behavior.",
            ],
            s,
        ),
        section(
            "Workflow Priorities",
            [
                "Load campaign history, product catalog data, and customer segment profiles.",
                "Surface a current recommendation and let the marketer apply it or adjust the brief.",
                "Use LangGraph to analyze performance patterns, generate channel variants, and rank them by projected CTR, ROAS, lift, confidence, and audience fit.",
                "Keep live AI actions optional and scoped to recommendation refresh, brief refinement, copy polish, selected images, and one selected TikTok video.",
                "Export the selected campaign state in the same shape that could later be stored in S3.",
            ],
            s,
        ),
        tech_table(s),
        section(
            "Tradeoffs",
            [
                "The performance model is heuristic rather than trained ML; it computes real metrics from synthetic data and applies rules for forecasted lift and fit.",
                "Product and ad assets are generated demo references instead of real retailer photography, which keeps the prototype self-contained and privacy-safe.",
                "Image generation is limited to selected top previews, and live video targets one TikTok creative, to control cost and latency.",
                "The prototype creates a campaign handoff package but does not publish directly into paid-media or email platforms.",
                "The CloudFormation file is a deployment skeleton rather than a fully hardened production stack.",
            ],
            s,
        ),
        PageBreak(),
        para("Build Approach and Considerations", s["title"]),
        para("Continuation: implementation challenges, future work, and delivery notes.", s["subtitle"]),
        Rule(176 * mm),
        section(
            "Interesting Challenges",
            [
                "Keeping the prototype honest: the UI calls a backend endpoint, the backend runs a LangGraph workflow, and outputs change based on products, segments, channels, objective, and strategy.",
                "Managing cost: the default path is deterministic and local, while live AI is opt-in and limited to specific actions.",
                "Making agent behavior understandable: the UI uses marketer-facing language such as recommendations, brief, ranked previews, and rationale, while technical details stay in docs and code.",
            ],
            s,
        ),
        section(
            "What I Would Do With More Time",
            [
                "Connect real S3 product assets, campaign exports, and analytics data.",
                "Train or calibrate a creative-response model with historical performance data.",
                "Add brand safety, legal review, approval states, audit logs, and creative memory.",
                "Extend image/video generation to controlled batch generation with human review.",
                "Add direct publishing integrations for paid social, display, search, and email platforms.",
                "Harden the AWS stack with CI/CD, observability, private networking, least-privilege IAM, and environment-specific configuration.",
            ],
            s,
        ),
        section(
            "Delivery Notes",
            [
                "README includes setup, run, verification, environment, export, and cost-control instructions.",
                "Architecture and build approach PDFs are generated into docs/ for direct submission.",
                "The repo includes a one-command dev runner plus a PDF generation script for reproducible documentation.",
            ],
            s,
        ),
    ]
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)


def section(title: str, items: list[str], s: dict[str, ParagraphStyle]) -> KeepTogether:
    return KeepTogether([para(title, s["h2"]), bullets(items, s["body"])])


def tech_table(s: dict[str, ParagraphStyle]) -> KeepTogether:
    data = [
        [para("Technology", s["table_head"]), para("Reasoning", s["table_head"])],
        [para("FastAPI", s["table_cell"]), para("Small, typed Python API for demo endpoints, static files, health checks, media adapters, and exports.", s["table_cell"])],
        [para("LangGraph", s["table_cell"]), para("Natural fit for the load, analyze, recommend, generate, score, and refine workflow.", s["table_cell"])],
        [para("React + Vite + TypeScript", s["table_cell"]), para("Fast iteration and type-safe UI state for a polished single-page campaign console.", s["table_cell"])],
        [para("TanStack Query", s["table_cell"]), para("Clean handling for user-triggered generation, media, recommendation, brief, and export mutations.", s["table_cell"])],
        [para("Pydantic settings", s["table_cell"]), para("Centralized provider, model, CORS, and cost-control configuration.", s["table_cell"])],
        [para("Provider adapters", s["table_cell"]), para("OpenAI, GPT Image 2, Seedance, Bedrock, and Nova Reel paths stay swappable behind backend interfaces.", s["table_cell"])],
        [para("Local ZIP export", s["table_cell"]), para("Immediate campaign handoff today, with a direct path to S3, metadata storage, and presigned URLs later.", s["table_cell"])],
    ]
    table = Table(data, colWidths=[42 * mm, 128 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FILL]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return KeepTogether([para("Technology Choices", s["h2"]), table, Spacer(1, 5)])


def assert_ascii_text() -> None:
    for path in [DOCS / "architecture.md", DOCS / "build-approach.md"]:
        text = path.read_text(encoding="utf-8")
        try:
            text.encode("ascii")
        except UnicodeEncodeError as exc:
            raise SystemExit(f"{path} contains non-ASCII text near index {exc.start}") from exc


def assert_pdf_size(path: Path) -> None:
    if not path.exists() or path.stat().st_size < 3_000:
        raise SystemExit(f"Expected a non-empty PDF at {path}")


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    assert_ascii_text()
    architecture_pdf()
    build_approach_pdf()
    assert_pdf_size(DOCS / "architecture.pdf")
    assert_pdf_size(DOCS / "build-approach.pdf")
    print(f"Wrote {DOCS / 'architecture.pdf'}")
    print(f"Wrote {DOCS / 'build-approach.pdf'}")


if __name__ == "__main__":
    main()
