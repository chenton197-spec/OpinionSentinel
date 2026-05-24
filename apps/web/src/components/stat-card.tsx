export function StatCard({ label, value, hint, tone = "neutral" }: { label: string; value: string; hint: string; tone?: "neutral" | "warning" | "danger" | "positive"; }) {
  const toneClass = {
    neutral: "from-white/10 to-white/5",
    warning: "from-amber-300/20 to-orange-300/10",
    danger: "from-rose-400/25 to-red-400/10",
    positive: "from-emerald-300/20 to-lime-300/10",
  }[tone];

  return (
    <div className={`rounded-[24px] border border-white/10 bg-gradient-to-br ${toneClass} p-5`}>
      <p className="text-sm text-[var(--muted)]">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
      <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{hint}</p>
    </div>
  );
}
