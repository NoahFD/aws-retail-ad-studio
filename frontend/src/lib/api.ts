export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const USE_DEMO_API = import.meta.env.PROD && !import.meta.env.VITE_API_BASE_URL;

export type Channel = "Meta" | "TikTok" | "Display" | "Email";
export type ImageProvider = "gpt-image-2" | "aws-bedrock-ready";
export type ModelPresentation = "female_model" | "male_model" | "product_only";

export type CampaignBrief = {
  campaign_name: string;
  objective: "Sales" | "Traffic" | "Awareness" | "Retention";
  market: string;
  primary_segment_id: string;
  additional_segment_id: string | null;
  channels: Channel[];
  product_ids: string[];
  budget_sgd: number;
  trend_window: string;
  tone: string;
  strategy_id: string;
  creative_instruction: string;
  image_provider: ImageProvider;
  model_presentation: ModelPresentation;
  use_live_ai: boolean;
  generation_mode: "generate" | "optimize";
};

export type Product = {
  id: string;
  name: string;
  category: string;
  price_sgd: number;
  description: string;
  image_url: string;
  tags: string[];
  margin: number;
  inventory_score: number;
};

export type Segment = {
  id: string;
  name: string;
  age_range: string;
  markets: string[];
  size_millions: number;
  profile: string;
  preferred_channels: Channel[];
  copy_preferences: string[];
  price_sensitivity: string;
  creative_notes: string;
};

export type DataSource = {
  name: string;
  type: string;
  status: "connected" | "warning" | "offline";
  records: number;
  freshness: string;
  aws_target: string;
};

export type InsightMetric = {
  label: string;
  value: string;
  delta: string;
  sentiment: "positive" | "neutral" | "negative";
};

export type CreativeVariant = {
  id: string;
  channel: Channel;
  format: string;
  product_id: string;
  segment_id: string;
  headline: string;
  body: string;
  cta: string;
  visual_direction: string;
  image_style: string;
  copy_style: string;
  predicted_ctr: number;
  predicted_roas: number;
  predicted_lift: number;
  confidence: number;
  rationale: string;
  image_prompt?: string | null;
  image_provider?: string | null;
  rank?: number;
};

export type GeneratedImageResult = {
  image_url: string;
  provider: string;
  model: string;
  size: string;
  quality: string;
  prompt: string;
  prompt_note?: string;
  generation_mode?: string;
  source_image_url?: string;
  model_presentation?: ModelPresentation | string;
  cost_guardrail: string;
};

export type GeneratedVideoResult = {
  video_url: string;
  provider: string;
  model: string;
  status: "ready" | "processing" | "demo_ready" | string;
  task_id?: string | null;
  live_provider_used: boolean;
  fallback_reason?: string | null;
  duration_seconds: number;
  ratio: string;
  resolution: string;
  prompt: string;
  reference_image_url?: string | null;
  reference_image_role?: string | null;
  model_presentation?: ModelPresentation | string;
  aws_ready_target: string;
  cost_guardrail: string;
};

export type ExportCampaignResult = {
  export_id: string;
  filename: string;
  download_url: string;
  storage_target: string;
  aws_ready_target: string;
  file_size_bytes: number;
  cost_guardrail: string;
};

export type BriefPatch = Partial<
  Pick<
    CampaignBrief,
    "market" | "objective" | "channels" | "primary_segment_id" | "product_ids" | "strategy_id" | "creative_instruction" | "model_presentation"
  >
>;

export type TodayRecommendationResult = {
  title: string;
  summary: string;
  confidence: number;
  signals: Array<{ label: string; value: string }>;
  brief_patch: BriefPatch;
  reasoning: string[];
  live_ai_used: boolean;
  errors: string[];
  cost_guardrail: string;
};

export type BriefRefineResult = {
  brief_patch: BriefPatch;
  rewritten_note: string;
  reasoning: string[];
  live_ai_used: boolean;
  errors: string[];
  cost_guardrail: string;
};

