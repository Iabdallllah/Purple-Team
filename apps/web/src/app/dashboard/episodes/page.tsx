'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Search, Filter, Play, Clock, AlertCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { getStatusColor } from '@/lib/utils';
import { RelativeTime } from '@/components/ui/RelativeTime';

interface Episode {
  id: string;
  project: string;
  target: string;
  scenario: string;
  status: 'pending' | 'initializing' | 'running' | 'completed' | 'failed' | 'cancelled';
  score: number | null;
  startedAt: string;
  duration?: string;
}

const mockEpisodes: Episode[] = [
  { id: '1', project: 'E-commerce API', target: 'Juice Shop', scenario: 'idor', status: 'completed', score: 78, startedAt: new Date(Date.now() - 3600000).toISOString(), duration: '2m 15s' },
  { id: '2', project: 'Payment Service', target: 'Custom App', scenario: 'injection', status: 'completed', score: 65, startedAt: new Date(Date.now() - 7200000).toISOString(), duration: '4m 32s' },
  { id: '3', project: 'User Portal', target: 'DVWA', scenario: 'business_logic', status: 'running', score: null, startedAt: new Date(Date.now() - 1800000).toISOString(), duration: '1m 45s' },
  { id: '4', project: 'Admin Panel', target: 'Juice Shop', scenario: 'ssrf', status: 'completed', score: 82, startedAt: new Date(Date.now() - 10800000).toISOString(), duration: '3m 08s' },
  { id: '5', project: 'Auth Service', target: 'Custom App', scenario: 'broken_auth', status: 'failed', score: 34, startedAt: new Date(Date.now() - 14400000).toISOString(), duration: '0m 52s' },
  { id: '6', project: 'E-commerce API', target: 'Juice Shop', scenario: 'injection', status: 'pending', score: null, startedAt: new Date(Date.now() - 900000).toISOString(), duration: '-' },
];

const scenarioLabels: Record<string, string> = {
  idor: 'IDOR',
  injection: 'Injection',
  business_logic: 'Business Logic',
  ssrf: 'SSRF',
  broken_auth: 'Broken Auth',
};

const scenarioColors: Record<string, string> = {
  idor: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  injection: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  business_logic: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  ssrf: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  broken_auth: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300',
};

export default function EpisodesPage() {
  const [episodes, setEpisodes] = useState<Episode[]>(mockEpisodes);
  const [filter, setFilter] = useState<string>('all');
  const [search, setSearch] = useState('');

  // In production, fetch from API
  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) return;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/episodes`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.items?.length) {
          setEpisodes(data.items.map((e: any) => ({
            id: e.id,
            project: e.project_id?.slice(0, 8) || 'Project',
            target: e.target_app_id?.slice(0, 8) || 'Target',
            scenario: e.scenario,
            status: e.status,
            score: e.score?.overall_score ?? null,
            startedAt: e.started_at || e.created_at,
            duration: e.completed_at && e.started_at ? `${Math.round((new Date(e.completed_at).getTime() - new Date(e.started_at).getTime())/1000)}s` : '-',
          })));
        }
      })
      .catch(() => {});
  }, []);

  const filtered = episodes.filter(e => {
    if (filter !== 'all' && e.status !== filter) return false;
    if (search && !`${e.project} ${e.target} ${e.scenario}`.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-dark-900 dark:text-white">Episodes</h1>
          <p className="text-sm text-dark-600 dark:text-dark-400 mt-1">All attack/defense runs — attack flow, detection outcome, response taken</p>
        </div>
        <Link href="/dashboard" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 shadow-sm">
          <Play className="h-4 w-4" /> New Episode
        </Link>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <CardTitle>All Episodes ({filtered.length})</CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-dark-400" />
                <Input placeholder="Search episodes..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10 w-64 h-9" />
              </div>
              <select value={filter} onChange={e => setFilter(e.target.value)} className="h-9 rounded-lg border border-dark-200 dark:border-dark-700 bg-white dark:bg-dark-900 px-3 text-sm">
                <option value="all">All status</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto -mx-6 px-6">
            <table className="w-full">
              <thead>
                <tr className="border-b border-dark-200 dark:border-dark-700">
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wide">Episode</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wide">Scenario</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wide">Status</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wide">Score</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wide">Duration</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wide">Started</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wide"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-100 dark:divide-dark-800">
                {filtered.map(ep => (
                  <tr key={ep.id} className="hover:bg-dark-50 dark:hover:bg-dark-900/50 transition-colors group">
                    <td className="py-4 px-4">
                      <div className="font-medium text-dark-900 dark:text-white font-mono text-sm">{ep.id.slice(0, 8)}</div>
                      <div className="text-xs text-dark-500">{ep.project} • {ep.target}</div>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${scenarioColors[ep.scenario] || 'bg-dark-100'}`}>
                        {scenarioLabels[ep.scenario] || ep.scenario}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(ep.status)}`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${ep.status === 'running' ? 'bg-blue-500 animate-pulse' : ep.status === 'completed' ? 'bg-emerald-500' : ep.status === 'failed' ? 'bg-red-500' : 'bg-amber-500'}`} />
                        {ep.status}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      {ep.score !== null ? (
                        <span className="inline-flex items-center gap-1 font-mono text-sm font-medium">
                          <span className={ep.score >= 70 ? 'text-emerald-600' : ep.score >= 40 ? 'text-amber-600' : 'text-red-600'}>{ep.score}</span>
                          <span className="text-dark-400 text-xs">/100</span>
                        </span>
                      ) : <span className="text-dark-400">—</span>}
                    </td>
                    <td className="py-4 px-4 text-sm text-dark-600 dark:text-dark-400 font-mono">{ep.duration}</td>
                    <td className="py-4 px-4 text-sm text-dark-500"><RelativeTime date={ep.startedAt} /></td>
                    <td className="py-4 px-4 text-right">
                      <Link href={`/dashboard/episodes/${ep.id}`} className="text-sm font-medium text-primary-600 hover:text-primary-700 opacity-0 group-hover:opacity-100 transition-opacity">
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="py-12 text-center">
                <Clock className="h-8 w-8 mx-auto text-dark-300 mb-3" />
                <p className="text-sm text-dark-500">No episodes match your filters</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
