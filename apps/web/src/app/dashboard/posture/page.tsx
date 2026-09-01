'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { PostureSummaryCard } from '@/components/charts/PostureSummaryCard';
import { DetectionRateChart } from '@/components/charts/DetectionRateChart';
import { CoverageHeatmap } from '@/components/charts/CoverageHeatmap';
import { TrendingUp, Shield, Activity, Clock } from 'lucide-react';

const mockPosture = {
  currentScore: 73,
  previousScore: 68,
  trend: 'improving' as const,
  detectionRate: 0.82,
  mttrSeconds: 45,
  coverageByCategory: {
    'A01': 0.75, 'A02': 0.60, 'A03': 0.85, 'A04': 0.45, 'A05': 0.70,
    'A06': 0.55, 'A07': 0.80, 'A08': 0.50, 'A09': 0.65, 'A10': 0.40,
  },
  totalEpisodes: 47,
  lastCalculatedAt: new Date().toISOString(),
};

const kpis = [
  { label: 'Detection Rate', value: '82%', target: '≥85%', status: 'warning' as const, desc: 'Known scenarios' },
  { label: 'Avg Episode', value: '4.2 min', target: '≤30 min', status: 'success' as const, desc: 'Per scenario' },
  { label: 'MTTR', value: '45s', target: '<60s', status: 'success' as const, desc: 'Mean time to respond' },
  { label: 'Coverage', value: '64%', target: '→85%', status: 'warning' as const, desc: 'OWASP/MITRE' },
];

export default function PosturePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-dark-900 dark:text-white">Security Posture</h1>
        <p className="text-sm text-dark-600 dark:text-dark-400 mt-1">Quantitative metrics executives can track — Detection Rate, MTTR, Coverage (per proposal KPIs)</p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map(k => (
          <Card key={k.label} className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-dark-500 uppercase tracking-wide">{k.label}</p>
                <p className="text-2xl font-bold text-dark-900 dark:text-white mt-2">{k.value}</p>
                <p className={`text-xs mt-2 font-medium ${k.status === 'success' ? 'text-emerald-600' : k.status === 'warning' ? 'text-amber-600' : 'text-red-600'}`}>{k.target} • {k.desc}</p>
              </div>
              <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${k.status === 'success' ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'}`}>
                {k.label.includes('Detection') ? <Activity className="h-5 w-5" /> : k.label.includes('MTTR') ? <Clock className="h-5 w-5" /> : <Shield className="h-5 w-5" />}
              </div>
            </div>
          </Card>
        ))}
      </div>

      <PostureSummaryCard data={mockPosture} />

      <div className="grid lg:grid-cols-2 gap-6">
        <DetectionRateChart />
        <CoverageHeatmap data={mockPosture.coverageByCategory} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><TrendingUp className="h-5 w-5 text-primary-600" /> Learning Curve (5–10 episodes → plateau expected)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg bg-dark-50 dark:bg-dark-900 border border-dark-200 dark:border-dark-800 p-4">
            <div className="flex items-end gap-1 h-24">
              {[45,52,58,63,71,74,78,82,81,83,82,83].map((v,i)=>(
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full bg-primary-600 rounded-t" style={{height: `${v}%`}} title={`#${i+1}: ${v}`} />
                  <span className="text-[10px] text-dark-500">#{i+1}</span>
                </div>
              ))}
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-dark-500">
              <span>Episode 1 → 12</span>
              <span className="text-emerald-600 font-medium">+83% plateau after #8 (per proposal: diminishing returns)</span>
            </div>
          </div>
          <p className="text-xs text-dark-500 mt-3">Measurable gain across first 5–10 episodes, documented plateau after — report honestly, not unlimited linear gain (per proposal Risks).</p>
        </CardContent>
      </Card>
    </div>
  );
}
