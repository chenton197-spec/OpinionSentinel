import Link from "next/link";

export default function LoginPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[var(--bg)] px-4 py-10 text-[var(--text)]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,122,89,0.24),transparent_30%),radial-gradient(circle_at_80%_0%,rgba(89,191,255,0.18),transparent_28%)]" />
      <div className="relative w-full max-w-md rounded-[32px] border border-white/10 bg-[var(--surface-strong)] p-8 shadow-[0_30px_100px_rgba(15,23,42,0.42)]">
        <p className="text-xs uppercase tracking-[0.3em] text-[var(--muted)]">Internal Access</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">登录公司舆情监控台</h1>
        <p className="mt-3 text-sm leading-7 text-[var(--muted)]">MVP 阶段默认采用极简账号体系。当前页面用于演示登录入口与后续权限扩展位置。</p>
        <div className="mt-8 space-y-4">
          <input className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none" placeholder="邮箱或工号" />
          <input className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none" placeholder="密码" type="password" />
        </div>
        <Link href="/dashboard" className="mt-6 inline-flex w-full items-center justify-center rounded-full bg-[var(--accent)] px-4 py-3 text-sm font-medium text-[var(--accent-contrast)]">
          进入后台
        </Link>
      </div>
    </div>
  );
}
