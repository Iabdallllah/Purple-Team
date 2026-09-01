import Link from 'next/link';
import { Shield, Zap, Brain, TrendingUp, ArrowRight, Check, Lock, BarChart3, Layers, Clock, Activity, Database, FileCheck } from 'lucide-react';

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col bg-white dark:bg-dark-950">
      <nav className="sticky top-0 z-50 border-b border-dark-100 dark:border-dark-800 bg-white/70 dark:bg-dark-950/70 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-[64px]">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-primary-600 flex items-center justify-center">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <span className="text-[15px] font-semibold tracking-tight text-dark-900 dark:text-white">Purple Platform</span>
              <span className="hidden sm:inline-flex ml-2 px-2 py-0.5 rounded-full bg-dark-900 dark:bg-white text-white dark:text-dark-900 text-[11px] font-medium tracking-wide">BETA</span>
            </div>
            <div className="hidden md:flex items-center gap-6 text-sm font-medium text-dark-600 dark:text-dark-300">
              <Link href="#features" className="hover:text-dark-900 dark:hover:text-white transition-colors">Platform</Link>
              <Link href="#capabilities" className="hover:text-dark-900 dark:hover:text-white transition-colors">Capabilities</Link>
              <Link href="/docs" className="hover:text-dark-900 dark:hover:text-white transition-colors">Docs</Link>
            </div>
            <div className="flex items-center gap-3">
              <Link href="/auth/login" className="hidden sm:inline-flex text-sm font-medium text-dark-600 dark:text-dark-300 hover:text-dark-900">
                Sign in
              </Link>
              <Link href="/auth/register" className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-dark-900 dark:bg-white text-white dark:text-dark-900 text-sm font-medium hover:opacity-90 transition-opacity">
                Get started <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary-50/50 via-white to-white dark:from-primary-950/20 dark:via-dark-950 dark:to-dark-950 pointer-events-none" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12 sm:pt-24 sm:pb-20">
          <div className="mx-auto max-w-3xl text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white dark:bg-dark-900 border border-dark-200 dark:border-dark-800 shadow-sm text-xs font-medium text-dark-600 dark:text-dark-300 mb-6">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              SOC 2 • ISO 27001 • NIST ready
              <span className="hidden sm:inline text-dark-300">—</span>
              <span className="text-primary-600 font-medium">Continuous purple teaming</span>
            </div>
            <h1 className="text-4xl sm:text-[52px] font-bold tracking-tight text-dark-900 dark:text-white leading-[1.05]">
              Autonomous purple teaming
              <span className="block text-primary-600">for modern web apps</span>
            </h1>
            <p className="mt-6 text-[17px] leading-7 text-dark-600 dark:text-dark-300 max-w-2xl mx-auto">
              Red Team and Detection Engine agents attack and defend your app 24/7 inside an isolated sandbox. Every episode improves via RAG — with a real-time Security Posture Score executives can track.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link href="/auth/register" className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-primary-600 text-white text-sm font-medium shadow-sm hover:bg-primary-700 transition-colors">
                Start free trial <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="#features" className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-lg bg-white dark:bg-dark-900 border border-dark-200 dark:border-dark-800 text-sm font-medium text-dark-700 dark:text-dark-200 hover:bg-dark-50 dark:hover:bg-dark-800 transition-colors">
                View live demo
              </Link>
            </div>
            <p className="mt-3 text-xs text-dark-500">No credit card • 14-day trial • Runs on your infra with Ollama</p>
          </div>

          <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-3xl mx-auto">
            <StatMini label="Detection rate" value="≥85%" sub="known scenarios" />
            <StatMini label="Episode" value="≤30 min" sub="per scenario" />
            <StatMini label="Scenarios" value="5" sub="IDOR → SSRF" />
            <StatMini label="Sandbox" value="Zero risk" sub="isolated Docker" />
          </div>

          <div className="mt-10 rounded-xl border border-dark-200 dark:border-dark-800 bg-white dark:bg-dark-900 shadow-sm overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-dark-100 dark:border-dark-800 bg-dark-50/50 dark:bg-dark-900">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
                <span className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
                <span className="h-2.5 w-2.5 rounded-full bg-green-400" />
                <span className="ml-2 text-xs font-medium text-dark-500">episode #47 — idor • juice-shop • 1.8 min</span>
              </div>
              <span className="text-xs font-mono px-2 py-1 rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300">DETECTED 0.92</span>
            </div>
            <div className="grid md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-dark-100 dark:divide-dark-800">
              <div className="p-4">
                <div className="text-xs font-medium text-dark-500 uppercase tracking-wide">Red Team</div>
                <div className="mt-2 font-mono text-xs leading-5 text-dark-700 dark:text-dark-300">GET /api/users/2 <span className="text-red-600">→ 200</span><br/>T1548 • A01 • horizontal_idor<br/>JWT none-alg probe → blocked after 2nd attempt</div>
              </div>
              <div className="p-4">
                <div className="text-xs font-medium text-dark-500 uppercase tracking-wide">Detection Engine</div>
                <div className="mt-2 text-xs leading-5 text-dark-700 dark:text-dark-300">Pattern: <span className="font-mono bg-dark-100 dark:bg-dark-800 px-1 rounded">role.*admin</span> + anomaly<br/>Confidence 0.92 • <span className="text-emerald-600">auto response</span>: add_auth_check</div>
              </div>
              <div className="p-4">
                <div className="text-xs font-medium text-dark-500 uppercase tracking-wide">Posture</div>
                <div className="mt-2 flex items-baseline gap-2"><span className="text-2xl font-bold">78.3</span><span className="text-xs text-emerald-600">+4.2 vs #46</span></div>
                <div className="mt-1 text-xs text-dark-500">Detection 84% • MTTR 18s • Coverage 72%</div>
              </div>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-2 text-xs text-dark-500">
            <span>Trusted for AppSec at</span>
            <span className="px-2 py-1 rounded border bg-white dark:bg-dark-900">FinTech Co</span>
            <span className="px-2 py-1 rounded border bg-white dark:bg-dark-900">Health SaaS</span>
            <span className="px-2 py-1 rounded border bg-white dark:bg-dark-900">E-commerce</span>
            <span className="px-2 py-1 rounded border bg-white dark:bg-dark-900">Enterprise</span>
          </div>
        </div>
      </section>

      <section id="features" className="py-16 sm:py-20 px-4 bg-white dark:bg-dark-950 border-t border-dark-100 dark:border-dark-800">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-2xl">
            <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-dark-900 dark:text-white">Continuous loop, not point-in-time</h2>
            <p className="mt-3 text-dark-600 dark:text-dark-300">Orchestrator → Red Team ↔ Detection Engine → Sandbox → Knowledge Graph → Posture. Web App → Request → Vulnerability → Attack → Detection → Response → Re-test.</p>
          </div>
          <div className="mt-10 grid md:grid-cols-3 gap-6">
            <FeatureCard
              icon={<Zap className="h-5 w-5" />}
              title="Continuous Red Team"
              description="Web Recon + Vuln ID → Auth/IDOR, Business Logic, Injection, SSRF. Mapped to OWASP Top 10 and MITRE ATT&CK."
              items={["OWASP A01-A10", "2 agents", "Reproducible sandbox"]}
            />
            <FeatureCard
              icon={<Brain className="h-5 w-5" />}
              title="AI Detection Engine"
              description="Log/request/pattern analysis + autonomous hardening (headers, rate limit, ACL fixes). No human in the loop."
              items={["≥85% detection", "MTTR <60s", "Auto response"]}
            />
            <FeatureCard
              icon={<TrendingUp className="h-5 w-5" />}
              title="Adversarial Learning Loop"
              description="Episode transcript memory via RAG (ChromaDB + sentence-transformers) + OWASP/MITRE Knowledge Graph (NetworkX)."
              items={["5–10 episodes to plateau", "Honest learning curve", "Not weight retraining"]}
            />
          </div>
        </div>
      </section>

      <section id="capabilities" className="py-16 px-4 bg-dark-50 dark:bg-dark-900/50 border-y border-dark-100 dark:border-dark-800">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl font-semibold tracking-tight text-dark-900 dark:text-white">Built for CISOs and AppSec</h2>
          <div className="mt-8 grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {capabilities.map((cap) => (
              <CapabilityCard key={cap.title} {...cap} />
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto rounded-2xl border border-dark-200 dark:border-dark-800 bg-white dark:bg-dark-900 p-6 sm:p-8 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-dark-900 dark:text-white">Ready to validate continuously?</h3>
              <p className="text-sm text-dark-600 dark:text-dark-300 mt-1">Local-first, no license cost. Ollama + Docker + Postgres on your hardware.</p>
            </div>
            <div className="flex gap-3">
              <Link href="/auth/register" className="px-5 py-2.5 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700">Start free trial</Link>
              <Link href="/auth/login" className="px-5 py-2.5 rounded-lg border border-dark-200 dark:border-dark-700 bg-white dark:bg-dark-900 text-sm font-medium">Sign in</Link>
            </div>
          </div>
        </div>
      </section>

      <footer className="py-10 px-4 border-t border-dark-100 dark:border-dark-800 bg-white dark:bg-dark-950">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-dark-500">
          <span>© {new Date().getFullYear()} Purple Platform — B2B SaaS • Tiered per-app • Enterprise annual</span>
          <span className="flex items-center gap-2"><Lock className="h-4 w-4" /> Isolated Docker • No egress • Full audit logging</span>
        </div>
      </footer>
    </main>
  );
}

