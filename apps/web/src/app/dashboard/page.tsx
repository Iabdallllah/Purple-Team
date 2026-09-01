'use client';

import { Shield, Clock, Target, Activity } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { PostureSummaryCard } from '@/components/charts/PostureSummaryCard';
import { RecentEpisodesTable } from '@/components/episodes/RecentEpisodesTable';
import { DetectionRateChart } from '@/components/charts/DetectionRateChart';
import { CoverageHeatmap } from '@/components/charts/CoverageHeatmap';

const mockPostureSummary = {
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

const mockStats = [
  { label: 'Total Episodes', value: '147', change: '+12%', icon: Activity, color: 'text-blue-600', bg: 'bg-blue-100' },
  { label: 'Detection Rate', value: '82%', change: '+5%', icon: Target, color: 'text-emerald-600', bg: 'bg-emerald-100' },
  { label: 'Avg MTTR', value: '45s', change: '-8s', icon: Clock, color: 'text-amber-600', bg: 'bg-amber-100' },
  { label: 'Coverage', value: '64%', change: '+3%', icon: Shield, color: 'text-violet-600', bg: 'bg-violet-100' },
];

const mockRecentEpisodes = [
  { id: '1', project: 'E-commerce API', target: 'Juice Shop', scenario: 'idor', status: 'completed' as const, score: 78, startedAt: new Date(Date.now() - 3600000).toISOString() },
  { id: '2', project: 'Payment Service', target: 'Custom App', scenario: 'injection', status: 'completed' as const, score: 65, startedAt: new Date(Date.now() - 7200000).toISOString() },
  { id: '3', project: 'User Portal', target: 'DVWA', scenario: 'business_logic', status: 'running' as const, score: null, startedAt: new Date(Date.now() - 1800000).toISOString() },
  { id: '4', project: 'Admin Panel', target: 'Juice Shop', scenario: 'ssrf', status: 'completed' as const, score: 82, startedAt: new Date(Date.now() - 10800000).toISOString() },
  { id: '5', project: 'Auth Service', target: 'Custom App', scenario: 'broken_auth', status: 'failed' as const, score: 34, startedAt: new Date(Date.now() - 14400000).toISOString() },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-dark-900 dark:text-white">Dashboard</h1>
          <p className="text-sm text-dark-600 dark:text-dark-400 mt-1">Real-time security posture overview</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          Live
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {mockStats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <PostureSummaryCard data={mockPostureSummary} />
          <DetectionRateChart />
        </div>
        <div className="space-y-6">
          <CoverageHeatmap data={mockPostureSummary.coverageByCategory} />
          <RecentEpisodesTable episodes={mockRecentEpisodes} />
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, change, icon: Icon, color, bg }: { label: string; value: string; change: string; icon: React.ComponentType<{ className?: string }>; color: string; bg: string }) {
  return (
    <Card className="p-5 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-dark-900 dark:text-white mt-2">{value}</p>
          <p className="text-xs font-medium text-emerald-600 dark:text-emerald-400 mt-2 flex items-center gap-1">
            <span className="inline-block h-1 w-1 rounded-full bg-emerald-500" />
            {change} vs last week
          </p>
        </div>
        <div className={`h-10 w-10 rounded-lg ${bg} dark:bg-opacity-20 flex items-center justify-center border border-dark-100 dark:border-dark-800`}>
          <Icon className={`h-5 w-5 ${color}`} />
        </div>
      </div>
    </Card>
  );
}
