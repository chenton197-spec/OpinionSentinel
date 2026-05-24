"use client";

import { useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { refreshCompanyNews, updateCompanyProfile, enrichCompanyProfile } from "@/lib/api";
import type { CompanyProfile } from "@/types";

function splitByComma(value: string): string[] {
  return value
    .split(/[,，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function CompanyProfileForm({ initialProfile }: { initialProfile: CompanyProfile }) {
  const router = useRouter();
  const [formState, setFormState] = useState({
    company_name: initialProfile.company_name,
    aliases: initialProfile.aliases.join("，"),
    industry: initialProfile.industry,
    regions: initialProfile.regions.join("，"),
    keywords: initialProfile.keywords.join("，"),
    notes: initialProfile.notes,
  });
  const [message, setMessage] = useState<string>("");
  const [isPending, startTransition] = useTransition();
  const [isEnriching, setIsEnriching] = useState(false);

  const parsedPreview = useMemo(
    () => ({
      aliases: splitByComma(formState.aliases),
      regions: splitByComma(formState.regions),
      keywords: splitByComma(formState.keywords),
    }),
    [formState.aliases, formState.regions, formState.keywords],
  );

  return (
    <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <form
        className="space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          setMessage("");

          startTransition(async () => {
            try {
              const updated = await updateCompanyProfile({
                company_name: formState.company_name,
                aliases: splitByComma(formState.aliases),
                industry: formState.industry,
                regions: splitByComma(formState.regions),
                keywords: splitByComma(formState.keywords),
                notes: formState.notes,
              });
              setFormState({
                company_name: updated.company_name,
                aliases: updated.aliases.join("，"),
                industry: updated.industry,
                regions: updated.regions.join("，"),
                keywords: updated.keywords.join("，"),
                notes: updated.notes,
              });
              
              setMessage(`已保存 ${updated.company_name}。后台正自动生成监控规则及挖掘重点舆情，请稍后前往看板查看新数据。`);
              
              // 脱离 startTransition，后台异步发起新闻抓取，不再阻塞按钮
              refreshCompanyNews().then(bootstrap => {
                setMessage(`已保存 ${updated.company_name}！新拦截 ${bootstrap.fetched_articles} 条舆情 (来源: ${bootstrap.source_label})。`);
                router.refresh();
              }).catch(() => {
                setMessage("抓取最新资讯时遇到异常，请确认网络状态");
              });
              
            } catch {
              setMessage("保存或抓取失败，请确认前后端接口已启动，且网络可访问官网/新闻门户数据源");
            }
          });
        }}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-2 text-sm text-[var(--muted)]">
            <div className="flex justify-between items-center">
              <span>公司名称</span>
              <button 
                type="button" 
                disabled={isEnriching || !formState.company_name}
                onClick={async () => {
                  if (!formState.company_name || isEnriching) return;
                  setIsEnriching(true);
                  setMessage("智能补全中...");
                  try {
                    const data = await enrichCompanyProfile(formState.company_name);
                    setFormState(cur => ({
                      ...cur,
                      aliases: data.aliases && data.aliases.length > 0 ? data.aliases.join('，') : "",
                      industry: data.industry || "",
                      regions: data.regions && data.regions.length > 0 ? data.regions.join('，') : "全国",
                      keywords: data.keywords && data.keywords.length > 0 ? data.keywords.join('，') : "",
                      notes: data.notes || "",
                    }));
                    setMessage("自动补全完成，请进行确认核对");
                  } catch (e: any) {
                    setMessage("自动补全失败：" + (e.message || "请求异常"));
                  } finally {
                    setIsEnriching(false);
                  }
                }}
                className={`text-xs ${isEnriching ? 'text-[var(--muted)] cursor-not-allowed' : 'text-[var(--accent-soft)] hover:text-white'}`}
              >{isEnriching ? "✨ 补全中..." : "✨ 智能补全其他信息"}</button>
            </div>
            <input
              value={formState.company_name}
              onChange={(event) => setFormState((current) => ({ ...current, company_name: event.target.value }))}
              className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none"
              placeholder="例如：字节跳动"
            />
          </label>
          <label className="space-y-2 text-sm text-[var(--muted)]">
            <span>所属行业</span>
            <input
              value={formState.industry}
              onChange={(event) => setFormState((current) => ({ ...current, industry: event.target.value }))}
              className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none"
              placeholder="例如：互联网 / 消费电子"
            />
          </label>
        </div>

        <label className="space-y-2 text-sm text-[var(--muted)]">
          <span>别名 / 品牌别称</span>
          <input
            value={formState.aliases}
            onChange={(event) => setFormState((current) => ({ ...current, aliases: event.target.value }))}
            className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none"
            placeholder="多个值用中文逗号分隔，例如：字节、ByteDance、抖音集团"
          />
        </label>

        <label className="space-y-2 text-sm text-[var(--muted)]">
          <span>重点地域</span>
          <input
            value={formState.regions}
            onChange={(event) => setFormState((current) => ({ ...current, regions: event.target.value }))}
            className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none"
            placeholder="例如：全国，华北，华东"
          />
        </label>

        <label className="space-y-2 text-sm text-[var(--muted)]">
          <span>监控关键词</span>
          <textarea
            value={formState.keywords}
            onChange={(event) => setFormState((current) => ({ ...current, keywords: event.target.value }))}
            className="min-h-28 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none"
            placeholder="例如：公司名，产品名，投诉，服务中断，裁员"
          />
        </label>

        <label className="space-y-2 text-sm text-[var(--muted)]">
          <span>备注</span>
          <textarea
            value={formState.notes}
            onChange={(event) => setFormState((current) => ({ ...current, notes: event.target.value }))}
            className="min-h-24 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none"
            placeholder="可填写监控重点、值班备注、真实数据源说明"
          />
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={isPending}
            className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-[var(--accent-contrast)] disabled:opacity-60"
          >
            {isPending ? "保存中..." : "保存监控公司"}
          </button>
          {message ? <p className="text-sm text-[var(--muted)]">{message}</p> : null}
        </div>
      </form>

      <div className="space-y-4 rounded-[24px] border border-white/10 bg-black/10 p-5 text-sm text-[var(--muted)]">
        <div>
          <p className="text-xs uppercase tracking-[0.3em]">Preview</p>
          <h4 className="mt-2 text-lg font-semibold text-white">当前监控主体预览</h4>
        </div>
        <div className="space-y-3 leading-7">
          <p><span className="text-white">公司：</span>{formState.company_name || "未填写"}</p>
          <p><span className="text-white">行业：</span>{formState.industry || "未填写"}</p>
          <p><span className="text-white">别名：</span>{parsedPreview.aliases.length ? parsedPreview.aliases.join("、") : "未填写"}</p>
          <p><span className="text-white">地域：</span>{parsedPreview.regions.length ? parsedPreview.regions.join("、") : "未填写"}</p>
          <p><span className="text-white">关键词：</span>{parsedPreview.keywords.length ? parsedPreview.keywords.join("、") : "未填写"}</p>
        </div>
        <div className="rounded-2xl border border-dashed border-white/15 bg-black/10 p-4 leading-7">
          <p className="text-white">说明</p>
          <p className="mt-2">这一步是“告诉系统你要监控谁”。当前保存后会自动补默认关键词、生成基础规则，并尝试从企业官网/公告候选和新闻门户真实结果抓取相关内容。</p>
        </div>
      </div>
    </div>
  );
}