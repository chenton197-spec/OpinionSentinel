import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { ArticleTable } from "@/components/article-table";
import { Panel } from "@/components/panel";
import { getArticles, getCompanyProfile } from "@/lib/api";

type SearchParamValue = string | string[] | undefined;

function firstValue(value: SearchParamValue): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function ArticlesPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, SearchParamValue>>;
}) {
  const params = await searchParams;
  const keyword = firstValue(params.keyword);
  const sourceTypeParam = firstValue(params.source_type);
  const sourceType = sourceTypeParam === undefined ? "news_portal" : sourceTypeParam;
  const sentiment = firstValue(params.sentiment);
  const onlyRuleHits = firstValue(params.only_rule_hits) === "true";
  const companyScope = firstValue(params.company_scope) === "true";
  const companyProfile = await getCompanyProfile();
  const articleList = await getArticles({
    keyword,
    source_type: sourceType || undefined,
    sentiment,
    only_rule_hits: onlyRuleHits,
    company_scope: companyScope,
  });

  return (
    <AppShell title="舆情列表" description={`默认优先显示新闻门户结果，避免商品/商城页干扰判断。当前监控公司“${companyProfile.company_name}”的公司范围可按需再勾选。`}>
      <Panel title="筛选条件" eyebrow="Filters">
        <form className="grid gap-4 md:grid-cols-4" method="get">
          <input
            name="keyword"
            defaultValue={keyword}
            placeholder="关键词，例如 物流"
            className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none placeholder:text-[var(--muted)]"
          />
          <select
            name="source_type"
            defaultValue={sourceTypeParam ?? "news_portal"}
            className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none"
          >
            <option value="">全部来源</option>
            <option value="company_announcement">企业官网/公告</option>
            <option value="news_portal">新闻门户</option>
            <option value="search_aggregator">搜索聚合</option>
          </select>
          <select
            name="sentiment"
            defaultValue={sentiment ?? ""}
            className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none"
          >
            <option value="">全部情感</option>
            <option value="positive">positive</option>
            <option value="neutral">neutral</option>
            <option value="negative">negative</option>
          </select>
          <label className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-[var(--muted)]">
            <input type="checkbox" name="only_rule_hits" value="true" defaultChecked={onlyRuleHits} className="accent-[var(--accent)]" />
            仅看规则命中
          </label>
          <label className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-[var(--muted)]">
            <input type="checkbox" name="company_scope" value="true" defaultChecked={companyScope} className="accent-[var(--accent)]" />
            仅看当前监控公司
          </label>
          <div className="md:col-span-4 flex gap-3">
            <button className="rounded-full bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[var(--accent-contrast)]" type="submit">
              应用筛选
            </button>
            <Link href="/articles" className="rounded-full border border-white/10 px-4 py-2 text-sm text-white hover:bg-white/8">
              重置
            </Link>
          </div>
        </form>
        <div className="mt-4 rounded-2xl border border-dashed border-white/10 bg-black/10 px-4 py-3 text-sm text-[var(--muted)]">
          当前公司关键词：{companyProfile.keywords.join("、")}
        </div>
      </Panel>

      <Panel title={`结果列表 · 共 ${articleList.total} 条`} eyebrow="Results">
        <ArticleTable items={articleList.items} />
      </Panel>
    </AppShell>
  );
}