export type StrategyCard = {
  id: string;
  title: string;
  tag: string;
  recommendation: string;
  expected_gain: string;
  confidence: number;
  evidence: string[];
  brief_hint: string;
};

export type InsightEngine = {
  last_refresh: string;
  cadence: string;
  next_refresh: string;
  summary: string;
  baseline: {
    roas: number;
    ctr: number;
    cpa: number;
  };
  cards: StrategyCard[];
};

export type BootstrapPayload = {
  products: Product[];
  segments: Segment[];
  data_sources: DataSource[];
  campaign_count: number;
  default_brief: CampaignBrief;
  insight_engine: InsightEngine;
  aws_mapping: {
    current: string;
    future: string[];
  };
  video_generation?: {
    provider: string;
    label: string;
    model: string;
    status: string;
    live_enabled: boolean;
    configured: boolean;
  };
};

export type AgentResult = {
  brief: CampaignBrief;
  plan: Record<string, string | number | string[]>;
  insights: InsightMetric[];
  variants: CreativeVariant[];
  top_patterns: Array<Record<string, string | number>>;
  agent_steps: Array<{ name: string; status: string; detail: string }>;
  data_sources: DataSource[];
  live_ai_used: boolean;
  cost_guardrail: string;
  errors: string[];
};

const demoProducts: Product[] = [
  {
    id: "prod_linen_shirt",
    name: "Linen Ease Shirt",
    category: "Shirts",
    price_sgd: 69,
    description: "Lightweight linen-blend shirt with relaxed tailoring for humid city days.",
    image_url: "/static/products/linen-shirt.png",
    tags: ["linen", "workwear", "best-seller", "breathable"],
    margin: 0.62,
    inventory_score: 91
  },
  {
    id: "prod_batik_maxi",
    name: "Batik Flow Maxi Dress",
    category: "Dresses",
    price_sgd: 129,
    description: "Fluid printed maxi dress designed for weekend dinners and festive gatherings.",
    image_url: "/static/products/batik-maxi.png",
    tags: ["dress", "occasion", "batik-inspired", "social"],
    margin: 0.58,
    inventory_score: 84
  },
  {
    id: "prod_tailored_trouser",
    name: "City Tailored Trouser",
    category: "Bottoms",
    price_sgd: 89,
    description: "Structured wide-leg trouser with all-day comfort and crease-resistant finish.",
    image_url: "/static/products/tailored-trouser.png",
    tags: ["workwear", "tailored", "capsule", "premium"],
    margin: 0.55,
    inventory_score: 78
  },
  {
    id: "prod_resort_overshirt",
    name: "Resort Linen Overshirt",
    category: "Menswear",
    price_sgd: 79,
    description: "Relaxed short-sleeve overshirt with a breathable linen texture.",
    image_url: "/static/products/resort-overshirt.png",
    tags: ["menswear", "linen", "weekend", "summer"],
    margin: 0.57,
    inventory_score: 88
  },
  {
    id: "prod_pleated_skirt",
    name: "Soft Pleat Midi Skirt",
    category: "Skirts",
    price_sgd: 95,
    description: "Soft pleated midi skirt with movement-led drape for office and evening wear.",
    image_url: "/static/products/pleated-skirt.png",
    tags: ["midi", "workwear", "movement", "capsule"],
    margin: 0.6,
    inventory_score: 73
  },
  {
    id: "prod_modest_tunic",
    name: "Airweave Modest Tunic",
    category: "Tops",
    price_sgd: 82,
    description: "Longline tunic with breathable coverage and a polished layered silhouette.",
    image_url: "/static/products/modest-tunic.png",
    tags: ["modest", "breathable", "layering", "occasion"],
    margin: 0.59,
    inventory_score: 86
  }
];

