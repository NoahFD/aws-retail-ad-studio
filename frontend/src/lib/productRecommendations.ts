import type { Product, Segment } from "@/lib/api";

export const RECOMMENDED_PRODUCT_FILTER = "recommended";
export const ALL_PRODUCT_FILTER = "all";

export type ProductFilter = typeof RECOMMENDED_PRODUCT_FILTER | typeof ALL_PRODUCT_FILTER | `category:${string}`;

export type ProductRecommendation = {
  product: Product;
  score: number;
  fitLabel: string;
  reasons: string[];
  recommended: boolean;
};

type SegmentRule = {
  categoryLabel: string;
  preferredTags: string[];
  categoryBoosts: Record<string, number>;
  valueMaxPrice?: number;
};

const segmentRules: Record<string, SegmentRule> = {
  seg_value_seekers: {
    categoryLabel: "Value-ready essentials",
    preferredTags: ["best-seller", "breathable", "linen", "workwear", "tailored", "capsule"],
    categoryBoosts: { Shirts: 14, Bottoms: 12, Menswear: 8, Tops: 8 },
    valueMaxPrice: 90
  },
  seg_style_enthusiasts: {
    categoryLabel: "Trend-led social pieces",
    preferredTags: ["social", "occasion", "batik-inspired", "movement", "weekend", "premium"],
    categoryBoosts: { Dresses: 14, Skirts: 10, Menswear: 8 }
  },
  seg_urban_professionals: {
    categoryLabel: "Office-to-evening essentials",
    preferredTags: ["workwear", "tailored", "capsule", "linen", "breathable", "premium"],
    categoryBoosts: { Shirts: 12, Bottoms: 12, Skirts: 8, Tops: 8 },
    valueMaxPrice: 110
  },
  seg_modest_fashion: {
    categoryLabel: "Breathable modest occasionwear",
    preferredTags: ["modest", "breathable", "layering", "occasion", "midi", "movement"],
    categoryBoosts: { Tops: 14, Dresses: 10, Skirts: 10 },
    valueMaxPrice: 130
  }
};

const defaultRule: SegmentRule = {
  categoryLabel: "High-readiness catalog picks",
  preferredTags: ["best-seller", "breathable", "premium", "capsule"],
  categoryBoosts: {},
  valueMaxPrice: 120
};

export function productRecommendationsForSegment(products: Product[], segment?: Segment): ProductRecommendation[] {
  const rule = segment ? segmentRules[segment.id] ?? defaultRule : defaultRule;
  const scored = products
    .map((product) => {
      const matchingTags = product.tags.filter((tag) => rule.preferredTags.includes(tag));
      const priceBoost = rule.valueMaxPrice && product.price_sgd <= rule.valueMaxPrice ? 12 : 0;
      const categoryBoost = rule.categoryBoosts[product.category] ?? 0;
      const inventoryBoost = product.inventory_score / 5;
      const marginBoost = product.margin * 18;
      const preferenceBoost = segment?.copy_preferences.includes("value-led") && product.price_sgd <= 90 ? 8 : 0;
      const score = Math.round(36 + inventoryBoost + marginBoost + categoryBoost + priceBoost + matchingTags.length * 6 + preferenceBoost);
      return {
        product,
        score,
        fitLabel: fitLabel(score),
        reasons: recommendationReasons(product, matchingTags, priceBoost > 0, categoryBoost > 0),
        recommended: false
      };
    })
    .sort((a, b) => b.score - a.score);

  return scored.map((item, index) => ({ ...item, recommended: index < Math.min(4, scored.length) }));
}

export function productFilterOptions(recommendations: ProductRecommendation[]) {
  const categories = Array.from(new Set(recommendations.map((item) => item.product.category)));
  return [
    { value: RECOMMENDED_PRODUCT_FILTER as ProductFilter, label: "Recommended" },
    { value: ALL_PRODUCT_FILTER as ProductFilter, label: "All products" },
    ...categories.map((category) => ({ value: `category:${category}` as ProductFilter, label: category }))
  ];
}

export function filterProductRecommendations(recommendations: ProductRecommendation[], filter: ProductFilter) {
  if (filter === ALL_PRODUCT_FILTER) return recommendations;
  if (filter === RECOMMENDED_PRODUCT_FILTER) return recommendations.filter((item) => item.recommended);
  const category = filter.replace("category:", "");
  return recommendations.filter((item) => item.product.category === category);
}

export function suggestedProductIds(recommendations: ProductRecommendation[], count = 4) {
  return recommendations.slice(0, count).map((item) => item.product.id);
}

export function suggestedCategoryLabel(segment?: Segment) {
  if (!segment) return defaultRule.categoryLabel;
  return (segmentRules[segment.id] ?? defaultRule).categoryLabel;
}

export function productInsightCopy(recommendations: ProductRecommendation[], segment?: Segment) {
  const top = recommendations.slice(0, 3).map((item) => item.product.name);
  if (!top.length) return "No catalog products are available for this segment yet.";
  const segmentName = segment?.name ?? "this segment";
  return `${segmentName}: ${top.join(", ")} score highest from price, inventory, margin, and product tags.`;
}

function fitLabel(score: number) {
  if (score >= 88) return "High fit";
  if (score >= 78) return "Good fit";
  return "Test fit";
}

function recommendationReasons(product: Product, matchingTags: string[], priceFit: boolean, categoryFit: boolean) {
  const reasons = [];
  if (categoryFit) reasons.push(`${product.category} fits segment intent`);
  if (matchingTags.length) reasons.push(matchingTags.slice(0, 2).join(" + "));
  if (priceFit) reasons.push(`SGD ${product.price_sgd} price point`);
  reasons.push(`${product.inventory_score}/100 inventory`);
  return reasons.slice(0, 3);
}
