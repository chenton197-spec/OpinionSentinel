"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { createReport } from "@/lib/api";
import type { ReportOutputFormat } from "@/types";

function todayInShanghai(): string {
  return new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Shanghai" }).format(new Date());
}

export function ReportExportForm() {
  const router = useRouter();
  const [message, setMessage] = useState<string>("");
  const [downloadUrl, setDownloadUrl] = useState<string>("");
  const [isPending, startTransition] = useTransition();

  function submitExport(outputFormat: ReportOutputFormat) {
    setMessage("");
    setDownloadUrl("");
    startTransition(async () => {
      try {
        const report = await createReport({
          report_type: "daily",
          time_range: todayInShanghai(),
          output_format: outputFormat,
          triggered_by: "web_admin",
        });
        const exportLabel = outputFormat.toUpperCase();
        if (report.status === "ready") {
          setMessage(`已生成 ${report.report_type.toUpperCase()} ${exportLabel} 报表，统计口径与看板保持一致。`);
          setDownloadUrl(report.download_url ?? "");
        } else if (report.status === "failed") {
          setMessage(report.error_message || `${exportLabel} 日报导出失败，请检查 Celery Worker 与 Redis。`);
        } else {
          setMessage(`已提交 ${exportLabel} 日报任务，Celery Worker 完成后会在历史任务中出现下载链接。`);
        }
        router.refresh();
      } catch {
        setMessage(`${outputFormat.toUpperCase()} 日报导出失败，请确认前后端服务、Redis 与 Celery Worker 已启动。`);
      }
    });
  }

  return (
    <div className="space-y-4">
      <p className="text-sm leading-7 text-[var(--muted)]">
        点击后会按当前看板同口径统计生成一份 HTML 或 PDF 日报；任务先写入后端，再由 Celery Worker 异步导出到可下载目录。
      </p>
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={isPending}
          onClick={() => submitExport("html")}
          className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-[var(--accent-contrast)] disabled:opacity-60"
        >
          {isPending ? "生成中..." : "生成今日 HTML 日报"}
        </button>
        <button
          type="button"
          disabled={isPending}
          onClick={() => submitExport("pdf")}
          className="rounded-full border border-white/10 px-5 py-3 text-sm font-medium text-white hover:bg-white/8 disabled:opacity-60"
        >
          {isPending ? "生成中..." : "生成今日 PDF 日报"}
        </button>
        {downloadUrl ? (
          <a href={downloadUrl} target="_blank" rel="noreferrer" className="rounded-full border border-white/10 px-4 py-3 text-sm text-white hover:bg-white/8">
            打开导出文件
          </a>
        ) : null}
      </div>
      {message ? <p className="text-sm text-[var(--muted)]">{message}</p> : null}
    </div>
  );
}