const demoSegments: Segment[] = [
  {
    id: "seg_urban_professionals",
    name: "Urban Professionals",
    age_range: "25-34",
    markets: ["Singapore", "Malaysia", "Thailand"],
    size_millions: 3.2,
    profile: "Office-to-evening shoppers who prefer versatile pieces and fast delivery",
    preferred_channels: ["Meta", "Email", "Display"],
    copy_preferences: ["benefit-led", "new-arrival", "editorial"],
    price_sensitivity: "Medium",
    creative_notes: "Clean editorial images, outfit utility, work-to-weekend framing"
  },
  {
    id: "seg_style_enthusiasts",
    name: "Style Enthusiasts",
    age_range: "18-24",
    markets: ["Singapore", "Indonesia", "Philippines"],
    size_millions: 2.7,
    profile: "Trend-led shoppers who save social posts and react to creator styling",
    preferred_channels: ["TikTok", "Meta"],
    copy_preferences: ["trend-led", "promo-urgency", "new-arrival"],
    price_sensitivity: "Medium",
    creative_notes: "Motion-first styling, creator framing, bold crop, social proof"
  },
  {
    id: "seg_value_seekers",
    name: "Value Seekers",
    age_range: "25-35",
    markets: ["Malaysia", "Indonesia", "Thailand"],
    size_millions: 4.6,
    profile: "Practical shoppers who compare price, promotion, and quality",
    preferred_channels: ["Display", "Email", "Meta"],
    copy_preferences: ["value-led", "promo-urgency", "benefit-led"],
    price_sensitivity: "High",
    creative_notes: "Clear offer framing, comparison language, product durability cues"
  },
  {
    id: "seg_modest_fashion",
    name: "Modest Fashion Shoppers",
    age_range: "22-39",
    markets: ["Malaysia", "Indonesia", "Singapore"],
    size_millions: 5.1,
    profile: "Occasion-led shoppers looking for breathable, polished coverage",
    preferred_channels: ["Meta", "TikTok", "Email"],
    copy_preferences: ["occasion-led", "editorial", "benefit-led"],
    price_sensitivity: "Medium",
    creative_notes: "Soft movement, breathable fabric cues, festive and office styling"
  }
];

const demoDataSources: DataSource[] = [
  { name: "Connected data", type: "Synced", status: "connected", records: 46, freshness: "15 min ago", aws_target: "Amazon S3 + Glue" },
  { name: "Sales & Orders", type: "Campaign history", status: "connected", records: 36, freshness: "15 min ago", aws_target: "S3 + Glue" },
  { name: "Product Catalog", type: "Images + details", status: "connected", records: 6, freshness: "15 min ago", aws_target: "DynamoDB + S3" },
  { name: "Customer Segments", type: "Audience profiles", status: "connected", records: 4, freshness: "15 min ago", aws_target: "Aurora or CDP export" },
  { name: "Ad Platforms", type: "Meta, TikTok, Google", status: "connected", records: 3, freshness: "15 min ago", aws_target: "EventBridge connectors" },
  { name: "Creative Library", type: "Approved assets", status: "connected", records: 12840, freshness: "15 min ago", aws_target: "S3 + CloudFront" }
];

const demoStrategies: StrategyCard[] = [
  {
    id: "trend_window",
    title: "Catch the trend window",
    tag: "Recommended",
    recommendation: "Start from the strongest recent pattern, then adapt it across the platforms selected for this campaign.",
    expected_gain: "+28% conversion lift",
    confidence: 92,
    evidence: [
      "Short video and hero-led layouts are outperforming static repeats.",
      "New-arrival copy is lifting click intent in the current trend window.",
      "Urban Professionals is a 3.2M audience across Singapore, Malaysia."
    ],
    brief_hint: "Show confident SEA styling, readable products, and concise premium copy."
  },
  {
    id: "product_winner",
    title: "Scale best-selling products",
    tag: "Sales lift",
    recommendation: "Push linen and batik products where product readiness and demand are strongest.",
    expected_gain: "+18% ROAS vs baseline",
    confidence: 86,
    evidence: ["Linen and batik products show strong search growth.", "Inventory readiness is above 84.", "Meta and Email provide efficient reach."],
    brief_hint: "Feature best-selling products, clear fabric benefits, and fast styling use cases."
  },
  {
    id: "creative_fatigue",
    title: "Refresh fatigued creative",
    tag: "Optimization",
    recommendation: "Replace older static assets with motion-led and editorial variants for high-fit audiences.",
    expected_gain: "-9% estimated CPA",
    confidence: 81,
    evidence: ["Repeated static formats show softer CTR.", "Short video improves social engagement.", "Fresh product crops reduce creative fatigue."],
    brief_hint: "Use fresh crops, lighter copy, and more motion-led fashion styling."
  }
];

