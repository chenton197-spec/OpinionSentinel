import type { SentimentLabel } from "@/types";

const toneMap: Record<SentimentLabel, string> = {
  positive: "bg-emerald-400/15 text-emerald-200 border-emerald-300/20",
  neutral: "bg-slate-200/10 text-slate-100 border-slate-200/10",
  negative: "bg-rose-400/15 text-rose-200 border-rose-300/20",
  pending: "bg-amber-400/15 text-amber-200 border-amber-300/20",
  failed: "bg-fuchsia-400/15 text-fuchsia-200 border-fuchsia-300/20",
};

export function SentimentPill({ value }: { value: SentimentLabel }) {
  return <span className={`inline-flex rounded-full border px-3 py-1 text-xs ${toneMap[value]}`}>{value}</span>;
}
