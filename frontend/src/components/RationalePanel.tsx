import { BarChart3, Clapperboard, Database, Loader2, Sparkles, Target } from "lucide-react";

import type { CampaignBrief, CreativeVariant, GeneratedImageResult, GeneratedVideoResult, Product, Segment } from "@/lib/api";
import { imageUrl } from "@/lib/api";
import { lift, pct } from "@/lib/presentation";

import { MetricCard } from "./MetricCard";

type RationalePanelProps = {
  variant: CreativeVariant | null;
  product?: Product;
  segment?: Segment;
  imageProvider: CampaignBrief["image_provider"];
  modelPresentation: CampaignBrief["model_presentation"];
  generatedImage?: GeneratedImageResult;
  generatedVideo?: GeneratedVideoResult;
  imagePrompt: string;
  videoPrompt: string;
  aiForecastUsed: boolean;
  imageBusy: boolean;
  imageError: string | null;
  previewsOutdated: boolean;
  updating: boolean;
  updateLabel: string;
  videoBusy: boolean;
  videoError: string | null;
  onImagePromptChange: (value: string) => void;
  onImageProviderChange: (value: CampaignBrief["image_provider"]) => void;
  onModelPresentationChange: (value: CampaignBrief["model_presentation"]) => void;
  onVideoPromptChange: (value: string) => void;
  onGenerateImage: () => void;
  onGenerateVideo: () => void;
};

