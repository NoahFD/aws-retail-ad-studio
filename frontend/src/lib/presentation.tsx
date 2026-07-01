import { Mail, Megaphone, PackageSearch, Play } from "lucide-react";

import type { Channel, CreativeVariant, Product } from "./api";

export function pct(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

export function lift(value: number) {
  return `+${(value * 100).toFixed(0)}%`;
}

export function channelIcon(channel: Channel) {
  if (channel === "Meta") return <Megaphone size={15} />;
  if (channel === "TikTok") return <Play size={15} />;
  if (channel === "Display") return <PackageSearch size={15} />;
  return <Mail size={15} />;
}

export function variantTitle(variant: CreativeVariant, product?: Product) {
  if (variant.channel === "TikTok") return `${product?.name ?? "Product"} short video`;
  if (variant.channel === "Meta") return `${product?.name ?? "Product"} carousel`;
  if (variant.channel === "Display") return `${product?.name ?? "Product"} display banner`;
  return `${product?.name ?? "Product"} email hero`;
}
