import { ArrowRight, Check, Loader2, RefreshCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { StrategyCard, TodayRecommendationResult } from "@/lib/api";

type TodayRecommendationProps = {
  campaignCount: number;
  error: string | null;
  recommendation: TodayRecommendationResult;
  refreshLabel: string;
  refreshNote: string;
  refreshing: boolean;
  applying: boolean;
  directionApplied: boolean;
  strategy?: StrategyCard;
  onRefresh: () => void;
  onUseSuggestion: () => void;
};

export function TodayRecommendation({
  campaignCount,
  error,
  recommendation,
  refreshLabel,
  refreshNote,
  refreshing,
  applying,
  directionApplied,
  strategy,
  onRefresh,
  onUseSuggestion
}: TodayRecommendationProps) {
  const confidence = recommendation.confidence || strategy?.confidence || 92;

  return (
    <section className={refreshing ? "panel today-panel is-updating" : "panel today-panel"} aria-busy={refreshing} aria-label="Today recommendation">
      {refreshing ? (
        <div className="data-update-overlay" role="status" aria-live="polite">
          <div className="data-update-card">
            <Loader2 className="spin" data-icon="inline-start" />
            <strong>Refreshing recommendation</strong>
            <span>Checking the latest campaign, product, and audience signals.</span>
          </div>
        </div>
      ) : null}

      <div className="today-copy">
        <h2 className="story-step-title">1 · Current opportunity</h2>
        <strong className="today-headline">{recommendation.title}</strong>
        <p>{recommendation.summary}</p>
        {recommendation.live_ai_used ? <em>Refreshed with live AI</em> : <em>Ready from connected data</em>}
      </div>

      <div className="today-proof" aria-label="Recommendation rationale">
        {recommendation.signals.slice(0, 3).map((signal) => (
          <article key={`${signal.label}-${signal.value}`}>
            <strong>{signal.label}</strong>
            <span>{signal.value}</span>
          </article>
        ))}
      </div>

      <div className="today-action">
        <div>
          <strong>{confidence}% confidence</strong>
          <span>
            Based on {campaignCount} campaigns · refreshed {refreshLabel}
          </span>
          {refreshNote ? <small className="refresh-note">{refreshNote}</small> : null}
          {error ? <small className="refresh-error">{error}</small> : null}
        </div>
        <div className="today-buttons">
          <Button className="secondary-today-action" onClick={onRefresh} disabled={refreshing} type="button">
            {refreshing ? <Loader2 className="spin" data-icon="inline-start" /> : <RefreshCcw data-icon="inline-start" />}
            Refresh from data
          </Button>
          <Button onClick={onUseSuggestion} disabled={applying || refreshing || directionApplied} type="button">
            {applying ? <Loader2 className="spin" data-icon="inline-start" /> : directionApplied ? <Check data-icon="inline-start" /> : null}
            {directionApplied ? "Direction applied" : "Use this direction"}
            {directionApplied ? null : <ArrowRight data-icon="inline-end" />}
          </Button>
        </div>
      </div>
    </section>
  );
}