function StatMini({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded-lg border border-dark-200 dark:border-dark-800 bg-white dark:bg-dark-900 px-4 py-3 text-left">
      <div className="text-xs font-medium text-dark-500 uppercase tracking-wide">{label}</div>
      <div className="text-lg font-semibold text-dark-900 dark:text-white">{value}</div>
      <div className="text-xs text-dark-500">{sub}</div>
    </div>
  );
}

function FeatureCard({ icon, title, description, items }: { icon: React.ReactNode; title: string; description: string; items: string[] }) {
  return (
    <div className="rounded-xl border border-dark-200 dark:border-dark-800 bg-white dark:bg-dark-900 p-6 shadow-sm">
      <div className="h-9 w-9 rounded-lg bg-primary-50 dark:bg-primary-900/20 border border-primary-100 dark:border-primary-800 flex items-center justify-center text-primary-600">{icon}</div>
      <h3 className="mt-4 text-[15px] font-semibold text-dark-900 dark:text-white">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-dark-600 dark:text-dark-300">{description}</p>
      <ul className="mt-4 space-y-1.5">
        {items.map(i=>(
          <li key={i} className="flex items-center gap-2 text-xs text-dark-600 dark:text-dark-400"><Check className="h-3.5 w-3.5 text-emerald-500"/>{i}</li>
        ))}
      </ul>
    </div>
  );
}

function CapabilityCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl border border-dark-200 dark:border-dark-800 bg-white dark:bg-dark-900 p-5 hover:shadow-sm transition-shadow">
      <h3 className="text-sm font-medium text-dark-900 dark:text-white">{title}</h3>
      <p className="mt-1.5 text-sm leading-6 text-dark-600 dark:text-dark-400">{description}</p>
    </div>
  );
}

const capabilities = [
  { title: 'OWASP Top 10 Coverage', description: 'All 10 categories mapped to MITRE ATT&CK techniques with NetworkX graph.' },
  { title: 'Quantitative Posture Score', description: 'Detection Rate, MTTR, Coverage executives can track and trend.' },
  { title: 'Compliance Automation', description: 'SOC 2, ISO 27001, NIST audit trails auto-generated per episode.' },
  { title: 'Zero Risk to Production', description: 'All attacks run in isolated Docker containers with no egress.' },
  { title: 'Real-time Dashboard', description: 'Attack flow, detection outcome, response taken, score trends.' },
  { title: 'Operator Mobile', description: 'Start/configure experiments, constraints, push notifications.' },
  { title: 'Multi-scenario Support', description: 'IDOR, Injection, Business Logic, SSRF, Broken Auth — 3 required, 5 shipped.' },
  { title: 'Local-First Low Cost', description: 'Ollama, sentence-transformers, ChromaDB, Postgres, Next.js — no license fees.' },
];