const defaultBrief: CampaignBrief = {
  campaign_name: "SEA Trend Window Launch",
  objective: "Sales",
  market: "Singapore",
  primary_segment_id: "seg_urban_professionals",
  additional_segment_id: "seg_style_enthusiasts",
  channels: ["Meta", "TikTok", "Display", "Email"],
  product_ids: ["prod_linen_shirt", "prod_batik_maxi", "prod_tailored_trouser", "prod_resort_overshirt"],
  budget_sgd: 1500,
  trend_window: "Next 14 days",
  tone: "Premium practical",
  strategy_id: "trend_window",
  creative_instruction: "Show confident SEA styling, readable products, and concise premium copy.",
  image_provider: "gpt-image-2",
  model_presentation: "female_model",
  use_live_ai: false,
  generation_mode: "generate"
};

function demoBootstrap(): BootstrapPayload {
  return {
    products: demoProducts,
    segments: demoSegments,
    data_sources: demoDataSources,
    campaign_count: 36,
    default_brief: defaultBrief,
    insight_engine: {
      last_refresh: "15 min ago",
      cadence: "Every 15 min when connected to ad platforms",
      next_refresh: "14 min",
      summary: "The engine scores recent campaign performance, catalog readiness, and segment fit, then proposes a starting strategy before the marketer briefs the campaign.",
      baseline: { roas: 6.5, ctr: 2.31, cpa: 6.21 },
      cards: demoStrategies
    },
    aws_mapping: {
      current: "Local demo data bundled for Netlify testing",
      future: ["Amazon S3", "AWS Glue", "Amazon Bedrock", "Amazon Nova Reel", "EventBridge", "App Runner"]
    },
    video_generation: {
      provider: "demo-cached",
      label: "Cached demo video",
      model: "local-demo-mp4",
      status: "Netlify demo fallback; local backend can call Seedance or AWS Nova Reel.",
      live_enabled: false,
      configured: true
    }
  };
}

function formatForChannel(channel: Channel) {
  if (channel === "TikTok") return "Short video";
  if (channel === "Meta") return "Social carousel";
  if (channel === "Display") return "Display creative";
  return "Email creative";
}

function segmentForVariant(brief: CampaignBrief) {
  return demoSegments.find((segment) => segment.id === brief.primary_segment_id) ?? demoSegments[0];
}

