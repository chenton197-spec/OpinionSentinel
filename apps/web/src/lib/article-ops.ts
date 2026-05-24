import type { Article, KeywordRule, SentimentLabel } from "@/types";

const TWO_HOURS_MS = 2 * 60 * 60 * 1000;
const TWELVE_HOURS_MS = 12 * 60 * 60 * 1000;

export type ArticleOpsSignals = {
  duplicateCandidates: Article[];
  heatingUp: boolean;
  negativeRuleMatched: boolean;
  officialResponseArticle: Article | null;
  recentSignalCount: number;
  shouldDeduplicateFirst: boolean;
  shouldHighlightInDaily: boolean;
  shouldSuggestOfficialResponse: boolean;
  shouldTriggerFeishuAlert: boolean;
};

function headlineKey(title: string): string {
  return title
    .split(" - ")[0]
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function articleTerms(article: Article): string[] {
  const terms = [
    ...article.keyword_hits.map((hit) => hit.keyword),
    ...article.tags,
    headlineKey(article.title),
  ];

  return [...new Set(terms.map((term) => term.trim().toLowerCase()).filter(Boolean))];
}

function sharedTerms(left: Article, right: Article): string[] {
  const rightTerms = new Set(articleTerms(right));
  return articleTerms(left).filter((term) => rightTerms.has(term));
}

function hasStrongSimilarity(left: Article, right: Article): boolean {
  const leftHeadline = headlineKey(left.title);
  const rightHeadline = headlineKey(right.title);
  const shared = sharedTerms(left, right);

  if (leftHeadline && rightHeadline && (leftHeadline === rightHeadline || leftHeadline.includes(rightHeadline) || rightHeadline.includes(leftHeadline))) {
    return true;
  }

  return shared.length >= 2;
}

function withinWindow(left: string, right: string, windowMs: number): boolean {
  return Math.abs(new Date(left).getTime() - new Date(right).getTime()) <= windowMs;
}

function isLLMNegative(article: Article): boolean {
  return article.sentiment.label === ("negative" as SentimentLabel) && article.sentiment.confidence >= 0.7;
}

export function buildArticleOpsSignals(article: Article, articles: Article[], rules: KeywordRule[]): ArticleOpsSignals {
  const negativeRuleIds = new Set(
    rules
      .filter((rule) => rule.sentiment_threshold === "negative")
      .map((rule) => rule.id),
  );
  const negativeRuleMatched = article.rule_hit_ids.some((ruleId) => negativeRuleIds.has(ruleId));

  const recentSimilarArticles = articles.filter((candidate) => (
    candidate.id !== article.id
    && withinWindow(article.published_at, candidate.published_at, TWO_HOURS_MS)
    && hasStrongSimilarity(article, candidate)
  ));

  const officialResponseArticle = articles
    .filter((candidate) => (
      candidate.id !== article.id
      && candidate.source_type === "company_announcement"
      && sharedTerms(article, candidate).length >= 1
    ))
    .sort((left, right) => new Date(right.published_at).getTime() - new Date(left.published_at).getTime())[0] ?? null;

  const duplicateCandidates = article.source_type === "search_aggregator"
    ? articles.filter((candidate) => (
      candidate.id !== article.id
      && withinWindow(article.published_at, candidate.published_at, TWELVE_HOURS_MS)
      && hasStrongSimilarity(article, candidate)
    ))
    : [];

  const shouldSuggestOfficialResponse = article.source_type === "news_portal" && article.risk_score > 70;
  const heatingUp = negativeRuleMatched && isLLMNegative(article) && recentSimilarArticles.length >= 2;
  const shouldTriggerFeishuAlert = heatingUp;
  const shouldHighlightInDaily = heatingUp;
  const shouldDeduplicateFirst = article.source_type === "search_aggregator" && duplicateCandidates.length > 0;

  return {
    duplicateCandidates,
    heatingUp,
    negativeRuleMatched,
    officialResponseArticle,
    recentSignalCount: recentSimilarArticles.length,
    shouldDeduplicateFirst,
    shouldHighlightInDaily,
    shouldSuggestOfficialResponse,
    shouldTriggerFeishuAlert,
  };
}