import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Hexagon, LayoutGrid, LogIn, Shield } from "lucide-react";

const METRIC_SEED = {
  txns: 12847,
  alerts: 53,
  prAuc: 0.934,
  rules: 185,
};

const DETECTIONS = [
  { id: "TX-8821", label: "Mixer layering", score: 0.97, tier: "high" as const },
  { id: "TX-8740", label: "Structuring", score: 0.83, tier: "high" as const },
  { id: "TX-8692", label: "Chain-hop", score: 0.79, tier: "mid" as const },
  { id: "TX-8611", label: "NFT wash trade", score: 0.74, tier: "mid" as const },
  { id: "TX-8550", label: "Low-velocity test", score: 0.12, tier: "low" as const },
];

function tierDot(tier: (typeof DETECTIONS)[number]["tier"]) {
  if (tier === "high") return "bg-[#f87171]";
  if (tier === "mid") return "bg-[#fbbf24]";
  return "bg-[#34d399]";
}

export default function LoginPage() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState(METRIC_SEED.alerts);
  const [remember, setRemember] = useState(true);

  useEffect(() => {
    const id = window.setInterval(() => {
      setAlerts((a) => a + 1);
    }, 7000);
    return () => window.clearInterval(id);
  }, []);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    navigate("/dashboard");
  }

  return (
    <div className="min-h-screen bg-[#060810] text-[#e6edf3]">
      <div className="mx-auto flex min-h-screen max-w-[1200px] flex-col lg:flex-row">
        <section className="flex flex-1 flex-col justify-center px-8 py-12 lg:max-w-[52%] lg:px-12 lg:py-16">
          <Link
            to="/"
            className="mb-10 inline-flex items-center gap-2 font-display text-lg font-bold tracking-tight text-[#e6edf3]"
          >
            <span className="relative flex h-8 w-8 items-center justify-center rounded-md border border-[#34d399]/35 bg-[#0d1117]">
              <Hexagon className="h-5 w-5 text-[#34d399]" aria-hidden />
            </span>
            AEGIS AML
          </Link>

          <h1 className="font-display text-3xl font-bold tracking-tight md:text-4xl">
            Welcome back to{" "}
            <span className="text-[#34d399]">Aegis.</span>
          </h1>
          <p className="mt-3 max-w-md font-data text-sm leading-relaxed text-[#9aa7b8]">
            Sign in to access your risk dashboard, case queue, and detection pipeline.
          </p>

          <form className="mt-10 max-w-md space-y-5" onSubmit={onSubmit}>
            <div>
              <label
                htmlFor="email"
                className="font-data text-[11px] font-medium uppercase tracking-wide text-[#9aa7b8]"
              >
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder="analyst@aegis.io"
                className="mt-1.5 w-full rounded-md border border-[var(--color-aegis-border)] bg-[#0d1117] px-3 py-2.5 font-mono text-sm text-[#e6edf3] placeholder:text-[#5c6b7e] outline-none ring-0 focus:border-[#34d399]/45"
              />
            </div>
            <div>
              <div className="flex items-center justify-between gap-2">
                <label
                  htmlFor="password"
                  className="font-data text-[11px] font-medium uppercase tracking-wide text-[#9aa7b8]"
                >
                  Password
                </label>
                <button
                  type="button"
                  className="font-data text-[11px] text-[#a78bfa] hover:text-[#c4b5fd]"
                >
                  Forgot password?
                </button>
              </div>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••••••"
                className="mt-1.5 w-full rounded-md border border-[var(--color-aegis-border)] bg-[#0d1117] px-3 py-2.5 font-mono text-sm text-[#e6edf3] placeholder:text-[#5c6b7e] outline-none focus:border-[#34d399]/45"
              />
            </div>

            <label className="flex cursor-pointer items-center gap-2 font-data text-[13px] text-[#9aa7b8]">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="h-4 w-4 rounded border-[var(--color-aegis-border)] bg-[#0d1117] text-[#34d399] focus:ring-[#34d399]/40"
              />
              Remember this device for 30 days
            </label>

            <button
              type="submit"
              className="flex w-full items-center justify-center gap-2 rounded-md border border-[#3d4a5c] bg-[#0d1117] px-4 py-3 font-data text-sm font-medium text-[#e6edf3] transition-colors hover:border-[#34d399]/40 hover:bg-[#060810]"
            >
              <LogIn className="h-4 w-4 text-[#34d399]" aria-hidden />
              Sign in to Dashboard
            </button>

            <div className="relative py-2 text-center font-data text-[11px] text-[#6b7c90]">
              <span className="relative z-10 bg-[#060810] px-3">or continue with</span>
              <span className="absolute left-0 right-0 top-1/2 h-px -translate-y-1/2 bg-[var(--color-aegis-border)]" />
            </div>

            <button
              type="button"
              className="flex w-full items-center justify-center gap-2 rounded-md border border-[var(--color-aegis-border)] bg-[#0d1117] px-4 py-3 font-data text-sm text-[#c8d4e0] hover:border-[#a78bfa]/35"
            >
              <LayoutGrid className="h-4 w-4 text-[#9aa7b8]" aria-hidden />
              Continue with SSO / SAML
            </button>
          </form>

          <footer className="mt-12 flex flex-wrap items-center gap-x-4 gap-y-2 font-data text-[11px] text-[#6b7c90]">
            <a href="#privacy" className="hover:text-[#c8d4e0]">
              Privacy Policy
            </a>
            <span className="text-[var(--color-aegis-border)]">·</span>
            <a href="#security" className="hover:text-[#c8d4e0]">
              Security
            </a>
            <span className="text-[var(--color-aegis-border)]">·</span>
            <a href="#terms" className="hover:text-[#c8d4e0]">
              Terms
            </a>
            <span className="ml-auto text-[#5c6b7e]">Aegis AML Platform v1.0 MVP</span>
          </footer>
        </section>

        <aside className="relative flex flex-1 flex-col border-t border-[var(--color-aegis-border)] bg-[#0d1117] bg-[linear-gradient(rgba(56,189,248,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(56,189,248,0.04)_1px,transparent_1px)] bg-[size:24px_24px] px-8 py-12 lg:border-l lg:border-t-0 lg:px-10 lg:py-16">
          <p className="font-mono text-[10px] font-medium uppercase tracking-[0.2em] text-[#34d399]">
            — Live platform stats
          </p>
          <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810]/60 p-4">
              <p className="font-display text-2xl font-semibold tabular-nums text-[#34d399]">
                {METRIC_SEED.txns.toLocaleString()}
              </p>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-wide text-[#9aa7b8]">
                Transactions scored today
              </p>
            </div>
            <div className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810]/60 p-4">
              <p className="font-display text-2xl font-semibold tabular-nums text-[#7dd3fc]">
                {alerts}
              </p>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-wide text-[#9aa7b8]">
                Active risk alerts
              </p>
            </div>
            <div className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810]/60 p-4">
              <p className="font-display text-2xl font-semibold tabular-nums text-[#a78bfa]">
                {METRIC_SEED.prAuc}
              </p>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-wide text-[#9aa7b8]">
                PR-AUC (meta-model)
              </p>
            </div>
            <div className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810]/60 p-4">
              <p className="font-display text-2xl font-semibold tabular-nums text-[#fbbf24]">
                {METRIC_SEED.rules}
              </p>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-wide text-[#9aa7b8]">
                Typology rules active
              </p>
            </div>
          </div>

          <div className="mt-8 flex-1 rounded-lg border border-[var(--color-aegis-border)] bg-[#060810]/50 p-4">
            <div className="flex items-center justify-between gap-2">
              <h2 className="font-display text-sm font-semibold text-[#e6edf3]">
                Recent detections
              </h2>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-[#34d399]/30 bg-[#34d399]/10 px-2 py-0.5 font-mono text-[10px] text-[#34d399]">
                <span className="h-1.5 w-1.5 rounded-full bg-[#34d399]" aria-hidden />
                Live
              </span>
            </div>
            <ul className="mt-4 space-y-2">
              {DETECTIONS.map((d) => (
                <li
                  key={d.id}
                  className="flex items-center justify-between gap-3 rounded border border-[var(--color-aegis-border)]/80 bg-[#0d1117]/80 px-3 py-2 font-mono text-[11px]"
                >
                  <span className="flex min-w-0 items-center gap-2 text-[#c8d4e0]">
                    <span className={`h-2 w-2 shrink-0 rounded-full ${tierDot(d.tier)}`} />
                    <span className="tabular-nums text-[#9aa7b8]">{d.id}</span>
                    <span className="truncate text-[#e6edf3]">{d.label}</span>
                  </span>
                  <span className="shrink-0 tabular-nums text-[#c8d4e0]">{d.score.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-6 font-mono text-[10px] text-[#6b7c90]">
            <span className="inline-flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5" aria-hidden />
              SOC 2 Type II
            </span>
            <span>AES-256 Encrypted</span>
            <span>99.9% Uptime</span>
          </div>
        </aside>
      </div>
    </div>
  );
}
