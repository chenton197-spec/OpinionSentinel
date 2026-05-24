from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
import re

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
from reportlab.pdfgen import canvas

from app.data.demo_store import add_report, get_articles, get_company_profile, get_report, get_reports, get_rules, update_report
from app.schemas.domain import ReportCreateRequest, ReportOutputFormat, ReportStatus, ReportTask, SentimentLabel, SourceType
from app.services.dashboard_service import get_dashboard_stats

TZ = timezone(timedelta(hours=8))
TWO_HOURS = timedelta(hours=2)
TWELVE_HOURS = timedelta(hours=12)


def _headline_key(title: str) -> str:
    return title.split(" - ")[0].strip().lower()


def _article_terms(article) -> set[str]:
    terms = {
        _headline_key(article.title),
        *(item.keyword.lower() for item in article.keyword_hits),
        *(tag.lower() for tag in article.tags),
    }
    return {term for term in terms if term}


def _shares_similarity(left, right) -> bool:
    left_headline = _headline_key(left.title)
    right_headline = _headline_key(right.title)
    if left_headline and right_headline and (
        left_headline == right_headline
        or left_headline in right_headline
        or right_headline in left_headline
    ):
        return True

    shared = _article_terms(left) & _article_terms(right)
    return len(shared) >= 2


def _within_window(left, right, window: timedelta) -> bool:
    return abs(left.published_at - right.published_at) <= window


def _is_llm_negative(article) -> bool:
    return article.sentiment.label == SentimentLabel.NEGATIVE and article.sentiment.confidence >= 0.7


def _build_article_signals(article, articles, negative_rule_ids: set[str]) -> dict[str, object]:
    negative_rule_hit = any(rule_id in negative_rule_ids for rule_id in article.rule_hit_ids)
    similar_recent = [
        candidate
        for candidate in articles
        if candidate.id != article.id and _within_window(article, candidate, TWO_HOURS) and _shares_similarity(article, candidate)
    ]
    duplicate_candidates = [
        candidate
        for candidate in articles
        if candidate.id != article.id and _within_window(article, candidate, TWELVE_HOURS) and _shares_similarity(article, candidate)
    ] if article.source_type == SourceType.SEARCH else []
    official_response = next(
        (
            candidate
            for candidate in sorted(articles, key=lambda item: item.published_at, reverse=True)
            if candidate.id != article.id
            and candidate.source_type == SourceType.COMPANY
            and len(_article_terms(article) & _article_terms(candidate)) >= 1
        ),
        None,
    )
    heating_up = negative_rule_hit and _is_llm_negative(article) and len(similar_recent) >= 2
    return {
        "duplicate_candidates": duplicate_candidates,
        "heating_up": heating_up,
        "official_response": official_response,
        "recent_signal_count": len(similar_recent),
        "should_deduplicate_first": article.source_type == SourceType.SEARCH and len(duplicate_candidates) > 0,
        "should_highlight_in_daily": heating_up,
        "should_suggest_official_response": article.source_type == SourceType.NEWS and article.risk_score > 70,
        "should_trigger_feishu_alert": heating_up,
    }


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\-]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "report"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _exports_dir() -> Path:
    exports_dir = _project_root() / "apps" / "web" / "public" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    return exports_dir


def _render_distribution(items) -> str:
    return "".join(
        f"<li><span>{escape(item.label)}</span><strong>{item.value}</strong></li>"
        for item in items
    )


def _render_trend(trend) -> str:
    return "".join(
        f"<tr><td>{escape(point.date)}</td><td>{point.total}</td><td>{point.negative}</td></tr>"
        for point in trend
    )


