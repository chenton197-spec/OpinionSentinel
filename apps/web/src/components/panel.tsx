import type { ReactNode } from "react";

export function Panel({ title, eyebrow, children }: { title: string; eyebrow?: string; children: ReactNode; }) {
  return (
    <section className="rounded-[28px] border border-white/10 bg-[var(--surface)] p-5 shadow-[0_18px_60px_rgba(15,23,42,0.18)] backdrop-blur lg:p-6">
      <div className="mb-4 space-y-1">
        {eyebrow ? <p className="text-xs uppercase tracking-[0.3em] text-[var(--muted)]">{eyebrow}</p> : null}
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>
      {children}
    </section>
  );
}
