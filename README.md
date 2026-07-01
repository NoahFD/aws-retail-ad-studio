# AI-Powered Retail Ad Studio

Prototype for **Scenario B: AI-Powered Retail Ad Studio** from the AWS APJ Innovation Hub challenge.

The app helps a Southeast Asia fashion retailer turn campaign history, product catalog data, and customer segments into a ranked set of channel-ready ad previews. A marketer can start from a data-backed recommendation, adjust the campaign brief, generate previews, create selected image/video assets, and export a campaign handoff package.

## Submission Contents

- **Codebase**: frontend, backend, infrastructure, data, static assets, and run scripts are included in this repository.
- **Architecture overview PDF**: [docs/architecture.pdf](docs/architecture.pdf)
- **Build approach and considerations PDF**: [docs/build-approach.pdf](docs/build-approach.pdf)
- **Editable source docs**: [docs/architecture.md](docs/architecture.md) and [docs/build-approach.md](docs/build-approach.md)
- **AWS deployment skeleton**: [infra/aws-prototype.yaml](infra/aws-prototype.yaml)

## Demo Flow

1. Open the Retail Creative Console.
2. Review **Today's recommendation** from campaign, product, and segment data.
3. Click **Refresh from data** to run one optional AI-assisted recommendation refresh.
4. Click **Apply to brief** or write a plain-language note in **Campaign Assistant**.
5. Click **Refine brief with AI** to translate the note into structured campaign fields.
6. Click **Create ad previews**.
7. Review ranked ad previews, predicted impact, and rationale.
8. Click **Polish copy** to run the optional LangGraph copy-refinement branch.
9. Click **Create platform images** to generate one image for the top preview on each selected platform.
10. Click **Create TikTok video** to generate or display the top TikTok short-form asset.
11. Click **Export** to download a campaign handoff ZIP.

## Tech Stack

- **Frontend**: React, TypeScript, Vite, TanStack Query, Tailwind CSS 4, shadcn/ui foundation, lucide-react
- **Backend**: Python, FastAPI, LangGraph, Pydantic, pydantic-settings
- **Data**: synthetic campaign CSV, product catalog JSON, customer segment JSON, generated product/ad assets
- **AI integrations**: optional OpenAI text calls, GPT Image 2 image generation, Seedance 2.0 via BytePlus Ark video path, AWS Bedrock/Nova Reel-ready adapters
- **Infrastructure path**: AWS App Runner/ECS, S3, DynamoDB/Aurora, Glue, EventBridge, CloudFront, Secrets Manager, Bedrock/OpenAI provider layer

The default preview-generation path is deterministic and local so the demo is repeatable and inexpensive. Live AI calls happen only when the marketer clicks a live action.

## Project Structure

```text
backend/
  app/                    FastAPI app, LangGraph agent, analytics, exporters, media adapters
  data/                   synthetic campaign, product, and segment data
  static/products/        product catalog images
  static/ads/             generated ad preview assets
  static/generated/       live generated image/video outputs
  static/exports/         local campaign ZIP exports
frontend/
  src/                    React app state, API client, constants, product logic
  src/components/         focused UI components and shadcn/ui primitives
  public/static/          static assets used by production/demo builds
docs/
  architecture.md         editable architecture source
  architecture.pdf        one-page architecture overview
  build-approach.md       editable build approach source
  build-approach.pdf      1-2 page build approach and considerations
infra/
  aws-prototype.yaml      AWS deployment skeleton
scripts/
  run_dev.sh              one-command local dev runner
  generate_deliverable_pdfs.py
                         regenerates the two PDF deliverables
```

## Prerequisites

- Python 3.11+
- Node.js 20.19+ or 22.12+ (Node 21.x is not supported by the current Vite release)
- Optional: an OpenAI API key for live recommendation, brief, copy, and image actions
- Optional: a BytePlus Ark key for live Seedance video generation

## Setup

From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cp .env.example .env
```

Update `.env` only if you want live AI actions. The app runs without keys for the deterministic demo path.

```bash
cd frontend
npm install
```

## Run Locally

Start both services with one command:

```bash
./scripts/run_dev.sh
```

Then open:

```text
http://localhost:5173
```

Or run the services separately:

```bash
# Terminal 1
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2
cd frontend
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

## Verification

Backend smoke test without spending model tokens:

```bash
source .venv/bin/activate
python - <<'PY'
from backend.app.agent import run_campaign_agent
from backend.app.models import CampaignBrief

result = run_campaign_agent(CampaignBrief(use_live_ai=False))
print(len(result.variants), result.variants[0].headline, result.live_ai_used)
PY
```

Frontend production build:

```bash
cd frontend
npm run build
```

Regenerate PDF deliverables:

```bash
source .venv/bin/activate
python scripts/generate_deliverable_pdfs.py
```

## Environment Variables

The full set is documented in [.env.example](.env.example). Key values:

- `OPENAI_API_KEY`: enables live recommendation refresh, brief refinement, copy polish, and GPT Image 2 generation.
- `OPENAI_MODEL`: text model for optional AI steps.
- `OPENAI_IMAGE_MODEL`: image model used by the selected image-generation provider.
- `IMAGE_PROVIDER`: `gpt-image-2` or `aws-bedrock-ready`.
- `VIDEO_PROVIDER`: `seedance-ark`, `aws-nova-reel`, or cached demo behavior depending on configuration.
- `VIDEO_LIVE_ENABLED`: set to `false` for instant demo playback using the cached video.
- `ARK_API_KEY`: enables live Seedance 2.0 calls through BytePlus Ark.
- `AWS_NOVA_REEL_S3_URI`: enables the AWS Nova Reel adapter path when AWS credentials are available.
- `BACKEND_CORS_ORIGINS`: allowed frontend origins for local/API calls.

## Export Package

The **Export** action creates a ZIP in `backend/static/exports/`. The package includes:

- `manifest.json`: full brief, plan, insights, selected creative, generated media metadata, source metadata, and AWS handoff notes
- `variants.csv`: ranked creative variants for media or agency handoff
- `assets/catalog/`: catalog reference images used by the ranked previews
- `assets/images/`: generated images when available
- `assets/videos/`: generated videos when available
- `README.txt`: human-readable campaign summary

The local payload is shaped so it can later be written to S3, recorded in DynamoDB/Aurora, and returned through a presigned URL.

## Cost Guardrail

Default campaign generation uses local data and deterministic scoring. These actions make optional live calls only when configured and clicked:

- **Refresh from data**: one text-model recommendation refresh
- **Refine brief with AI**: one text-model brief refinement
- **Polish copy**: one text-model copy pass
- **Create platform images**: one image per selected platform
- **Create TikTok video**: one selected TikTok video when live video is enabled

The **Export** action does not call a model.
