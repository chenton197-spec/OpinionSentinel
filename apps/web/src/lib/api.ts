import {
  mockAlerts,
  mockArticleList,
  mockArticles,
  mockCompanyProfile,
  mockDashboard,
  mockReports,
  mockRules,
} from "@/lib/mock-data";
import type {
  AlertEvent,
  Article,
  ArticleListResponse,
  CompanyBootstrapResult,
  CompanyProfile,
  CompanyProfileUpdateRequest,
  DashboardStats,
  KeywordRule,
  ReportCreateRequest,
  ReportTask,
} from "@/types";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, fallback: T, init?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      next: init?.cache === "no-store" ? undefined : { revalidate: 30 },
      ...init,
    });

    if (!response.ok) {
      throw new Error(`Request failed for ${path}`);
    }

    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export async function getDashboard(): Promise<DashboardStats> {
  return request("/dashboard/overview", mockDashboard);
}

export async function getArticles(params?: {
  keyword?: string;
  source_type?: string;
  sentiment?: string;
  only_rule_hits?: boolean;
  company_scope?: boolean;
}): Promise<ArticleListResponse> {
  const search = new URLSearchParams();
  if (params?.keyword) search.set("keyword", params.keyword);
  if (params?.source_type) search.set("source_type", params.source_type);
  if (params?.sentiment) search.set("sentiment", params.sentiment);
  if (params?.only_rule_hits) search.set("only_rule_hits", "true");
  if (params?.company_scope) search.set("company_scope", "true");
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return request(`/articles${suffix}`, mockArticleList);
}

export async function getArticle(articleId: string): Promise<Article | null> {
  return request(`/articles/${articleId}`, mockArticles.find((item) => item.id === articleId) ?? null);
}

export async function getRules(): Promise<KeywordRule[]> {
  return request("/rules", mockRules);
}

export async function getAlerts(): Promise<AlertEvent[]> {
  return request("/alerts", mockAlerts);
}

export async function getReports(): Promise<ReportTask[]> {
  return request("/reports", mockReports, { cache: "no-store" });
}

export async function createReport(payload: ReportCreateRequest): Promise<ReportTask> {
  const response = await fetch(`${apiBaseUrl}/reports`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to create report");
  }

  return (await response.json()) as ReportTask;
}

export async function getCompanyProfile(): Promise<CompanyProfile> {
  return request("/company", mockCompanyProfile);
}

export async function updateCompanyProfile(payload: CompanyProfileUpdateRequest): Promise<CompanyProfile> {
  const response = await fetch(`${apiBaseUrl}/company`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to update company profile");
  }

  return (await response.json()) as CompanyProfile;
}

export async function refreshCompanyNews(): Promise<CompanyBootstrapResult> {
  const response = await fetch(`${apiBaseUrl}/company/refresh-news`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to refresh company news");
  }

  return (await response.json()) as CompanyBootstrapResult;
}


export async function enrichCompanyProfile(company_name: string) {
  const res = await fetch(`${apiBaseUrl}/company/enrich`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company_name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "请求补全接口失败");
  }
  return res.json();
}