def _render_focus_items(articles, signal_map) -> str:
    blocks: list[str] = []
    for article in articles:
        signals = signal_map[article.id]
        tags: list[str] = []
        if signals["should_highlight_in_daily"]:
            tags.append("日报加粗")
        if signals["should_trigger_feishu_alert"]:
            tags.append("飞书告警")
        if signals["should_suggest_official_response"]:
            tags.append("补官方回应")
        if signals["should_deduplicate_first"]:
            tags.append("先去重")

        recommendation = "继续观察。"
        if signals["should_highlight_in_daily"]:
            recommendation = f"近 2 小时内有 {signals['recent_signal_count']} 条相似负面舆情升温，建议日报加粗并触发飞书告警。"
        elif signals["should_suggest_official_response"]:
            official_response = signals["official_response"]
            if official_response:
                recommendation = f"建议补充官方回应链接：{official_response.original_url}"
            else:
                recommendation = "建议补录官网公告或声明链接，补齐官方回应。"
        elif signals["should_deduplicate_first"]:
            recommendation = f"搜索聚合存在 {len(signals['duplicate_candidates'])} 条潜在重复项，建议先去重。"

        blocks.append(
            f"""
            <article class=\"focus-card {'focus-strong' if signals['should_highlight_in_daily'] else ''}\">
              <div class=\"focus-header\">
                <h3>{escape(article.title)}</h3>
                <div class=\"badges\">{''.join(f'<span>{escape(tag)}</span>' for tag in tags) or '<span>观察中</span>'}</div>
              </div>
              <p class=\"meta\">来源：{escape(article.source_name)} · 风险分：{article.risk_score} · 发布时间：{article.published_at.strftime('%Y-%m-%d %H:%M')}</p>
              <p>{escape(article.summary)}</p>
              <p class=\"recommendation\">{escape(recommendation)}</p>
            </article>
            """
        )

    return "".join(blocks)


