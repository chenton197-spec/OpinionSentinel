import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { Panel } from "@/components/panel";
import { getAlerts, getArticles, getRules } from "@/lib/api";
import { buildArticleOpsSignals } from "@/lib/article-ops";

export default async function AlertsPage() {
  const alerts = await getAlerts();
  const articles = await getArticles();
  const rules = await getRules();
  const articleMap = new Map(articles.items.map((article) => [article.id, article]));

  return (
    <AppShell title="预警记录" description="首期只实现关键词命中与负面情感命中两类预警，并记录通知状态与回执，方便后台复盘。">
      <Panel title={`最近预警 · ${alerts.length} 条`} eyebrow="Alerts">
        <div className="space-y-4">
          {alerts.map((alert) => {
            const article = articleMap.get(alert.article_id);
            const signals = article ? buildArticleOpsSignals(article, articles.items, rules) : null;

            return (
              <div key={alert.id} className={`rounded-[24px] border bg-black/10 p-5 ${signals?.shouldTriggerFeishuAlert ? "border-rose-300/40" : "border-white/10"}`}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm text-[var(--muted)]">{alert.rule_name}</p>
                    <Link href={`/articles/${alert.article_id}`} className="mt-1 block text-base font-semibold text-white hover:text-[var(--accent-soft)]">
                      {alert.article_title}
                    </Link>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {signals?.shouldTriggerFeishuAlert ? <span className="rounded-full bg-rose-400/15 px-3 py-1 text-xs text-rose-200">建议立即飞书告警</span> : null}
                    {signals?.shouldDeduplicateFirst ? <span className="rounded-full bg-amber-400/15 px-3 py-1 text-xs text-amber-200">先去重</span> : null}
                    {signals?.shouldSuggestOfficialResponse ? <span className="rounded-full bg-sky-400/15 px-3 py-1 text-xs text-sky-200">补官方回应</span> : null}
                    <span className={`rounded-full px-3 py-1 text-xs ${alert.notification_status === "sent" ? "bg-emerald-400/15 text-emerald-200" : "bg-amber-400/15 text-amber-200"}`}>
                      {alert.notification_status}
                    </span>
                  </div>
                </div>
                <p className="mt-3 text-sm leading-6 text-[var(--muted)]">触发原因：{alert.trigger_reason}</p>
                {signals?.shouldTriggerFeishuAlert ? <p className="mt-2 text-sm leading-6 text-rose-200">升级建议：近 2 小时相似负面舆情持续升温，建议飞书即时通知，并同步纳入日报重点条目。</p> : null}
                {signals?.shouldDeduplicateFirst ? <p className="mt-2 text-sm leading-6 text-amber-100">去重建议：该条来自搜索聚合，存在 {signals.duplicateCandidates.length} 条潜在重复项，建议先合并再升级。</p> : null}
                <p className="mt-2 text-sm text-[var(--muted)]">通知回执：{alert.notification_receipt}</p>
              </div>
            );
          })}
        </div>
      </Panel>
    </AppShell>
  );
}
