"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { href: "/dashboard", label: "总览看板" },
  { href: "/articles", label: "舆情列表" },
  { href: "/rules", label: "关键词规则" },
  { href: "/alerts", label: "预警记录" },
  { href: "/reports", label: "日报周报" },
  { href: "/settings", label: "系统设置" },
];

export function SideNav() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-6 flex h-fit flex-col gap-6 rounded-[28px] border border-white/10 bg-[var(--surface-strong)] p-5 shadow-[0_24px_80px_rgba(15,23,42,0.38)] backdrop-blur">
      <div className="space-y-1">
        <p className="text-xs uppercase tracking-[0.3em] text-[var(--muted)]">Brand Ops</p>
        <h1 className="text-xl font-semibold text-white">公司舆情监控台</h1>
        <p className="text-sm leading-6 text-[var(--muted)]">MVP 演示版，覆盖看板、规则、预警和报表闭环。</p>
      </div>
      <nav className="flex flex-col gap-2">
        {navigation.map((item) => {
          const active = pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-2xl px-4 py-3 text-sm transition ${
                active
                  ? "bg-[var(--accent)] text-[var(--accent-contrast)] shadow-[0_10px_30px_rgba(255,122,89,0.28)]"
                  : "text-[var(--muted)] hover:bg-white/6 hover:text-white"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-[var(--muted)]">
        <p className="font-medium text-white">监控建议</p>
        <p className="mt-2 leading-6">优先盯住负面情感、物流与客服类关键词，并给搜索聚合结果单独做去重观察。</p>
      </div>
    </aside>
  );
}
