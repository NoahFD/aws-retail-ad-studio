import { useMutation } from "@tanstack/react-query";
import { Check, ShieldCheck, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { BriefBuilder } from "@/components/BriefBuilder";
import { LoadingScreen } from "@/components/LoadingScreen";
import { PreviewResults } from "@/components/PreviewResults";
import { RationalePanel } from "@/components/RationalePanel";
import { TodayRecommendation } from "@/components/TodayRecommendation";
import type {
  AgentResult,
  BriefPatch,
  BriefRefineResult,
  BootstrapPayload,
  CampaignBrief,
  Channel,
  CreativeVariant,
  ExportCampaignResult,
  GeneratedImageResult,
  GeneratedVideoResult,
  Product,
  Segment,
  TodayRecommendationResult
} from "@/lib/api";
import { api, imageUrl } from "@/lib/api";
import { defaultTodayRecommendation, navItems } from "@/lib/constants";
import {
  RECOMMENDED_PRODUCT_FILTER,
  type ProductFilter,
  productRecommendationsForSegment,
  suggestedProductIds
} from "@/lib/productRecommendations";

export function App() {
  const [bootstrap, setBootstrap] = useState<BootstrapPayload | null>(null);
  const [brief, setBrief] = useState<CampaignBrief | null>(null);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [selectedVariantId, setSelectedVariantId] = useState<string | null>(null);
  const [todayRecommendation, setTodayRecommendation] = useState<TodayRecommendationResult>(defaultTodayRecommendation);
  const [dataRefreshLabel, setDataRefreshLabel] = useState("15 min ago");
  const [briefRefineResult, setBriefRefineResult] = useState<BriefRefineResult | null>(null);
  const [generatedImages, setGeneratedImages] = useState<Record<string, GeneratedImageResult>>({});
  const [generatedVideos, setGeneratedVideos] = useState<Record<string, GeneratedVideoResult>>({});
  const [imagePrompt, setImagePrompt] = useState(
    "Keep the selected product unchanged. Follow the selected model presentation, then improve background, lighting, crop, and fabric texture."
  );
  const [videoPrompt, setVideoPrompt] = useState(
    "For product-only, use the generated product image as the first frame. For male or female model, use privacy-safe framing and focus on garment movement."
  );
  const [productFilter, setProductFilter] = useState<ProductFilter>(RECOMMENDED_PRODUCT_FILTER);
  const [exportResult, setExportResult] = useState<ExportCampaignResult | null>(null);
  const [busyLabel, setBusyLabel] = useState("Connecting retail data");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [insightError, setInsightError] = useState<string | null>(null);
  const [insightRefreshNote, setInsightRefreshNote] = useState("Local campaign history, catalog, and customer segments are ready.");
  const [briefRefineError, setBriefRefineError] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const generateMutation = useMutation({
    mutationFn: (nextBrief: CampaignBrief) => api.generate(nextBrief)
  });
  const refreshInsightMutation = useMutation({
    mutationFn: (nextBrief: CampaignBrief) => api.refreshInsight(nextBrief)
  });
  const refineBriefMutation = useMutation({
    mutationFn: ({ nextBrief, note }: { nextBrief: CampaignBrief; note: string }) => api.refineBrief(nextBrief, note)
  });
  const generateImageMutation = useMutation({
    mutationFn: ({ nextBrief, variant, promptNote }: { nextBrief: CampaignBrief; variant: CreativeVariant; promptNote: string }) =>
      api.generateImage(nextBrief, variant, promptNote)
  });
  const generateVideoMutation = useMutation({
    mutationFn: ({
      nextBrief,
      variant,
      promptNote,
      referenceImageUrl,
      referenceImageRole
    }: {
      nextBrief: CampaignBrief;
      variant: CreativeVariant;
      promptNote: string;
      referenceImageUrl: string | null;
      referenceImageRole: string;
    }) => api.generateVideo(nextBrief, variant, promptNote, referenceImageUrl, referenceImageRole)
  });
  const exportCampaignMutation = useMutation({
    mutationFn: ({
      nextBrief,
      currentResult,
      currentSelectedVariantId,
      currentGeneratedImages,
      currentGeneratedVideos
    }: {
      nextBrief: CampaignBrief;
      currentResult: AgentResult;
      currentSelectedVariantId: string | null;
      currentGeneratedImages: Record<string, GeneratedImageResult>;
      currentGeneratedVideos: Record<string, GeneratedVideoResult>;
    }) => api.exportCampaign(nextBrief, currentResult, currentSelectedVariantId, currentGeneratedImages, currentGeneratedVideos)
  });

  useEffect(() => {
    let cancelled = false;

    async function start() {
      try {
        setLoading(true);
        const boot = await api.bootstrap();
        if (cancelled) return;

        const firstBrief: CampaignBrief = {
          ...boot.default_brief,
          market: "Thailand",
          primary_segment_id: "seg_value_seekers",
          channels: ["Meta", "Display"],
          product_ids: ["prod_tailored_trouser"],
          creative_instruction: "Manual campaign draft for next collection. Keep it premium and product-readable.",
          use_live_ai: false
        };
        setBootstrap(boot);
        setDataRefreshLabel(boot.insight_engine.last_refresh);
        setBrief(firstBrief);
        setImagePrompt(defaultImagePromptForBrief(firstBrief));
        setVideoPrompt(defaultVideoPromptForBrief(firstBrief));
        setBusyLabel("Scoring current draft");

        const generated = await api.generate(firstBrief);
        if (cancelled) return;
        setResult(generated);
        setSelectedVariantId(generated.variants[0]?.id ?? null);
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Unable to start the demo");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    start();
    return () => {
      cancelled = true;
    };
  }, []);

  const products = bootstrap?.products ?? [];
  const segments = bootstrap?.segments ?? [];
  const selectedProducts = useMemo(() => products.filter((product) => brief?.product_ids.includes(product.id)), [brief?.product_ids, products]);
  const primarySegment = segments.find((segment) => segment.id === brief?.primary_segment_id) ?? segments[0];
  const productRecommendations = useMemo(
    () => productRecommendationsForSegment(products, primarySegment),
    [primarySegment, products]
  );
  const selectedStrategy =
    bootstrap?.insight_engine.cards.find((strategy) => strategy.id === brief?.strategy_id) ?? bootstrap?.insight_engine.cards[0];
  const selectedVariant = result?.variants.find((variant) => variant.id === selectedVariantId) ?? result?.variants[0] ?? null;
  const selectedVariantProduct = selectedVariant ? products.find((product) => product.id === selectedVariant.product_id) : undefined;
  const selectedVariantSegment = selectedVariant ? segments.find((segment) => segment.id === selectedVariant.segment_id) : primarySegment;
  const previewsOutdated = useMemo(() => {
    if (!brief || !result?.brief) return false;
    return !briefMatchesResult(brief, result.brief);
  }, [brief, result?.brief]);
  const directionApplied = useMemo(() => {
    if (!brief || previewsOutdated) return false;
    return briefMatchesPatch(brief, todayRecommendation.brief_patch);
  }, [brief, previewsOutdated, todayRecommendation.brief_patch]);
  const visibleVariants = useMemo(
    () => [...(result?.variants ?? [])].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [result]
  );

  useEffect(() => {
    setProductFilter(RECOMMENDED_PRODUCT_FILTER);
  }, [brief?.primary_segment_id]);

  function updateBrief(patch: Partial<CampaignBrief>) {
    setBrief((current) => (current ? { ...current, ...patch } : current));
  }

  async function useTodaySuggestion() {
    if (!brief) return;
    const nextBrief = {
      ...buildBriefFromPatch(brief, todayRecommendation.brief_patch),
      use_live_ai: todayRecommendation.live_ai_used
    };
    setBriefRefineResult(null);
    setError(null);
    setImageError(null);
    setVideoError(null);
    setExportError(null);
    setLoading(true);
    setBusyLabel("Applying data-backed direction");
    try {
      setBrief(nextBrief);
      setImagePrompt(defaultImagePromptForBrief(nextBrief));
      setVideoPrompt(defaultVideoPromptForBrief(nextBrief));
      const generated = await generateMutation.mutateAsync(nextBrief);
      setResult(generated);
      setSelectedVariantId(generated.variants[0]?.id ?? null);
      setGeneratedImages({});
      setGeneratedVideos({});
      setExportResult(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to apply recommendation");
    } finally {
      setLoading(false);
    }
  }

  async function refreshInsightWithAI() {
    if (!brief) return;
    const previousRecommendation = todayRecommendation;
    setInsightError(null);
    setInsightRefreshNote("Checking live campaign, product, and audience signals...");
    try {
      const recommendation = await refreshInsightMutation.mutateAsync(brief);
      setTodayRecommendation(recommendation);
      setDataRefreshLabel("just now");
      const changed = recommendationSignature(previousRecommendation) !== recommendationSignature(recommendation);
      const source = recommendation.live_ai_used ? "Live OpenAI refresh" : "Backend data refresh";
      const target = describeRecommendationPatch(recommendation.brief_patch, products, segments);
      setInsightRefreshNote(
        changed
          ? `${source}: ${target}.`
          : `${source}: current data still points to the same campaign direction.`
      );
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Unable to refresh recommendation";
      setInsightError(message);
      setInsightRefreshNote("Refresh failed; showing the last successful recommendation.");
    }
  }

  async function refineBriefWithAI() {
    if (!brief) return;
    setBriefRefineError(null);
    try {
      const refined = await refineBriefMutation.mutateAsync({ nextBrief: brief, note: brief.creative_instruction });
      const nextBrief = {
        ...buildBriefFromPatch(brief, refined.brief_patch),
        use_live_ai: refined.live_ai_used
      };
      setBriefRefineResult(refined);
      setBrief(nextBrief);
      setImagePrompt(defaultImagePromptForBrief(nextBrief));
      setVideoPrompt(defaultVideoPromptForBrief(nextBrief));
    } catch (caught) {
      setBriefRefineError(caught instanceof Error ? caught.message : "Unable to refine brief");
    }
  }

  function toggleChannel(channel: Channel) {
    setBrief((current) => {
      if (!current) return current;
      const next = current.channels.includes(channel) ? current.channels.filter((item) => item !== channel) : [...current.channels, channel];
      return { ...current, channels: next.length ? next : [channel] };
    });
  }

  function toggleProduct(productId: string) {
    setBrief((current) => {
      if (!current) return current;
      const exists = current.product_ids.includes(productId);
      const next = exists ? current.product_ids.filter((id) => id !== productId) : [...current.product_ids, productId].slice(-4);
      return { ...current, product_ids: next.length ? next : [productId] };
    });
  }

  async function useSuggestedProducts() {
    if (!brief) return;
    const productIds = suggestedProductIds(productRecommendations);
    if (!productIds.length) return;
    const nextBrief = { ...brief, product_ids: productIds, generation_mode: "generate" as const, use_live_ai: false };
    setError(null);
    setImageError(null);
    setVideoError(null);
    setExportError(null);
    setProductFilter(RECOMMENDED_PRODUCT_FILTER);
    setLoading(true);
    setBusyLabel("Applying suggested products");
    try {
      setBrief(nextBrief);
      const generated = await generateMutation.mutateAsync(nextBrief);
      setResult(generated);
      setSelectedVariantId(generated.variants[0]?.id ?? null);
      setGeneratedImages({});
      setGeneratedVideos({});
      setExportResult(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to apply suggested products");
    } finally {
      setLoading(false);
    }
  }

  function updateModelPresentation(modelPresentation: CampaignBrief["model_presentation"]) {
    if (!brief) return;
    const nextBrief = { ...brief, model_presentation: modelPresentation };
    setBrief(nextBrief);
    setImagePrompt(defaultImagePromptForBrief(nextBrief));
    setVideoPrompt(defaultVideoPromptForBrief(nextBrief));
  }

  async function runGeneration(mode: "generate" | "optimize", live = false) {
    if (!brief) return;
    setError(null);
    setLoading(true);
    setBusyLabel(live ? "Improving copy and re-ranking" : mode === "optimize" ? "Optimizing forecast" : "Recalculating forecast");
    try {
      const nextBrief = { ...brief, generation_mode: mode, use_live_ai: live };
      setBrief(nextBrief);
      const generated = await generateMutation.mutateAsync(nextBrief);
      setResult(generated);
      setSelectedVariantId(generated.variants[0]?.id ?? null);
      setGeneratedImages({});
      setGeneratedVideos({});
      setExportResult(null);
      if (live) {
        setBusyLabel("OpenAI copy polish complete");
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to generate previews");
    } finally {
      setLoading(false);
    }
  }

  async function generateSelectedImage() {
    if (!brief || !result) return;
    setImageError(null);
    if (previewsOutdated) {
      setImageError("Refresh ad previews before creating platform images.");
      return;
    }
    const targetVariants = topVariantsForSelectedChannels(visibleVariants, brief.channels);
    if (!targetVariants.length) {
      setImageError("No platform previews are ready for image generation.");
      return;
    }
    try {
      const generatedEntries: Record<string, GeneratedImageResult> = {};
      for (const variant of targetVariants) {
        const image = await generateImageMutation.mutateAsync({ nextBrief: brief, variant, promptNote: imagePrompt });
        generatedEntries[variant.id] = image;
      }
      setGeneratedImages((current) => ({ ...current, ...generatedEntries }));
      setGeneratedVideos((current) => {
        const next = { ...current };
        for (const variant of targetVariants) {
          delete next[variant.id];
        }
        return next;
      });
      setSelectedVariantId(targetVariants[0].id);
    } catch (caught) {
      setImageError(caught instanceof Error ? caught.message : "Unable to create platform images");
    }
  }

  async function generateSelectedVideo() {
    if (!brief || !result) return;
    setVideoError(null);
    if (previewsOutdated) {
      setVideoError("Refresh ad previews before creating a TikTok video.");
      return;
    }
    const tikTokVariant = visibleVariants.find((variant) => variant.channel === "TikTok");
    if (!tikTokVariant) {
      setVideoError("Select TikTok as a platform and refresh ad previews before creating video.");
      return;
    }
    try {
      setSelectedVariantId(tikTokVariant.id);
      const generatedImageUrl = generatedImages[tikTokVariant.id]?.image_url ?? null;
      const useProductOnlyReference = brief.model_presentation === "product_only" && Boolean(generatedImageUrl);
      const referenceImage = useProductOnlyReference ? generatedImageUrl : null;
      const referenceImageRole = useProductOnlyReference ? "first_frame" : "text_prompt";
      const video = await generateVideoMutation.mutateAsync({
        nextBrief: brief,
        variant: tikTokVariant,
        promptNote: videoPrompt,
        referenceImageUrl: referenceImage,
        referenceImageRole
      });
      setGeneratedVideos((current) => ({ ...current, [tikTokVariant.id]: video }));
    } catch (caught) {
      setVideoError(caught instanceof Error ? caught.message : "Unable to create TikTok video");
    }
  }

  async function exportCampaignPackage() {
    if (!brief || !result) return;
    setExportError(null);
    try {
      const exported = await exportCampaignMutation.mutateAsync({
        nextBrief: brief,
        currentResult: result,
        currentSelectedVariantId: selectedVariant?.id ?? selectedVariantId,
        currentGeneratedImages: generatedImages,
        currentGeneratedVideos: generatedVideos
      });
      setExportResult(exported);
      try {
        await downloadExportPackage(exported);
      } catch {
        setExportError("Export saved. Use the download link below if the browser did not start the download automatically.");
      }
    } catch (caught) {
      setExportResult(null);
      setExportError(caught instanceof Error ? caught.message : "Unable to export campaign package");
    }
  }

  if (!bootstrap || !brief) return <LoadingScreen label={busyLabel} error={error} />;

  const visibleRefreshLabel = refreshInsightMutation.isPending ? "refreshing now" : dataRefreshLabel;

  return (
    <div className="retail-console">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-icon">
            <Sparkles size={18} />
          </div>
          <div>
            <strong>SEA Creative Hub</strong>
            <span>Retail ad studio</span>
          </div>
        </div>

        <nav className="main-nav" aria-label="Main navigation">
          {navItems.map((item) => (
            <button className={item.active ? "active" : ""} key={item.label}>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-card">
          <ShieldCheck size={17} />
          <strong>Retail data connected</strong>
          <span>Campaign history, catalog, audience profiles</span>
        </div>
      </aside>

      <main className="console-main">
        <header className="hero-bar">
          <div>
            <h1>From trend signal to campaign-ready creative</h1>
            <p>A marketer starts with current performance signals, shapes the brief, generates platform assets, and exports a launch package.</p>
          </div>
          <div className="header-status" aria-label="Workspace status">
            <span>
              <Check size={14} />
              {refreshInsightMutation.isPending ? "Refreshing data..." : `Data refreshed ${dataRefreshLabel}`}
            </span>
            <span>{visibleVariants.length} previews ready</span>
          </div>
        </header>

        {error ? <div className="error-banner">{error}</div> : null}

        <TodayRecommendation
          campaignCount={bootstrap.campaign_count}
          error={insightError}
          recommendation={todayRecommendation}
          refreshLabel={visibleRefreshLabel}
          refreshNote={insightRefreshNote}
          refreshing={refreshInsightMutation.isPending}
          applying={loading}
          directionApplied={directionApplied}
          strategy={selectedStrategy}
          onRefresh={refreshInsightWithAI}
          onUseSuggestion={useTodaySuggestion}
        />

        <section className="console-grid">
          <div className="left-column">
            <BriefBuilder
              brief={brief}
              loading={loading}
              productFilter={productFilter}
              productRecommendations={productRecommendations}
              segments={segments}
              selectedProducts={selectedProducts}
              primarySegment={primarySegment}
              selectedStrategy={selectedStrategy}
              previewsOutdated={previewsOutdated}
              updateBrief={updateBrief}
              updateProductFilter={setProductFilter}
              toggleChannel={toggleChannel}
              toggleProduct={toggleProduct}
              briefRefineBusy={refineBriefMutation.isPending}
              briefRefineError={briefRefineError}
              briefRefineResult={briefRefineResult}
              onRefineBrief={refineBriefWithAI}
              onUseSuggestedProducts={useSuggestedProducts}
              onGenerate={() => runGeneration("generate")}
            />
          </div>

          <div className="right-column">
            <RationalePanel
              variant={selectedVariant}
              product={selectedVariantProduct}
              segment={selectedVariantSegment}
              imageProvider={brief.image_provider}
              modelPresentation={brief.model_presentation}
              generatedImage={!previewsOutdated && selectedVariant ? generatedImages[selectedVariant.id] : undefined}
              generatedVideo={!previewsOutdated && selectedVariant ? generatedVideos[selectedVariant.id] : undefined}
              imagePrompt={imagePrompt}
              videoPrompt={videoPrompt}
              aiForecastUsed={Boolean(result?.live_ai_used) && !previewsOutdated}
              imageBusy={generateImageMutation.isPending}
              imageError={imageError}
              previewsOutdated={previewsOutdated}
              updating={loading}
              updateLabel={busyLabel}
              videoBusy={generateVideoMutation.isPending}
              videoError={videoError}
              onImagePromptChange={setImagePrompt}
              onImageProviderChange={(imageProvider) => updateBrief({ image_provider: imageProvider })}
              onModelPresentationChange={updateModelPresentation}
              onVideoPromptChange={setVideoPrompt}
              onGenerateImage={generateSelectedImage}
              onGenerateVideo={generateSelectedVideo}
            />
            <PreviewResults
              variants={visibleVariants}
              products={products}
              segments={segments}
              selectedVariantId={selectedVariant?.id}
              exportBusy={exportCampaignMutation.isPending}
              exportError={exportError}
              exportResult={exportResult}
              generatedImages={previewsOutdated ? {} : generatedImages}
              generatedVideos={previewsOutdated ? {} : generatedVideos}
              previewsOutdated={previewsOutdated}
              updating={loading}
              updateLabel={busyLabel}
              onExport={exportCampaignPackage}
              onSelect={setSelectedVariantId}
            />
          </div>
        </section>
      </main>
    </div>
  );
}

function buildBriefFromPatch(current: CampaignBrief, patch: BriefPatch): CampaignBrief {
  return {
    ...current,
    ...patch,
    channels: patch.channels?.length ? patch.channels : current.channels,
    product_ids: patch.product_ids?.length ? patch.product_ids : current.product_ids,
    generation_mode: "generate",
    use_live_ai: false
  };
}

function defaultImagePromptForBrief(brief: CampaignBrief) {
  if (brief.model_presentation === "product_only") {
    return "Keep the selected product unchanged. Create a clean product-only flat lay or mannequin image with crisp fabric texture and campaign-ready lighting.";
  }
  const model = brief.model_presentation === "male_model" ? "male model" : "female model";
  return `Keep the selected product unchanged. Use a ${model}, natural pose, clean SEA retail styling, readable garment details, and campaign-ready lighting.`;
}

function defaultVideoPromptForBrief(brief: CampaignBrief) {
  if (brief.model_presentation === "product_only") {
    return "Use the generated product image as the first frame. Add fabric movement, close detail, subtle camera push-in, and no person or face.";
  }
  const model = brief.model_presentation === "male_model" ? "male model" : "female model";
  return `Use privacy-safe ${model} framing. Focus on natural garment movement, fabric detail, and a short social-commerce camera move.`;
}

function briefMatchesResult(current: CampaignBrief, generated: CampaignBrief) {
  return JSON.stringify(briefSignature(current)) === JSON.stringify(briefSignature(generated));
}

function briefMatchesPatch(brief: CampaignBrief, patch: BriefPatch) {
  if (patch.market && brief.market !== patch.market) return false;
  if (patch.objective && brief.objective !== patch.objective) return false;
  if (patch.primary_segment_id && brief.primary_segment_id !== patch.primary_segment_id) return false;
  if (patch.strategy_id && brief.strategy_id !== patch.strategy_id) return false;
  if (patch.creative_instruction && brief.creative_instruction !== patch.creative_instruction) return false;
  if (patch.model_presentation && brief.model_presentation !== patch.model_presentation) return false;
  if (patch.channels?.length && !sameStringSet(brief.channels, patch.channels)) return false;
  if (patch.product_ids?.length && !sameStringSet(brief.product_ids, patch.product_ids)) return false;
  return true;
}

function sameStringSet(left: string[], right: string[]) {
  if (left.length !== right.length) return false;
  const normalizedLeft = [...left].sort();
  const normalizedRight = [...right].sort();
  return normalizedLeft.every((value, index) => value === normalizedRight[index]);
}

function recommendationSignature(recommendation: TodayRecommendationResult) {
  return JSON.stringify({
    title: recommendation.title,
    patch: {
      ...recommendation.brief_patch,
      channels: recommendation.brief_patch.channels ? [...recommendation.brief_patch.channels].sort() : undefined,
      product_ids: recommendation.brief_patch.product_ids ? [...recommendation.brief_patch.product_ids].sort() : undefined
    }
  });
}

function describeRecommendationPatch(patch: BriefPatch, products: Product[], segments: Segment[]) {
  const segmentName = segments.find((segment) => segment.id === patch.primary_segment_id)?.name;
  const productNames = (patch.product_ids ?? [])
    .map((id) => products.find((product) => product.id === id)?.name)
    .filter(Boolean)
    .slice(0, 2);
  const parts = [
    patch.market,
    segmentName,
    patch.channels?.join(" + "),
    productNames.length ? productNames.join(", ") : null
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : "recommendation updated";
}

function briefSignature(brief: CampaignBrief) {
  return {
    market: brief.market,
    objective: brief.objective,
    primary_segment_id: brief.primary_segment_id,
    channels: [...brief.channels].sort(),
    product_ids: [...brief.product_ids].sort(),
    strategy_id: brief.strategy_id,
    creative_instruction: brief.creative_instruction,
    image_provider: brief.image_provider,
    model_presentation: brief.model_presentation
  };
}

function topVariantsForSelectedChannels(variants: CreativeVariant[], channels: Channel[]) {
  const seen = new Set<Channel>();
  const targets: CreativeVariant[] = [];
  for (const channel of channels) {
    if (seen.has(channel)) continue;
    const variant = variants.find((item) => item.channel === channel);
    if (variant) {
      targets.push(variant);
      seen.add(channel);
    }
  }
  return targets;
}

async function downloadExportPackage(exported: ExportCampaignResult) {
  const resolvedUrl = imageUrl(exported.download_url);
  let downloadUrl = resolvedUrl;
  let shouldRevoke = false;

  if (!resolvedUrl.startsWith("blob:") && !resolvedUrl.startsWith("data:")) {
    const response = await fetch(resolvedUrl);
    if (!response.ok) throw new Error("The export was created, but the browser could not download it.");
    const blob = await response.blob();
    downloadUrl = URL.createObjectURL(blob);
    shouldRevoke = true;
  }

  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = exported.filename;
  document.body.appendChild(link);
  link.click();
  link.remove();

  if (shouldRevoke) {
    window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
  }
}