export function RationalePanel({
  variant,
  product,
  segment,
  imageProvider,
  modelPresentation,
  generatedImage,
  generatedVideo,
  imagePrompt,
  videoPrompt,
  aiForecastUsed,
  imageBusy,
  imageError,
  previewsOutdated,
  updating,
  updateLabel,
  videoBusy,
  videoError,
  onImagePromptChange,
  onImageProviderChange,
  onModelPresentationChange,
  onVideoPromptChange,
  onGenerateImage,
  onGenerateVideo
}: RationalePanelProps) {
  if (!variant || !product) return null;

  const reviewImage = generatedImage?.image_url ? imageUrl(generatedImage.image_url) : imageUrl(product.image_url);
  const reviewVideo = generatedVideo?.video_url ? imageUrl(generatedVideo.video_url) : null;
  const presentationLabel = modelPresentationLabel(modelPresentation);

  return (
    <section className={updating ? "panel rationale-panel is-updating" : "panel rationale-panel"} aria-busy={updating}>
      {updating ? (
        <div className="data-update-overlay" role="status" aria-live="polite">
          <div className="data-update-card">
            <Loader2 className="spin" size={18} />
            <strong>{updateLabel}</strong>
            <span>Updating ROAS, CTR, and lift from campaign history, catalog, and audience fit.</span>
          </div>
        </div>
      ) : null}

      <div className="section-title compact">
        <div>
          <h2 className="story-step-title">3 · Selected creative</h2>
          <p>Forecast impact, rationale, and production-ready assets for the chosen product, platform, and segment.</p>
        </div>
        <div className="section-actions">
          <button onClick={onGenerateImage} disabled={imageBusy || previewsOutdated || updating} type="button">
            {imageBusy ? <Loader2 className="spin" size={14} /> : <Sparkles size={14} />}
            {generatedImage ? "Regenerate platform images" : "Create platform images"}
          </button>
          <button onClick={onGenerateVideo} disabled={videoBusy || previewsOutdated || updating} type="button">
            {videoBusy ? <Loader2 className="spin" size={14} /> : <Clapperboard size={14} />}
            {generatedVideo ? "Regenerate TikTok video" : "Create TikTok video"}
          </button>
        </div>
      </div>

      <div className="rationale-hero">
        <div className={generatedImage ? "live-image-frame generated" : "live-image-frame"}>
          <img src={reviewImage} alt={generatedImage ? `${product.name} generated creative` : product.name} />
          {generatedImage ? <span>{generatedImage.provider}</span> : null}
        </div>
        <div>
          <span>
            {variant.channel} · {segment?.name ?? "Audience"} · {presentationLabel}
          </span>
          <strong>{variant.headline}</strong>
          <p>{variant.rationale}</p>
        </div>
      </div>

      <div className="asset-model-picker">
        <div className="field-head">
          <strong>Model presentation</strong>
          <span>Controls image and video direction</span>
        </div>
        <div className="model-option-grid">
          {[
            { value: "female_model", label: "Female model", detail: "Lifestyle shot with a female model" },
            { value: "male_model", label: "Male model", detail: "Lifestyle shot with a male model" },
            { value: "product_only", label: "Product only", detail: "Flat lay, hanger, or mannequin" }
          ].map((option) => (
            <button
              className={modelPresentation === option.value ? "active" : ""}
              disabled={updating || imageBusy || videoBusy}
              key={option.value}
              onClick={() => onModelPresentationChange(option.value as CampaignBrief["model_presentation"])}
              type="button"
            >
              <strong>{option.label}</strong>
              <span>{option.detail}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="asset-prompt-grid">
        <div className="asset-prompt-box">
          <div className="field-head">
            <strong>Image direction</strong>
            <span>{presentationLabel}</span>
          </div>
          <label className="asset-provider-control">
            Image provider
            <select
              value={imageProvider}
              disabled={updating || imageBusy}
              onChange={(event) => onImageProviderChange(event.target.value as CampaignBrief["image_provider"])}
            >
              <option value="gpt-image-2">OpenAI GPT Image 2</option>
              <option value="aws-bedrock-ready">AWS Bedrock-ready adapter</option>
            </select>
          </label>
          <textarea
            aria-label="Image generation direction"
            value={imagePrompt}
            disabled={updating || imageBusy}
            onChange={(event) => onImagePromptChange(event.target.value)}
            placeholder={`Keep ${product.name} unchanged. Use ${presentationLabel.toLowerCase()} and adjust background, crop, lighting, or fabric detail.`}
          />
        </div>
        <div className="asset-prompt-box">
          <div className="field-head">
            <strong>Video direction</strong>
            <span>{modelPresentation === "product_only" ? "Uses product-only first frame" : "Text-guided for privacy"}</span>
          </div>
          <textarea
            aria-label="Video generation direction"
            value={videoPrompt}
            disabled={updating || imageBusy || videoBusy}
            onChange={(event) => onVideoPromptChange(event.target.value)}
            placeholder="Describe motion, camera movement, first frame, privacy-safe crop, and product detail."
          />
        </div>
      </div>

      {previewsOutdated ? (
        <div className="refresh-notice">
          Refresh previews to update this recommendation before creating image or video assets.
        </div>
      ) : null}
      {imageError ? <div className="inline-error">{imageError}</div> : null}
      {videoError ? <div className="inline-error">{videoError}</div> : null}
      {aiForecastUsed ? (
        <div className="forecast-proof">
          <Sparkles size={14} />
          <span>AI-assisted forecast: metrics were calibrated with live AI, then bounded by historical performance guardrails.</span>
        </div>
      ) : null}
      {generatedImage ? (
        <div className="image-proof">
          <Sparkles size={14} />
          <span>
            Live image generated with {generatedImage.model}. Product reference: {product.name}. {generatedImage.cost_guardrail}
          </span>
        </div>
      ) : null}
      {generatedVideo ? (
        <div className="video-proof">
          <div className="video-frame">
            <video controls muted playsInline poster={reviewImage} src={reviewVideo ?? undefined} />
          </div>
          <div className="video-copy">
            <span>{generatedVideo.live_provider_used ? "Live provider output" : "Demo-safe video preview"}</span>
            <strong>
              {generatedVideo.provider} · {generatedVideo.duration_seconds}s · {generatedVideo.ratio}
            </strong>
            <p>{generatedVideo.fallback_reason ?? generatedVideo.cost_guardrail}</p>
            {generatedVideo.reference_image_url ? (
              <small>
                Video reference: {generatedVideo.reference_image_role === "first_frame" ? "generated image as first frame" : "selected product image"}
              </small>
            ) : null}
            <small>AWS-ready target: {generatedVideo.aws_ready_target}</small>
          </div>
        </div>
      ) : null}

      <div className="impact-grid">
        <MetricCard label="Forecast ROAS" value={`${variant.predicted_roas.toFixed(1)}x`} />
        <MetricCard label="Predicted CTR" value={pct(variant.predicted_ctr)} />
        <MetricCard label="Expected lift" value={lift(variant.predicted_lift)} />
      </div>

      <div className="rationale-list">
        <article>
          <BarChart3 size={16} />
          <span>Ranked using historical channel performance, format performance, and segment fit.</span>
        </article>
        <article>
          <Database size={16} />
          <span>Uses product catalog imagery and descriptions instead of a blank creative brief.</span>
        </article>
        <article>
          <Target size={16} />
          <span>Creative prompt: {variant.image_prompt ?? "Provider-ready image instructions are prepared after generation."}</span>
        </article>
      </div>
    </section>
  );
}

function modelPresentationLabel(value: CampaignBrief["model_presentation"]) {
  if (value === "male_model") return "Male model";
  if (value === "product_only") return "Product only";
  return "Female model";
}
