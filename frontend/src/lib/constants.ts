import type { Channel, TodayRecommendationResult } from "./api";

export const channels: Channel[] = ["Meta", "TikTok", "Display", "Email"];

export const markets = ["Singapore", "Malaysia", "Indonesia", "Thailand"];

export const promptSuggestions = ["Show product texture", "Premium city backdrop", "Stronger offer", "Less posed"];

export const navItems = [
  { label: "Creative Console", active: true },
  { label: "Campaigns" },
  { label: "Performance" },
  { label: "Audiences" },
  { label: "Products" }
];

export const defaultTodayRecommendation: TodayRecommendationResult = {
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
    model_presentation: "female_model",
    creative_instruction: "TikTok-first Malaysia launch for Style Enthusiasts. Make it premium, less posed, show product texture and upbeat city energy."
  },
  reasoning: [
    "Short video is a strong recent format in the campaign history.",
    "Style Enthusiasts prefer TikTok and Meta with trend-led creative.",
    "Selected products have strong visual assets and inventory readiness."
  ],
  live_ai_used: false,
  errors: [],
  cost_guardrail: "Default data-backed recommendation. Refreshing uses one small OpenAI call locally."
};
