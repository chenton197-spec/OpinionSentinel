import type { ReactNode } from "react";

import { SideNav } from "@/components/side-nav";

export function AppShell({ title, description, actions, children }: { title: string; description: string; actions?: ReactNode; children: ReactNode; }) {
  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[280px_1fr] lg:px-6">
        <SideNav />
        <main className="space-y-6">
          <header className="overflow-hidden rounded-[32px] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(255,122,89,0.28),_transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.05),rgba(255,255,255,0.02))] p-8 shadow-[0_20px_80px_rgba(15,23,42,0.24)] backdrop-blur">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-3xl space-y-3">
                <p className="text-xs uppercase tracking-[0.3em] text-[var(--muted)]">内部运营后台</p>
                <h2 className="text-3xl font-semibold tracking-tight text-white lg:text-4xl">{title}</h2>
                <p className="max-w-2xl text-sm leading-7 text-[var(--muted)] lg:text-base">{description}</p>
              </div>
              {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
            </div>
          </header>
          {children}
        </main>
      </div>
    </div>
  );
}
