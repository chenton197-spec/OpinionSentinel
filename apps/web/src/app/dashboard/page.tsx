import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { DistributionList } from "@/components/distribution-list";
import { Panel } from "@/components/panel";
import { SentimentPill } from "@/components/sentiment-pill";
import { StatCard } from "@/components/stat-card";
import { getCompanyProfile, getDashboard } from "@/lib/api";

export default async function DashboardPage() {
  const dashboard = await getDashboard();
  const companyProfile = await getCompanyProfile();

  return (
    <AppShell
      title="公司舆情总览看板"
      description={`当前监控主体：${companyProfile.company_name}。围绕品牌声量、负面风险、重点来源和规则命中构建首期闭环。关键词示例：${companyProfile.keywords.slice(0, 4).join("、") || "未配置"}。`}
      actions={
        <>
          <Link href="/reports" className="rounded-full border border-white/10 px-4 py-2 text-sm text-white hover:bg-white/8">
            查看报表
          </Link>
          <Link href="/settings" className="rounded-full border border-white/10 px-4 py-2 text-sm text-white hover:bg-white/8">
            修改公司
          </Link>
          <Link href="/rules" className="rounded-full bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[var(--accent-contrast)]">
            管理规则
          </Link>
        </>
      }
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="总舆情量" value={String(dashboard.total_articles)} hint={`重点来源：${dashboard.top_source}`} />
        <StatCard label="负面占比" value={`${Math.round(dashboard.negative_ratio * 100)}%`} hint="负面项建议触发人工复核" tone="danger" />
        <StatCard label="今日新增" value={String(dashboard.today_new)} hint="当前种子数据与接口结果可回退展示" tone="positive" />
        <StatCard label="启用规则" value={String(dashboard.active_rules)} hint="支持关键词、情感阈值与来源范围" tone="warning" />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <Panel title="趋势观察" eyebrow="Trend">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-4">
              {dashboard.trend.map((point) => (
                <div key={point.date} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[var(--muted)]">{point.date}</span>
                    <span className="text-white">总量 {point.total} / 负面 {point.negative}</span>
                  </div>
                  <div className="grid gap-2">
                    <div className="h-2 rounded-full bg-white/6">
                      <div className="h-2 rounded-full bg-white/80" style={{ width: `${point.total * 24}%` }} />
                    </div>
                    <div className="h-2 rounded-full bg-white/6">
                      <div className="h-2 rounded-full bg-[var(--accent)]" style={{ width: `${Math.max(point.negative * 30, 8)}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="rounded-[24px] border border-white/10 bg-black/20 p-5">
              <p className="text-sm text-[var(--muted)]">值班提示</p>
              <ul className="mt-4 space-y-3 text-sm leading-7 text-white/88">
                <li>负面与物流、客服类关键词同时出现时，优先升级人工确认。</li>
                <li>官网公告可作为负面回应的修复信号，建议在看板里并排观察。</li>
                <li>搜索聚合结果要与新闻门户交叉去重，避免放大量级误判。</li>
              </ul>
            </div>
          </div>
        </Panel>

        <Panel title="重点舆情" eyebrow="Focus">
          <div className="space-y-4">
            {dashboard.highlighted_articles.map((article) => (
              <Link key={article.id} href={`/articles/${article.id}`} className="block rounded-[22px] border border-white/10 bg-black/10 p-4 hover:bg-white/6">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium text-white">{article.title}</p>
                  <SentimentPill value={article.sentiment.label} />
                </div>
                <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{article.summary}</p>
              </Link>
            ))}
          </div>
        </Panel>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <Panel title="来源分布" eyebrow="Sources">
          <DistributionList items={dashboard.source_distribution} />
        </Panel>
        <Panel title="情感分布" eyebrow="Sentiment">
          <DistributionList items={dashboard.sentiment_distribution} highlight />
        </Panel>
        <Panel title="高频关键词" eyebrow="Keywords">
          <DistributionList items={dashboard.top_keywords} highlight />
        </Panel>
      </section>
    </AppShell>
  );
}
