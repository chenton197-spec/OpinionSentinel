import type { DistributionItem } from "@/types";

export function DistributionList({ items, highlight = false }: { items: DistributionItem[]; highlight?: boolean; }) {
  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.label} className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[var(--muted)]">{item.label}</span>
            <span className="text-white">{item.value}</span>
          </div>
          <div className="h-2 rounded-full bg-white/6">
            <div
              className={`h-2 rounded-full ${highlight ? "bg-[var(--accent)]" : "bg-white/60"}`}
              style={{ width: `${Math.max((item.value / max) * 100, 10)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