function demoGenerate(brief: CampaignBrief): AgentResult {
  const strategy = demoStrategies.find((item) => item.id === brief.strategy_id) ?? demoStrategies[0];
  const channelsToUse = brief.channels.length ? brief.channels : defaultBrief.channels;
  const promptIntent = brief.creative_instruction.toLowerCase();
  const variants = demoVariantSlots(brief, channelsToUse).map(({ channel, product }, index) => {
    const segment = segmentForVariant(brief);
    const roas = Math.min(6.8 - index * 0.18 + product.inventory_score / 500, 6.8);
    const ctr = Math.max(0.018, 0.0376 - index * 0.0021 + (segment.preferred_channels.includes(channel) ? 0.001 : 0));
    const liftValue = Math.max(0.18, 0.48 - index * 0.035);
    return {
      id: `${channel.toLowerCase()}-${product.id}-${index}`,
      channel,
      format: formatForChannel(channel),
      product_id: product.id,
      segment_id: segment.id,
      headline: `Made for now: ${product.name}`,
      body: `A data-backed ${product.category.toLowerCase()} story for ${segment.name.toLowerCase()} in ${brief.market}.`,
      cta: channel === "Email" ? "Explore picks" : "Shop the edit",
      visual_direction: `${channel} creative using ${product.name}; ${brief.creative_instruction}`,
      image_style: channel === "TikTok" ? "creator-motion" : "editorial",
      copy_style: "new-arrival",
      predicted_ctr: ctr,
      predicted_roas: roas,
      predicted_lift: liftValue,
      confidence: Math.round(92 - index * 4),
      rationale: `Uses ${strategy.title.toLowerCase()} with ${product.name} because similar campaigns over-indexed for ${segment.name} on ${channel}. Creative direction: ${brief.creative_instruction}`,
      image_prompt: `Create a polished SEA fashion retail ad image for ${channel}. Product: ${product.name}. Model presentation: ${modelPresentationLabel(brief.model_presentation)}. Audience: ${segment.name} in ${brief.market}. Creative direction from marketer: ${brief.creative_instruction}.`,
      image_provider: brief.image_provider
    } satisfies CreativeVariant;
  });
  const ranked = variants
    .sort((a, b) => {
      const aIntentBoost = promptIntent.includes(a.channel.toLowerCase()) ? 1 : 0;
      const bIntentBoost = promptIntent.includes(b.channel.toLowerCase()) ? 1 : 0;
      return b.predicted_roas + bIntentBoost - (a.predicted_roas + aIntentBoost);
    })
    .map((variant, index) => ({ ...variant, rank: index + 1 }));
  const leadVariant = ranked[0];

  return {
    brief,
    plan: {
      narrative: strategy.recommendation,
      primary_channel: leadVariant?.channel ?? channelsToUse[0] ?? "Meta",
      primary_format: leadVariant?.format ?? formatForChannel(channelsToUse[0] ?? "Meta"),
      copy_style: leadVariant?.copy_style ?? "new-arrival",
      projected_roas: 10,
      projected_ctr: 0.0317,
      projected_lift: 0.3
    },
    insights: [
      { label: "ROAS", value: "10.0x", delta: "+54%", sentiment: "positive" },
      { label: "CTR", value: "3.17%", delta: "+37%", sentiment: "positive" },
      { label: "Lift", value: "+30%", delta: "forecast", sentiment: "positive" }
    ],
    variants: ranked,
    top_patterns: [
      { channel: leadVariant?.channel ?? "Meta", format: leadVariant?.format ?? "Social carousel", roas: leadVariant?.predicted_roas ?? 6.8 },
      { channel: "TikTok", format: "Short video", ctr: 3.76 }
    ],
    agent_steps: [
      { name: "Read retail signals", status: "complete", detail: "Loaded campaign history, catalog, and segment profiles." },
      { name: "Recommend direction", status: "complete", detail: strategy.recommendation },
      { name: "Create ad previews", status: "complete", detail: `Prepared ${ranked.length} focused previews for the selected audience and platforms.` }
    ],
    data_sources: demoDataSources,
    live_ai_used: brief.use_live_ai,
    cost_guardrail: "Static Netlify demo mode",
    errors: []
  };
}

function productsForDemoBrief(brief: CampaignBrief) {
  const selected = brief.product_ids
    .map((productId) => demoProducts.find((product) => product.id === productId))
    .filter((product): product is Product => Boolean(product));
  return selected.length ? selected : demoProducts.slice(0, 4);
}

function demoVariantSlots(brief: CampaignBrief, channels: Channel[]) {
  const products = productsForDemoBrief(brief);
  if (!products.length) return [];

  const roundLimit =
    channels.length === 1 ? Math.min(3, products.length) : channels.length === 2 ? Math.min(2, products.length) : products.length === 1 ? 1 : 2;
  const targetCount = Math.min(6, channels.length * roundLimit, channels.length * products.length);
  const slots: Array<{ channel: Channel; product: Product }> = [];
  const used = new Set<string>();
  let cursor = 0;

  for (let round = 0; round < roundLimit; round += 1) {
    for (const channel of channels) {
      if (slots.length >= targetCount) return slots;
      const next = pickNextDemoProduct(products, channel, used, cursor);
      if (!next.product) continue;
      used.add(`${channel}:${next.product.id}`);
      cursor = next.nextCursor;
      slots.push({ channel, product: next.product });
    }
  }

  return slots;
}

