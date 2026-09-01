'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { getStatusColor } from '@/lib/utils';
import { RelativeTime } from '@/components/ui/RelativeTime';
import { ExternalLink, ChevronRight, AlertCircle, CheckCircle, Loader2, XCircle } from 'lucide-react';

interface Episode {
  id: string;
  project: string;
  target: string;
  scenario: string;
  status: 'pending' | 'initializing' | 'running' | 'completed' | 'failed' | 'cancelled';
  score: number | null;
  startedAt: string;
}

interface RecentEpisodesTableProps {
  episodes: Episode[];
}

export function RecentEpisodesTable({ episodes }: RecentEpisodesTableProps) {
  const scenarioLabels: Record<string, string> = {
    idor: 'IDOR/Auth',
    injection: 'Injection',
    business_logic: 'Biz Logic',
    ssrf: 'SSRF',
    broken_auth: 'Broken Auth',
  };

  const statusIcons = {
    completed: CheckCircle,
    running: Loader2,
    failed: XCircle,
    pending: AlertCircle,
    initializing: Loader2,
    cancelled: XCircle,
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Episodes</CardTitle>
        <a href="/dashboard/episodes" className="text-sm text-primary-600 hover:underline flex items-center gap-1">
          View All <ChevronRight className="h-4 w-4" />
        </a>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-200 dark:border-dark-700">
                <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Project</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Target</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Scenario</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Status</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Score</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Started</th>
                <th className="text-right py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-100 dark:divide-dark-800">
              {episodes.map((episode) => {
                const StatusIcon = statusIcons[episode.status];
                const isRunning = episode.status === 'running' || episode.status === 'initializing';

                return (
                  <tr key={episode.id} className="hover:bg-dark-50 dark:hover:bg-dark-900/50 transition-colors">
                    <td className="py-4 px-4">
                      <div className="font-medium text-dark-900 dark:text-white">{episode.project}</div>
                    </td>
                    <td className="py-4 px-4 text-dark-600 dark:text-dark-300">{episode.target}</td>
                    <td className="py-4 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
                        {scenarioLabels[episode.scenario] || episode.scenario}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(episode.status)}`}>
                        <StatusIcon className={`h-3 w-3 ${isRunning ? 'animate-spin' : ''}`} />
                        {episode.status}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      {episode.score !== null ? (
                        <span className="font-mono font-medium text-dark-900 dark:text-white">{episode.score}</span>
                      ) : (
                        <span className="text-dark-400 dark:text-dark-500">—</span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-dark-600 dark:text-dark-400 text-sm">
                      <RelativeTime date={episode.startedAt} />
                    </td>
                    <td className="py-4 px-4 text-right">
                      <a href={`/dashboard/episodes/${episode.id}`} className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 flex items-center justify-end gap-1">
                        Details <ExternalLink className="h-3 w-3" />
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}