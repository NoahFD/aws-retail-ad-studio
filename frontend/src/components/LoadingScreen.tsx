import { Sparkles } from "lucide-react";

export function LoadingScreen({ label, error }: { label: string; error: string | null }) {
  return (
    <div className="loading-screen">
      <div className="loading-card">
        <Sparkles size={26} />
        <h1>Retail Creative Console</h1>
        <p>{error ?? label}</p>
      </div>
    </div>
  );
}