function pickNextDemoProduct(products: Product[], channel: Channel, used: Set<string>, startIndex: number) {
  for (let offset = 0; offset < products.length; offset += 1) {
    const candidateIndex = (startIndex + offset) % products.length;
    const product = products[candidateIndex];
    if (!used.has(`${channel}:${product.id}`)) {
      return { product, nextCursor: candidateIndex + 1 };
    }
  }
  return { product: null, nextCursor: startIndex };
}

function demoRecommendation(): TodayRecommendationResult {
  return {
    title: "Launch a TikTok-first Malaysia edit while the style trend is still moving.",
    summary: "Current and historical campaign data points to Style Enthusiasts, short video, and texture-led product shots as the strongest starting point.",
    confidence: 92,
    signals: [
      { label: "Signal", value: "Short video is outperforming static repeats." },
      { label: "Audience", value: "Style Enthusiasts show high fit for TikTok and Meta." },
      { label: "Products", value: "Batik, linen, trouser, and skirt assets are campaign-ready." }
    ],
    brief_patch: {
      market: "Malaysia",
      channels: ["Meta", "TikTok"],
      primary_segment_id: "seg_style_enthusiasts",
      product_ids: ["prod_batik_maxi", "prod_tailored_trouser", "prod_resort_overshirt", "prod_pleated_skirt"],
      strategy_id: "trend_window",
      creative_instruction: "TikTok-first Malaysia launch for Style Enthusiasts. Make it premium, less posed, show product texture and upbeat city energy."
    },
    reasoning: [
      "Short video is a strong recent format in the campaign history.",
      "Style Enthusiasts prefer TikTok and Meta with trend-led creative.",
      "Selected products have strong visual assets and inventory readiness."
    ],
    live_ai_used: false,
    errors: [],
    cost_guardrail: "Static Netlify fallback. Local backend refreshes this with OpenAI."
  };
}

function demoRefineBrief(note: string, brief: CampaignBrief): BriefRefineResult {
  const lowered = note.toLowerCase();
  const patch: BriefPatch = { creative_instruction: note || brief.creative_instruction };
  if (lowered.includes("indonesia")) patch.market = "Indonesia";
  else if (lowered.includes("malaysia")) patch.market = "Malaysia";
  else if (lowered.includes("thailand")) patch.market = "Thailand";
  else if (lowered.includes("singapore")) patch.market = "Singapore";
  if (lowered.includes("tiktok")) patch.channels = ["Meta", "TikTok"];
  if (lowered.includes("style") || lowered.includes("young") || lowered.includes("creator")) patch.primary_segment_id = "seg_style_enthusiasts";
  if (lowered.includes("value") || lowered.includes("promo")) patch.primary_segment_id = "seg_value_seekers";
  if (lowered.includes("modest") || lowered.includes("raya")) patch.primary_segment_id = "seg_modest_fashion";
  if (lowered.includes("male model") || lowered.includes("men model")) patch.model_presentation = "male_model";
  if (lowered.includes("female model") || lowered.includes("women model")) patch.model_presentation = "female_model";
  if (lowered.includes("product only") || lowered.includes("no model") || lowered.includes("just the shirt") || lowered.includes("flat lay")) {
    patch.model_presentation = "product_only";
  }
  if (lowered.includes("batik") || lowered.includes("dress")) {
    patch.product_ids = ["prod_batik_maxi", "prod_pleated_skirt", "prod_linen_shirt", "prod_tailored_trouser"];
  }
  patch.strategy_id = lowered.includes("refresh") ? "creative_fatigue" : "trend_window";
  return {
    brief_patch: patch,
    rewritten_note: String(patch.creative_instruction),
    reasoning: [
      "The note was mapped to campaign fields using demo rules.",
      "Run locally to use OpenAI for this brief-refinement step."
    ],
    live_ai_used: false,
    errors: [],
    cost_guardrail: "Static Netlify fallback. Local backend refines this with OpenAI."
  };
}

