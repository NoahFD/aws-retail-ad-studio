import { Loader2, PencilSparkles, Sparkles, Tags, Users } from "lucide-react";

import type { BriefRefineResult, CampaignBrief, Channel, Product, Segment, StrategyCard } from "@/lib/api";
import { imageUrl } from "@/lib/api";
import { channels, markets, promptSuggestions } from "@/lib/constants";
import { channelIcon } from "@/lib/presentation";
import type { ProductFilter, ProductRecommendation } from "@/lib/productRecommendations";
import {
  filterProductRecommendations,
  productFilterOptions,
  productInsightCopy,
  suggestedCategoryLabel
} from "@/lib/productRecommendations";

type BriefBuilderProps = {
  brief: CampaignBrief;
  loading: boolean;
  productFilter: ProductFilter;
  productRecommendations: ProductRecommendation[];
  segments: Segment[];
  selectedProducts: Product[];
  primarySegment?: Segment;
  selectedStrategy?: StrategyCard;
  previewsOutdated: boolean;
  updateBrief: (patch: Partial<CampaignBrief>) => void;
  updateProductFilter: (filter: ProductFilter) => void;
  toggleChannel: (channel: Channel) => void;
  toggleProduct: (productId: string) => void;
  briefRefineBusy: boolean;
  briefRefineError: string | null;
  briefRefineResult: BriefRefineResult | null;
  onRefineBrief: () => void;
  onUseSuggestedProducts: () => void;
  onGenerate: () => void;
};

export function BriefBuilder({
  brief,
  loading,
  productFilter,
  productRecommendations,
  segments,
  selectedProducts,
  primarySegment,
  selectedStrategy,
  previewsOutdated,
  updateBrief,
  updateProductFilter,
  toggleChannel,
  toggleProduct,
  briefRefineBusy,
  briefRefineError,
  briefRefineResult,
  onRefineBrief,
  onUseSuggestedProducts,
  onGenerate
}: BriefBuilderProps) {
  const productOptions = productFilterOptions(productRecommendations);
  const visibleProductRecommendations = filterProductRecommendations(productRecommendations, productFilter);

  return (
    <section className="panel brief-panel">
      <div className="section-title">
        <div>
          <h2 className="story-step-title">2 · Campaign brief</h2>
          <p>Describe the campaign in plain language, let the assistant fill the fields, then edit the choices before generating.</p>
        </div>
      </div>

      <div className="copilot-box">
        <div className="copilot-header">
          <div>
            <strong>Campaign Assistant</strong>
            <span>Write what you want. It turns your note into market, platform, audience, and product choices.</span>
          </div>
        </div>
        <textarea
          aria-label="Prompt or creative instructions"
          value={brief.creative_instruction}
          onChange={(event) => updateBrief({ creative_instruction: event.target.value })}
          placeholder="Example: TikTok-first Malaysia launch for value seekers. Use product-only flat lay and show fabric texture."
        />
        <div className="copilot-actions">
          <div className="prompt-chips">
            {promptSuggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => {
                  const current = brief.creative_instruction.trim();
                  const patch: Partial<CampaignBrief> = {
                    creative_instruction: current.includes(suggestion) ? current : `${current}${current ? " " : ""}${suggestion}.`
                  };
                  updateBrief(patch);
                }}
                type="button"
              >
                {suggestion}
              </button>
            ))}
          </div>
          <button className="secondary-action" onClick={onRefineBrief} disabled={loading || briefRefineBusy} type="button">
            {briefRefineBusy ? <Loader2 className="spin" size={15} /> : <Sparkles size={15} />}
            Refine brief with AI
          </button>
        </div>
        {briefRefineError ? <div className="inline-error compact-error">{briefRefineError}</div> : null}
        {briefRefineResult ? (
          <div className="assistant-result">
            <strong>{briefRefineResult.live_ai_used ? "AI-filled brief" : "Brief updated"}</strong>
            <span>{briefRefineResult.reasoning.slice(0, 2).join(" ")}</span>
          </div>
        ) : null}
        <div className="data-direction">
          <Sparkles size={15} />
          <span>
            <strong>Suggested from current data:</strong> {selectedStrategy?.title ?? "Catch the trend window"} ·{" "}
            {selectedStrategy?.recommendation ?? "Use the strongest recent performance pattern as the starting point."}
          </span>
        </div>
      </div>

      <div className="brief-form">
        <label>
          Market
          <select value={brief.market} onChange={(event) => updateBrief({ market: event.target.value })}>
            {markets.map((market) => (
              <option key={market}>{market}</option>
            ))}
          </select>
        </label>

        <label>
          Objective
          <select value={brief.objective} onChange={(event) => updateBrief({ objective: event.target.value as CampaignBrief["objective"] })}>
            <option>Sales</option>
            <option>Traffic</option>
            <option>Awareness</option>
            <option>Retention</option>
          </select>
        </label>

        <div className="wide channel-picker">
          <div className="field-head">
            <strong>Platforms</strong>
            <span>{brief.channels.length} selected</span>
          </div>
          <div>
            {channels.map((channel) => (
              <button className={brief.channels.includes(channel) ? "active" : ""} key={channel} onClick={() => toggleChannel(channel)} type="button">
                {channelIcon(channel)}
                {channel}
              </button>
            ))}
          </div>
        </div>

        <label className="wide">
          Audience segment
          <select value={brief.primary_segment_id} onChange={(event) => updateBrief({ primary_segment_id: event.target.value })}>
            {segments.map((segment) => (
              <option key={segment.id} value={segment.id}>
                {segment.name}
              </option>
            ))}
          </select>
        </label>

        <div className="wide audience-note">
          <Users size={15} />
          <span>
            <strong>{primarySegment?.name}</strong> {primarySegment?.profile}
          </span>
        </div>

        <div className="wide product-picker">
          <div className="field-head">
            <strong>Products</strong>
            <span>{selectedProducts.length} selected</span>
          </div>
          <div className="product-suggestion">
            <Tags size={15} />
            <span>
              <strong>Suggested category: {suggestedCategoryLabel(primarySegment)}</strong> · {productInsightCopy(productRecommendations, primarySegment)}
            </span>
            <button onClick={onUseSuggestedProducts} disabled={loading} type="button">
              Use suggested products
            </button>
          </div>
          <div className="product-filter-row" aria-label="Product filters">
            {productOptions.map((option) => (
              <button
                className={productFilter === option.value ? "active" : ""}
                key={option.value}
                onClick={() => updateProductFilter(option.value)}
                type="button"
              >
                {option.label}
              </button>
            ))}
          </div>
          <div className="product-row">
            {visibleProductRecommendations.map((recommendation) => (
              <button
                aria-pressed={brief.product_ids.includes(recommendation.product.id)}
                className={brief.product_ids.includes(recommendation.product.id) ? "active" : ""}
                key={recommendation.product.id}
                onClick={() => toggleProduct(recommendation.product.id)}
                type="button"
              >
                <img src={imageUrl(recommendation.product.image_url)} alt={recommendation.product.name} />
                <span>{recommendation.product.name}</span>
                <small>
                  {recommendation.fitLabel} · {recommendation.reasons[0]}
                </small>
              </button>
            ))}
          </div>
        </div>

      </div>

      <div className="action-row">
        <button className="primary-action" onClick={onGenerate} disabled={loading} type="button">
          {loading ? <Loader2 className="spin" size={17} /> : <PencilSparkles size={17} />}
          {previewsOutdated ? "Refresh ad previews" : "Create ad previews"}
        </button>
      </div>
    </section>
  );
}
