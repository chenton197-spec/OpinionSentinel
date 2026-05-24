import type { Article, ArticleListResponse, DashboardStats, KeywordRule, AlertEvent, ReportTask, CompanyProfile } from "@/types";

export const mockArticles: Article[] = [];
export const mockArticleList: ArticleListResponse = { items: [], total: 0, page: 1, page_size: 10 };
export const mockDashboard: DashboardStats = { total_articles: 0, negative_ratio: 0, today_new: 0, active_rules: 0, top_source: "", trend: [], source_distribution: [], sentiment_distribution: [], top_keywords: [], highlighted_articles: [] };
export const mockRules: KeywordRule[] = [];
export const mockAlerts: AlertEvent[] = [];
export const mockReports: ReportTask[] = [];
export const mockCompanyProfile: CompanyProfile = {
  company_name: "未配置主体",
  aliases: [],
  industry: "未知",
  regions: ["全国"],
  keywords: [],
  notes: "",
  updated_at: new Date().toISOString(),
};
