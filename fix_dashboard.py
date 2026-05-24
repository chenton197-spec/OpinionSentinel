import re

with open("apps/api/app/services/dashboard_service.py", "r") as f:
    code = f.read()

import_line = "from app.services.article_service import _matches_company_scope"
if import_line not in code:
    code = code.replace("from app.data.demo_store", f"{import_line}\nfrom app.data.demo_store")

if "articles = [a for a in get_articles() if _matches_company_scope(a)]" not in code:
    code = code.replace("articles = get_articles()", "articles = [a for a in get_articles() if _matches_company_scope(a)]")

if "len(articles) == 0" not in code: # Handle empty state gracefully for the dashboard max / index operations
    empty_handling = """    if not articles:
        return DashboardStats(
            total_articles=0, negative_ratio=0.0, today_new=0, active_rules=len([r for r in rules if r.enabled]),
            top_source="-", trend=[], source_distribution=[], sentiment_distribution=[], top_keywords=[], highlighted_articles=[]
        )"""
    code = code.replace("news_first_articles = ", f"{empty_handling}\n    news_first_articles = ")

with open("apps/api/app/services/dashboard_service.py", "w") as f:
    f.write(code)

print("Dashboard service updated")
