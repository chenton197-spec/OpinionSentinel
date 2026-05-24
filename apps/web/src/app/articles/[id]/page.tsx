import Link from "next/link";
import { notFound } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { Panel } from "@/components/panel";
import { SentimentPill } from "@/components/sentiment-pill";
import { getArticle, getArticles, getRules } from "@/lib/api";
import { buildArticleOpsSignals } from "@/lib/article-ops";

export default async function ArticleDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const article = await getArticle(id);

  if (!article) {
    notFound();
  }

  const articleList = await getArticles();
  const rules = await getRules();
  const related = articleList.items.filter((item) => item.id !== article.id).slice(0, 3);
  const signals = buildArticleOpsSignals(article, articleList.items, rules);
  const recommendations = [
    signals.shouldSuggestOfficialResponse
      ? signals.officialResponseArticle
        ? {
            key: "official-response-link",
            content: (
              <>
                当前为新闻门户高风险稿件，建议补充官方回应链接：
                <Link href={`/articles/${signals.officialResponseArticle.id}`} className="text-[var(--accent-soft)] hover:text-white">
                  {signals.officialResponseArticle.title}
                </Link>
              </>
            ),
          }
        : {
            key: "official-response-missing",
            content: "当前为新闻门户高风险稿件，建议补充官方回应链接；暂未找到现成官网回应，建议补录公告或声明地址。",
          }
      : null,
    signals.shouldTriggerFeishuAlert
      ? {
          key: "heating-up-alert",
          content: `该稿件命中负面规则，且近 2 小时内有 ${signals.recentSignalCount} 条相似舆情持续升温，建议触发飞书告警并在日报中加粗展示。`,
        }
      : null,
    signals.shouldDeduplicateFirst
      ? {
          key: "dedup-first",
          content: `该稿件来自搜索聚合，检测到 ${signals.duplicateCandidates.length} 条潜在重复项，建议先做去重判断，再决定是否升级。`,
        }
      : null,
  ].filter((item): item is any => Boolean(item));

  return (
    <AppShell title="舆情详情" description="展示标准化后的文章主体、情感结果、来源元数据与规则命中信息，方便品牌团队快速判断是否需要升级处理。">
      <section className="grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
        <Panel title={article.title} eyebrow={article.source_name}>
          <div className="flex flex-wrap items-center gap-3 text-sm text-[var(--muted)]">
            <SentimentPill value={article.sentiment.label} />
            <span>作者：{article.author}</span>
            <span>发布时间：{new Date(article.published_at).toLocaleString("zh-CN")}</span>
            <span>风险分：{article.risk_score}</span>
          </div>
          <p className="mt-6 text-base leading-8 text-white/88">{article.content}</p>

          <div className="mt-6 flex flex-wrap gap-2">
            {article.tags.map((tag) => (
              <span key={tag} className="rounded-full border border-white/10 px-3 py-1 text-xs text-[var(--muted)]">
                {tag}
              </span>
            ))}
          </div>

          <div className="mt-8 rounded-[22px] border border-white/10 bg-black/15 p-4 text-sm leading-7 text-[var(--muted)]">
            <p className="font-medium text-white">原文与命中信息</p>
            <div className="mt-2 flex flex-col gap-1">
              <span>依据来源（原文地址）：</span>
              {article.original_url.split(',').map((url, idx) => (
                <a key={idx} href={url.trim()} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 underline break-all inline-block">
                  {url.trim()}
                </a>
              ))}
            </div>
            <p>命中关键词：{article.keyword_hits.map((hit) => hit.keyword).join("、")}</p>
            <p>命中规则：{article.rule_hit_ids.length ? article.rule_hit_ids.join("、") : "未命中"}</p>
            <p>情感说明：{article.sentiment.reason}</p>
          </div>
        </Panel>

        <div className="space-y-6">
          <Panel title="相关推荐" eyebrow="Related">
            <div className="space-y-4">
              {related.map((item) => (
                <Link key={item.id} href={`/articles/${item.id}`} className="block rounded-[22px] border border-white/10 bg-black/10 p-4 hover:bg-white/6">
                  <p className="font-medium text-white">{item.title}</p>
                  <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{item.summary}</p>
                </Link>
              ))}
            </div>
          </Panel>

          <Panel title="处理建议" eyebrow="Ops">
            <ul className="space-y-3 text-sm leading-7 text-[var(--muted)]">
              {recommendations.length ? recommendations.map((item) => <li key={item.key}>{item.content}</li>) : <li>当前未触发额外升级动作，建议继续观察情感走势、规则命中和是否出现官网回应。</li>}
            </ul>
          </Panel>
        </div>
      </section>
    </AppShell>
  );
}
