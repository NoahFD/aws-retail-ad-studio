import { ArrowRight, Loader2, Play } from "lucide-react";

import type { CreativeVariant, ExportCampaignResult, GeneratedImageResult, GeneratedVideoResult, Product, Segment } from "@/lib/api";
import { imageUrl } from "@/lib/api";
import { channelIcon, lift, pct, variantTitle } from "@/lib/presentation";

type PreviewResultsProps = {
  variants: CreativeVariant[];
  products: Product[];
  segments: Segment[];
  selectedVariantId?: string;
  exportBusy: boolean;
  exportError: string | null;
  exportResult: ExportCampaignResult | null;
  generatedImages: Record<string, GeneratedImageResult>;
  generatedVideos: Record<string, GeneratedVideoResult>;
  previewsOutdated: boolean;
  updating: boolean;
  updateLabel: string;
  onExport: () => void;
  onSelect: (variantId: string) => void;
};

export function PreviewResults({
  variants,
  products,
  segments,
  selectedVariantId,
  exportBusy,
  exportError,
  exportResult,
  generatedImages,
  generatedVideos,
  previewsOutdated,
  updating,
  updateLabel,
  onExport,
  onSelect
}: PreviewResultsProps) {
  return (
    <section className={updating ? "panel preview-panel is-updating" : "panel preview-panel"} aria-busy={updating}>
      {updating ? (
        <div className="data-update-overlay" role="status" aria-live="polite">
          <div className="data-update-card">
            <Loader2 className="spin" size={18} />
            <strong>{updateLabel}</strong>
            <span>Ranking fresh previews against the selected platforms, products, and audience.</span>
          </div>
        </div>
      ) : null}

      <div className="section-title compact">
        <div>
          <h2 className="story-step-title">4 · Review and export</h2>
          <p>Ranked by predicted ROAS, CTR, lift, and audience fit, then packaged for local or AWS handoff.</p>
        </div>
        <button disabled={exportBusy || variants.length === 0 || updating || previewsOutdated} onClick={onExport} type="button">
          {exportBusy ? <Loader2 className="spin" size={14} /> : "Export"}
          {!exportBusy ? <ArrowRight size={14} /> : null}
        </button>
      </div>

      {previewsOutdated ? (
        <div className="refresh-notice">
          Refresh previews to match the current brief before export.
        </div>
      ) : null}

      {exportResult || exportError ? (
        <div className={exportError && !exportResult ? "export-status error" : "export-status"} role="status">
          {exportResult ? (
            <>
              <strong>Saved locally: {exportResult.filename}</strong>
              <span>AWS-ready target: {exportResult.aws_ready_target}</span>
              {exportError ? <small>{exportError}</small> : null}
              <a download={exportResult.filename} href={imageUrl(exportResult.download_url)}>
                Download package
              </a>
            </>
          ) : (
            <span>{exportError}</span>
          )}
        </div>
      ) : null}

      <div className="preview-list">
        {variants.slice(0, 5).map((variant) => {
          const product = products.find((item) => item.id === variant.product_id);
          const segment = segments.find((item) => item.id === variant.segment_id);
          return (
            <PreviewCard
              key={variant.id}
              product={product}
              segment={segment}
              selected={selectedVariantId === variant.id}
              variant={variant}
              generatedImage={generatedImages[variant.id]}
              generatedVideo={generatedVideos[variant.id]}
              onSelect={() => onSelect(variant.id)}
            />
          );
        })}
      </div>
    </section>
  );
}

function PreviewCard({
  variant,
  product,
  segment,
  selected,
  generatedImage,
  generatedVideo,
  onSelect
}: {
  variant: CreativeVariant;
  product?: Product;
  segment?: Segment;
  selected: boolean;
  generatedImage?: GeneratedImageResult;
  generatedVideo?: GeneratedVideoResult;
  onSelect: () => void;
}) {
  const productImage = generatedImage?.image_url ? imageUrl(generatedImage.image_url) : product ? imageUrl(product.image_url) : "";
  const isTikTok = variant.channel === "TikTok";
  const mediaPath = product?.category === "Menswear" ? "/static/ads/tiktok-menswear.png" : "/static/ads/tiktok-dress.png";
  const tikTokImage = generatedImage?.image_url ? imageUrl(generatedImage.image_url) : productImage || imageUrl(mediaPath);
  const tikTokVideo = generatedVideo?.video_url ? imageUrl(generatedVideo.video_url) : "";

  return (
    <button className={selected ? "preview-card selected" : "preview-card"} onClick={onSelect} type="button">
      <div className="preview-topline">
        <span>
          {channelIcon(variant.channel)}
          {variant.channel}
        </span>
        <strong>#{variant.rank ?? 1}</strong>
      </div>

      <div className={`ad-mock ${variant.channel.toLowerCase()}`}>
        {isTikTok ? (
          <>
            {tikTokVideo ? (
              <video autoPlay loop muted playsInline poster={tikTokImage} src={tikTokVideo} />
            ) : (
              <img src={tikTokImage} alt={`${product?.name ?? "Product"} video preview`} />
            )}
            <div className="play-button">
              <Play size={20} fill="currentColor" />
            </div>
            {generatedVideo ? <span className="asset-badge">Video ready</span> : generatedImage ? <span className="asset-badge">Image ready</span> : null}
          </>
        ) : (
          <>
            <img src={productImage} alt={product?.name ?? "Product"} />
            <div>
              <strong>{variant.headline}</strong>
              <p>{variant.body}</p>
              <small>{variant.cta}</small>
            </div>
            {generatedImage ? <span className="asset-badge">Image ready</span> : null}
          </>
        )}
      </div>

      <div className="preview-copy">
        <strong>{variantTitle(variant, product)}</strong>
        <span>
          {segment?.name ?? "Audience"} · {variant.format}
        </span>
      </div>

      <div className="score-row">
        <Score label="ROAS" value={`${variant.predicted_roas.toFixed(1)}x`} />
        <Score label="CTR" value={pct(variant.predicted_ctr)} />
        <Score label="Lift" value={lift(variant.predicted_lift)} />
      </div>
    </button>
  );
}

function Score({ label, value }: { label: string; value: string }) {
  return (
    <span>
      <strong>{value}</strong>
      <small>{label}</small>
    </span>
  );
}