def _build_report_html(report: ReportTask) -> str:
    dashboard = get_dashboard_stats()
    articles = get_articles()
    profile = get_company_profile()
    rules = get_rules()
    negative_rule_ids = {rule.id for rule in rules if rule.sentiment_threshold == SentimentLabel.NEGATIVE}
    signal_map = {
        article.id: _build_article_signals(article, articles, negative_rule_ids)
        for article in articles
    }
    focus_articles = sorted(articles, key=lambda item: item.risk_score, reverse=True)[:5]
    highlighted_count = len([article for article in focus_articles if signal_map[article.id]["should_highlight_in_daily"]])
    generated_at = datetime.now(tz=TZ)

    return f"""
<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"utf-8\" />
    <title>{escape(profile.company_name)} {escape(report.report_type.upper())} 报表</title>
    <style>
      :root {{ color-scheme: light; }}
      body {{ font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Segoe UI', sans-serif; margin: 0; background: #f5f7fb; color: #172033; }}
      .wrap {{ max-width: 1080px; margin: 0 auto; padding: 32px 24px 56px; }}
      .hero {{ background: linear-gradient(135deg, #172033, #243b5a); color: #fff; border-radius: 28px; padding: 28px 32px; box-shadow: 0 18px 50px rgba(23,32,51,0.18); }}
      .hero p {{ color: rgba(255,255,255,0.78); }}
      .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin-top: 24px; }}
      .card, .panel {{ background: #fff; border-radius: 24px; border: 1px solid #e5ebf5; box-shadow: 0 14px 38px rgba(15,23,42,0.06); }}
      .card {{ padding: 20px; }}
      .card strong {{ display: block; margin-top: 12px; font-size: 32px; }}
      .panels {{ display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 20px; margin-top: 24px; }}
      .panel {{ padding: 22px; }}
      .panel h2 {{ margin: 0 0 16px; font-size: 18px; }}
      .list, .dist {{ margin: 0; padding: 0; list-style: none; display: grid; gap: 12px; }}
      .dist li {{ display: flex; justify-content: space-between; gap: 12px; padding: 12px 14px; background: #f6f8fc; border-radius: 16px; }}
      table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
      th, td {{ padding: 10px 8px; border-bottom: 1px solid #ebeff6; text-align: left; }}
      .focus-list {{ display: grid; gap: 14px; margin-top: 24px; }}
      .focus-card {{ background: #fff; border: 1px solid #e5ebf5; border-radius: 22px; padding: 18px 20px; }}
      .focus-strong {{ border-color: #f1a0aa; background: #fff5f6; }}
      .focus-header {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }}
      .focus-header h3 {{ margin: 0; font-size: 18px; }}
      .badges {{ display: flex; flex-wrap: wrap; gap: 8px; }}
      .badges span {{ background: #edf2ff; color: #294a7a; border-radius: 999px; padding: 6px 10px; font-size: 12px; }}
      .meta {{ color: #66758f; font-size: 13px; }}
      .recommendation {{ font-weight: 600; color: #172033; }}
      @media (max-width: 900px) {{ .grid, .panels {{ grid-template-columns: 1fr; }} .focus-header {{ flex-direction: column; }} }}
    </style>
  </head>
  <body>
    <main class=\"wrap\">
      <section class=\"hero\">
        <p>Company Reputation Monitor</p>
        <h1>{escape(profile.company_name)} {escape(report.report_type.upper())} 报表</h1>
        <p>时间范围：{escape(report.time_range)} · 生成时间：{generated_at.strftime('%Y-%m-%d %H:%M:%S')} · 统计口径：复用看板 DashboardStats</p>
      </section>

      <section class=\"grid\">
        <article class=\"card\"><span>总舆情量</span><strong>{dashboard.total_articles}</strong><p>与看板 total_articles 保持一致</p></article>
        <article class=\"card\"><span>负面占比</span><strong>{round(dashboard.negative_ratio * 100)}%</strong><p>与看板 negative_ratio 保持一致</p></article>
        <article class=\"card\"><span>今日新增</span><strong>{dashboard.today_new}</strong><p>与看板 today_new 保持一致</p></article>
        <article class=\"card\"><span>启用规则</span><strong>{dashboard.active_rules}</strong><p>与看板 active_rules 保持一致</p></article>
      </section>

      <section class=\"panels\">
        <section class=\"panel\">
          <h2>趋势观察</h2>
          <table>
            <thead><tr><th>日期</th><th>总量</th><th>负面</th></tr></thead>
            <tbody>{_render_trend(dashboard.trend)}</tbody>
          </table>
        </section>
        <section class=\"panel\">
          <h2>分布概览</h2>
          <ul class=\"dist\">{_render_distribution(dashboard.source_distribution[:5])}</ul>
          <h2 style=\"margin-top:18px\">高频关键词</h2>
          <ul class=\"dist\">{_render_distribution(dashboard.top_keywords[:5])}</ul>
        </section>
      </section>

      <section class=\"panel\" style=\"margin-top:24px\">
        <h2>日报重点建议</h2>
        <p>重点来源：{escape(dashboard.top_source)} · 加粗条目：{highlighted_count} · 说明：以下条目按风险分排序，并附加去重、官方回应、飞书告警建议。</p>
        <div class=\"focus-list\">{_render_focus_items(focus_articles, signal_map)}</div>
      </section>
    </main>
  </body>
</html>
    """.strip()


def _draw_pdf_line(pdf: canvas.Canvas, text: str, x: int, y: int, *, font_name: str = "STSong-Light", font_size: int = 11) -> int:
    pdf.setFont(font_name, font_size)
    max_width = 520
    current = ""
    for char in text:
        next_text = f"{current}{char}"
        if stringWidth(next_text, font_name, font_size) <= max_width:
            current = next_text
            continue
        pdf.drawString(x, y, current)
        y -= 16
        current = char
    if current:
        pdf.drawString(x, y, current)
        y -= 16
    return y


