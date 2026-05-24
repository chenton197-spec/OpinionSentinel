import { CompanyProfileForm } from "@/components/company-profile-form";
import { AppShell } from "@/components/app-shell";
import { Panel } from "@/components/panel";
import { getCompanyProfile } from "@/lib/api";

const services = [
  { name: "Next.js Web", detail: "后台页面与路由" },
  { name: "FastAPI API", detail: "业务接口与调度入口" },
  { name: "PostgreSQL", detail: "主数据存储" },
  { name: "Elasticsearch", detail: "全文检索与聚合" },
  { name: "Redis / Celery", detail: "异步任务与重试队列" },
];

export default async function SettingsPage() {
  const companyProfile = await getCompanyProfile();

  return (
    <AppShell title="系统设置" description="这里可以配置你真正要监控的公司主体。保存后会自动补默认关键词、生成基础规则，并尝试抓取该公司的企业官网/公告候选和新闻门户结果。">
      <Panel title="监控公司配置" eyebrow="Company Profile">
        <CompanyProfileForm initialProfile={companyProfile} />
      </Panel>

      <section className="grid gap-6 lg:grid-cols-2">
        <Panel title="运行组成" eyebrow="Infra">
          <div className="space-y-3 text-sm text-[var(--muted)]">
            {services.map((service) => (
              <div key={service.name} className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/10 px-4 py-3">
                <span className="text-white">{service.name}</span>
                <span>{service.detail}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="演示模式说明" eyebrow="Demo Mode">
          <ul className="space-y-3 text-sm leading-7 text-[var(--muted)]">
            <li>当前默认支持后端接口不可用时的前端本地回退数据，便于演示。</li>
            <li>你现在可以先在本页输入实际公司，保存为监控主体配置。</li>
            <li>保存后会自动生成基础规则，并尝试从企业官网/公告候选和新闻门户抓取相关结果；如果外网源超时，页面仍会保留已保存配置。</li>
          </ul>
        </Panel>
      </section>
    </AppShell>
  );
}
