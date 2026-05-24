import { AppShell } from "@/components/app-shell";
import { Panel } from "@/components/panel";
import { getRules } from "@/lib/api";

export default async function RulesPage() {
  const rules = await getRules();

  return (
    <AppShell title="关键词规则" description="首期规则引擎支持包含词、排除词、情感阈值、来源范围和通知通道配置。前端当前以可演示表单结构和规则列表为主。">
      <section className="grid gap-6 xl:grid-cols-[1.05fr_1.35fr]">
        <Panel title="新建规则草案" eyebrow="Rule Composer">
          <div className="space-y-4 text-sm text-[var(--muted)]">
            <div className="rounded-[22px] border border-dashed border-white/15 bg-black/10 p-4 leading-7">
              <p className="font-medium text-white">推荐字段</p>
              <p className="mt-2">包含词：品牌名、物流、客服、投诉</p>
              <p>排除词：招聘、活动、非品牌词</p>
              <p>情感阈值：negative</p>
              <p>来源范围：新闻门户、搜索聚合</p>
              <p>通知通道：飞书优先</p>
            </div>
            <div className="rounded-[22px] border border-white/10 bg-black/10 p-4 leading-7">
              <p className="font-medium text-white">后续接入方向</p>
              <p className="mt-2">下一步可直接把这里替换为 Client Form，并调用后端 POST /api/rules 完成真实创建。</p>
            </div>
          </div>
        </Panel>

        <Panel title="已生效规则" eyebrow="Active Rules">
          <div className="space-y-4">
            {rules.map((rule) => (
              <div key={rule.id} className="rounded-[24px] border border-white/10 bg-black/10 p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h4 className="text-base font-semibold text-white">{rule.name}</h4>
                    <p className="mt-1 text-sm text-[var(--muted)]">创建人：{rule.created_by} · 更新时间：{new Date(rule.updated_at).toLocaleString("zh-CN")}</p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs ${rule.enabled ? "bg-emerald-400/15 text-emerald-200" : "bg-white/8 text-[var(--muted)]"}`}>
                    {rule.enabled ? "启用中" : "已停用"}
                  </span>
                </div>
                <div className="mt-4 grid gap-3 text-sm text-[var(--muted)] md:grid-cols-2">
                  <p>包含词：{rule.include_keywords.join("、")}</p>
                  <p>排除词：{rule.exclude_keywords.length ? rule.exclude_keywords.join("、") : "无"}</p>
                  <p>情感阈值：{rule.sentiment_threshold ?? "不限"}</p>
                  <p>通知通道：{rule.notification_channels.join("、")}</p>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </section>
    </AppShell>
  );
}
