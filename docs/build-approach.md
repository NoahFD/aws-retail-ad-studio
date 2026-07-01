# Build Approach and Considerations

## Approach

I prioritized the executive demo story first: a marketing manager should be able to move from connected retail data to an exportable campaign package in one session. The first screen is the working product rather than a landing page because the prototype needs to prove the workflow, not just describe it.

The core flow is:

1. Load campaign history, product catalog data, and customer segment profiles.
2. Surface a current recommendation from the available data.
3. Let the marketer apply the recommendation, edit campaign controls, or write a plain-language note.
4. Use a LangGraph workflow to analyze performance patterns and generate channel-specific creative variants.
5. Rank variants by projected CTR, ROAS, lift, confidence, and audience fit.
6. Allow optional AI polish for recommendations, brief refinement, copy, selected images, and a selected TikTok video.
7. Export the campaign handoff package with the same structure that could later be stored in S3.

The main priority was a credible end-to-end prototype: real frontend, real backend, structured data, generated assets, explainable scoring, and practical export behavior.

## Technology Choices

- **FastAPI** gives a small, clear Python API for demo endpoints, typed request/response models, static files, and health checks.
- **LangGraph** fits the multi-step campaign workflow: load data, analyze, recommend, generate, score, and optionally refine.
- **React + Vite + TypeScript** supports a polished single-page product experience with fast iteration and type-safe UI state.
- **TanStack Query** manages user-triggered API actions such as generation, recommendation refresh, brief refinement, media generation, and export.
- **Tailwind CSS 4 with shadcn/ui foundations** keeps the UI maintainable while preserving the custom executive-demo layout.
- **Pydantic and pydantic-settings** centralize schema validation and runtime configuration for models, providers, CORS, and cost controls.
- **Local CSV/JSON/image assets** make the demo portable and avoid exposing real retailer data.
- **Provider adapters** keep GPT Image 2, Seedance, AWS Bedrock-ready image generation, and AWS Nova Reel-ready video generation behind backend interfaces.
- **Local ZIP export** creates an immediate handoff artifact while preserving a clean path to S3 and presigned URLs.

## Tradeoffs

- The performance model is heuristic rather than trained ML. It computes real metrics from the synthetic dataset, then applies rules for forecasted lift and audience fit.
- Assets are generated demo references rather than real product photography, which protects privacy and keeps the prototype self-contained.
- Live image generation is intentionally limited to selected top previews to control cost and latency.
- Live video generation targets one selected TikTok creative; the cached demo video is available when a fast walkthrough matters more than live generation.
- The prototype does not push campaigns directly to Meta, TikTok, Google Ads, or an email service provider. It creates the plan and handoff package those integrations would consume.
- The CloudFormation file is a deployment skeleton, not a fully hardened production stack.
- Tailwind/shadcn were added as a foundation without rewriting every existing class, which kept the demo stable under a short timeline.

## Challenges and Solutions

The first challenge was keeping the prototype honest. A static mock would be faster, but it would not satisfy the brief. The implemented UI calls a backend endpoint, the backend runs a LangGraph workflow, and outputs change based on selected products, segments, channels, objective, and strategy.

The second challenge was cost control. The default path is deterministic and local, while live AI is opt-in and scoped to specific actions. This makes repeated demo practice safe while preserving a credible AI integration path.

The third challenge was explaining agent behavior to non-technical users. The UI presents business concepts like recommendations, campaign brief, ranked previews, and rationale. Technical details stay in the docs and backend structure.

## What I Would Do Differently With More Time

- Connect real S3 product assets, campaign exports, and analytics data.
- Train or calibrate a creative-response model with historical performance data.
- Add brand safety, legal review, approval states, and audit logs.
- Extend image/video generation to controlled batch generation with human review.
- Store every agent run and performance result as long-term creative memory.
- Add direct publishing integrations for paid social, display, search, and email platforms.
- Harden the AWS stack with CI/CD, observability, private networking, IAM least privilege, and environment-specific configuration.