function demoExportCampaign(
  brief: CampaignBrief,
  result: AgentResult,
  selectedVariantId: string | null,
  generatedImages: Record<string, GeneratedImageResult>,
  generatedVideos: Record<string, GeneratedVideoResult>
): ExportCampaignResult {
  const slug = slugify(brief.campaign_name);
  const filename = `${slug}-${Date.now()}.json`;
  const selectedVariant = result.variants.find((variant) => variant.id === selectedVariantId) ?? result.variants[0] ?? null;
  const packageBody = {
    exported_at: new Date().toISOString(),
    campaign_name: brief.campaign_name,
    storage_target: "Browser download",
    aws_ready_target: `s3://retail-creative-exports/${filename}`,
    brief,
    plan: result.plan,
    selected_variant: selectedVariant,
    variants: result.variants,
    generated_images: generatedImages,
    generated_videos: generatedVideos,
    note: "Netlify demo fallback. Local backend exports a ZIP; AWS can write the same package to S3 and return a presigned URL."
  };
  const text = JSON.stringify(packageBody, null, 2);
  const blob = new Blob([text], { type: "application/json" });
  const downloadUrl = URL.createObjectURL(blob);
  return {
    export_id: filename.replace(/\.json$/, ""),
    filename,
    download_url: downloadUrl,
    storage_target: "Browser download",
    aws_ready_target: `s3://retail-creative-exports/${filename}`,
    file_size_bytes: blob.size,
    cost_guardrail: "Export used existing demo data only. No AI call was made."
  };
}

function demoGenerateVideo(
  brief: CampaignBrief,
  variant: CreativeVariant,
  promptNote?: string,
  referenceImageUrl?: string | null,
  referenceImageRole = "reference_image"
): GeneratedVideoResult {
  return {
    video_url: "/static/generated/videos/demo-seedance-fashion.mp4",
    provider: "Cached demo video",
    model: "local-demo-mp4",
    status: "demo_ready",
    task_id: null,
    live_provider_used: false,
    fallback_reason: "Netlify demo uses a cached vertical video. Local backend can call Seedance via BytePlus Ark or AWS Nova Reel when configured.",
    duration_seconds: 4,
    ratio: "9:16",
    resolution: "480p",
    prompt: `Vertical fashion ad for ${variant.channel}. Campaign: ${brief.creative_instruction}. ${promptNote ?? ""}`,
    reference_image_url: referenceImageUrl ?? null,
    reference_image_role: referenceImageRole,
    model_presentation: brief.model_presentation,
    aws_ready_target: "s3://retail-creative-videos/demo-seedance-fashion.mp4",
    cost_guardrail: "No live video cost was used in the static demo."
  };
}