def _build_report_pdf(report: ReportTask, output_path: Path) -> None:
    dashboard = get_dashboard_stats()
    articles = get_articles()
    rules = get_rules()
    negative_rule_ids = {rule.id for rule in rules if rule.sentiment_threshold == SentimentLabel.NEGATIVE}
    focus_articles = sorted(articles, key=lambda item: item.risk_score, reverse=True)[:5]
    profile = get_company_profile()
    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    y = height - 56

    pdf.setFont("STSong-Light", 18)
    pdf.drawString(40, y, f"{profile.company_name} {report.report_type.upper()} Report")
    y -= 24
    pdf.setFont("STSong-Light", 11)
    pdf.drawString(40, y, f"Time Range: {report.time_range}    Generated At: {datetime.now(tz=TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 28
    for line in [
        f"Total Articles: {dashboard.total_articles}",
        f"Negative Ratio: {round(dashboard.negative_ratio * 100)}%",
        f"Today New: {dashboard.today_new}",
        f"Active Rules: {dashboard.active_rules}",
        f"Top Source: {dashboard.top_source}",
    ]:
        pdf.drawString(40, y, line)
        y -= 18

    y -= 12
    pdf.setFont("STSong-Light", 14)
    pdf.drawString(40, y, "Daily Focus")
    y -= 24
    for article in focus_articles:
        signals = _build_article_signals(article, articles, negative_rule_ids)
        y = _draw_pdf_line(pdf, f"- {article.title}", 40, y, font_name="STSong-Light", font_size=12)
        y = _draw_pdf_line(pdf, f"  Source: {article.source_name}  Risk: {article.risk_score}", 40, y)
        recommendation = "Continue observing."
        if signals["should_highlight_in_daily"]:
            recommendation = f"Heat up within 2h with {signals['recent_signal_count']} similar negative articles. Trigger alert and highlight in daily report."
        elif signals["should_suggest_official_response"]:
            official_response = signals["official_response"]
            recommendation = f"Supplement official response link: {official_response.original_url if official_response else 'missing official response'}"
        elif signals["should_deduplicate_first"]:
            recommendation = f"Deduplicate {len(signals['duplicate_candidates'])} search aggregation candidates before escalation."
        y = _draw_pdf_line(pdf, f"  {recommendation}", 40, y)
        y -= 8
        if y < 100:
            pdf.showPage()
            y = height - 56

    pdf.save()


def _report_filename(report: ReportTask) -> str:
    suffix = "html" if report.output_format == ReportOutputFormat.HTML else "pdf"
    return f"{_slugify(report.report_type)}-{_slugify(report.time_range)}-{report.created_at.strftime('%Y%m%d%H%M%S')}.{suffix}"


def generate_report_export(report_id: str) -> ReportTask:
    report = update_report(report_id, status=ReportStatus.RUNNING, error_message="")
    output_path = _exports_dir() / _report_filename(report)

    try:
        if report.output_format == ReportOutputFormat.PDF:
            _build_report_pdf(report, output_path)
        else:
            output_path.write_text(_build_report_html(report), encoding="utf-8")
        return update_report(
            report_id,
            status=ReportStatus.READY,
            download_url=f"/exports/{output_path.name}",
            error_message="",
        )
    except Exception as exc:
        return update_report(report_id, status=ReportStatus.FAILED, error_message=str(exc))


def list_reports() -> list[ReportTask]:
    reports = get_reports()
    reports.sort(key=lambda item: item.created_at, reverse=True)
    return reports


def create_report(payload: ReportCreateRequest) -> ReportTask:
    report = add_report(
        payload.report_type,
        payload.time_range,
        payload.triggered_by,
        output_format=payload.output_format,
        status=ReportStatus.PENDING,
        created_at=datetime.now(tz=TZ),
    )
    try:
        from app.tasks.report_tasks import generate_report_export_task

        generate_report_export_task.delay(report.id)
    except Exception as exc:
        return update_report(report.id, status=ReportStatus.FAILED, error_message=str(exc))
    return get_report(report.id)
