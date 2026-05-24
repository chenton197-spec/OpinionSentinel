export type SourceType =
  | "company_announcement"
  | "news_portal"
  | "search_aggregator"
  | "reserved_extension";

export type SentimentLabel =
  | "positive"
  | "neutral"
  | "negative"
  | "pending"
  | "failed";

export type NotificationStatus = "pending" | "sent" | "failed";

export type ReportStatus = "pending" | "running" | "ready" | "failed";

export type ReportOutputFormat = "html" | "pdf";

export interface KeywordHit {
  keyword: string;
  matched_text: string;
}

export interface SentimentResult {
  label: SentimentLabel;
  confidence: number;
  analyzed_at: string;
  reason: string;
}

export interface Article {
  id: string;
  title: string;
  summary: string;
  content: string;
  source_name: string;
  source_type: SourceType;
  source_domain: string;
  original_url: string;
  author: string;
  published_at: string;
  crawled_at: string;
  fingerprint: string;
  sentiment: SentimentResult;
  keyword_hits: KeywordHit[];
  tags: string[];
  region: string;
  industry: string;
  rule_hit_ids: string[];
  risk_score: number;
}

export interface ArticleListResponse {
  items: Article[];
  total: number;
  page: number;
  page_size: number;
}

export interface DistributionItem {
  label: string;
  value: number;
}

export interface TrendPoint {
  date: string;
  total: number;
  negative: number;
}

export interface DashboardStats {
  total_articles: number;
  negative_ratio: number;
  today_new: number;
  active_rules: number;
  top_source: string;
  trend: TrendPoint[];
  source_distribution: DistributionItem[];
  sentiment_distribution: DistributionItem[];
  top_keywords: DistributionItem[];
  highlighted_articles: Article[];
}

export interface KeywordRule {
  id: string;
  name: string;
  include_keywords: string[];
  exclude_keywords: string[];
  sentiment_threshold: SentimentLabel | null;
  source_scope: SourceType[];
  enabled: boolean;
  notification_channels: string[];
  created_by: string;
  updated_at: string;
}

export interface AlertEvent {
  id: string;
  rule_id: string;
  article_id: string;
  rule_name: string;
  article_title: string;
  trigger_reason: string;
  triggered_at: string;
  notification_status: NotificationStatus;
  notification_receipt: string;
}

export interface ReportTask {
  id: string;
  report_type: string;
  time_range: string;
  status: ReportStatus;
  output_format: ReportOutputFormat;
  download_url: string | null;
  error_message?: string | null;
  triggered_by: string;
  created_at: string;
}

export interface ReportCreateRequest {
  report_type: string;
  time_range: string;
  output_format: ReportOutputFormat;
  triggered_by: string;
}

export interface CompanyProfile {
  company_name: string;
  aliases: string[];
  industry: string;
  regions: string[];
  keywords: string[];
  notes: string;
  updated_at: string;
}

export interface CompanyProfileUpdateRequest {
  company_name: string;
  aliases: string[];
  industry: string;
  regions: string[];
  keywords: string[];
  notes: string;
}

export interface CompanyBootstrapResult {
  company_profile: CompanyProfile;
  generated_rule_names: string[];
  fetched_articles: number;
  total_articles: number;
  source_label: string;
  article_titles: string[];
}
