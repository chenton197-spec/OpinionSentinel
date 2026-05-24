import Link from "next/link";

import { SentimentPill } from "@/components/sentiment-pill";
import type { Article } from "@/types";

export function ArticleTable({ items }: { items: Article[] }) {
  return (
    <div className="overflow-hidden rounded-[24px] border border-white/10">
      <table className="min-w-full divide-y divide-white/10 text-sm">
        <thead className="bg-white/5 text-left text-[var(--muted)]">
          <tr>
            <th className="px-4 py-3 font-medium">标题</th>
            <th className="px-4 py-3 font-medium">来源</th>
            <th className="px-4 py-3 font-medium">情感</th>
            <th className="px-4 py-3 font-medium">风险分</th>
            <th className="px-4 py-3 font-medium">规则命中</th>
            <th className="px-4 py-3 font-medium">发布时间</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5 bg-black/10">
          {items.map((article) => (
            <tr key={article.id} className="transition hover:bg-white/5">
              <td className="px-4 py-4 align-top">
                <Link href={`/articles/${article.id}`} className="font-medium text-white hover:text-[var(--accent-soft)]">
                  {article.title}
                </Link>
                <p className="mt-2 max-w-xl text-xs leading-6 text-[var(--muted)]">{article.summary}</p>
              </td>
              <td className="px-4 py-4 text-[var(--muted)]">{article.source_name}</td>
              <td className="px-4 py-4"><SentimentPill value={article.sentiment.label} /></td>
              <td className="px-4 py-4 text-white">{article.risk_score}</td>
              <td className="px-4 py-4 text-[var(--muted)]">{article.rule_hit_ids.length ? `${article.rule_hit_ids.length} 条` : "未命中"}</td>
              <td className="px-4 py-4 text-[var(--muted)]">{new Date(article.published_at).toLocaleString("zh-CN")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