async function demoRequest<T>(path: string, init?: RequestInit): Promise<T> {
  if (path === "/api/bootstrap") return demoBootstrap() as T;
  if (path === "/api/generate") {
    const brief = init?.body ? (JSON.parse(String(init.body)) as CampaignBrief) : defaultBrief;
    return demoGenerate(brief) as T;
  }
  if (path === "/api/refresh-insight") return demoRecommendation() as T;
  if (path === "/api/refine-brief") {
    const body = init?.body ? (JSON.parse(String(init.body)) as { note: string; brief: CampaignBrief }) : { note: "", brief: defaultBrief };
    return demoRefineBrief(body.note, body.brief) as T;
  }
  if (path === "/api/generate-image") {
    return {
      image_url: "/static/ads/tiktok-dress.png",
      provider: "GPT Image 2",
      model: "gpt-image-2",
      size: "1024x1536",
      quality: "demo",
      prompt: "Static Netlify demo image. Run locally with the Python backend for live generation.",
      prompt_note: "",
      generation_mode: "catalog_reference_edit",
      source_image_url: "/static/products/batik-maxi.png",
      model_presentation: "female_model",
      cost_guardrail: "Netlify demo fallback. Local backend generates one image per selected platform."
    } as T;
  }
  if (path === "/api/generate-video") {
    const body = init?.body
      ? (JSON.parse(String(init.body)) as {
          brief: CampaignBrief;
          variant: CreativeVariant;
          prompt_note?: string;
          reference_image_url?: string | null;
          reference_image_role?: string;
        })
      : { brief: defaultBrief, variant: demoGenerate(defaultBrief).variants[0] };
    return demoGenerateVideo(body.brief, body.variant, body.prompt_note, body.reference_image_url, body.reference_image_role) as T;
  }
  if (path === "/api/export-campaign") {
    const body = init?.body
      ? (JSON.parse(String(init.body)) as {
          brief: CampaignBrief;
          result: AgentResult;
          selected_variant_id: string | null;
          generated_images: Record<string, GeneratedImageResult>;
          generated_videos: Record<string, GeneratedVideoResult>;
        })
      : {
          brief: defaultBrief,
          result: demoGenerate(defaultBrief),
          selected_variant_id: null,
          generated_images: {},
          generated_videos: {}
        };
    return demoExportCampaign(body.brief, body.result, body.selected_variant_id, body.generated_images, body.generated_videos) as T;
  }
  throw new Error(`Demo endpoint not found: ${path}`);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (USE_DEMO_API) return demoRequest<T>(path, init);
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function imageUrl(path: string) {
  if (path.startsWith("http") || path.startsWith("blob:") || path.startsWith("data:")) return path;
  if (USE_DEMO_API) return path;
  return `${API_BASE}${path}`;
}

export const api = {
  bootstrap: () => request<BootstrapPayload>("/api/bootstrap"),
  generate: (brief: CampaignBrief) =>
    request<AgentResult>("/api/generate", {
      method: "POST",
      body: JSON.stringify(brief)
    }),
  generateImage: (brief: CampaignBrief, variant: CreativeVariant, promptNote?: string) =>
    request<GeneratedImageResult>("/api/generate-image", {
      method: "POST",
      body: JSON.stringify({ brief, variant, prompt_note: promptNote })
    }),
  generateVideo: (brief: CampaignBrief, variant: CreativeVariant, promptNote?: string, referenceImageUrl?: string | null, referenceImageRole?: string) =>
    request<GeneratedVideoResult>("/api/generate-video", {
      method: "POST",
      body: JSON.stringify({
        brief,
        variant,
        prompt_note: promptNote,
        reference_image_url: referenceImageUrl,
        reference_image_role: referenceImageRole ?? "reference_image"
      })
    }),
  refreshInsight: (brief: CampaignBrief) =>
    request<TodayRecommendationResult>("/api/refresh-insight", {
      method: "POST",
      body: JSON.stringify({ brief })
    }),
  refineBrief: (brief: CampaignBrief, note: string) =>
    request<BriefRefineResult>("/api/refine-brief", {
      method: "POST",
      body: JSON.stringify({ brief, note })
    }),
  exportCampaign: (
    brief: CampaignBrief,
    result: AgentResult,
    selectedVariantId: string | null,
    generatedImages: Record<string, GeneratedImageResult>,
    generatedVideos: Record<string, GeneratedVideoResult>
  ) =>
    request<ExportCampaignResult>("/api/export-campaign", {
      method: "POST",
      body: JSON.stringify({
        brief,
        result,
        selected_variant_id: selectedVariantId,
        generated_images: generatedImages,
        generated_videos: generatedVideos
      })
    })
};

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 48) || "campaign-export";
}

function modelPresentationLabel(value: ModelPresentation) {
  if (value === "male_model") return "male model";
  if (value === "product_only") return "product-only";
  return "female model";
}
