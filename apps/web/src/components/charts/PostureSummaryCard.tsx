'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, Target, Clock, BarChart3 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { getScoreColor, getScoreBgColor } from '@/lib/utils';

interface PostureSummaryCardProps {
  data: {
    currentScore: number;
    previousScore?: number;
    trend: 'improving' | 'stable' | 'declining';
    detectionRate: number;
    mttrSeconds: number;
    coverageByCategory: Record<string, number>;
    totalEpisodes: number;
    lastCalculatedAt: string;
  };
}

export function PostureSummaryCard({ data }: PostureSummaryCardProps) {
  const TrendIcon = data.trend === 'improving' ? TrendingUp : data.trend === 'declining' ? TrendingDown : Minus;
  const trendColor = data.trend === 'improving' ? 'text-green-600' : data.trend === 'declining' ? 'text-red-600' : 'text-gray-600';
  const trendBg = data.trend === 'improving' ? 'bg-green-100' : data.trend === 'declining' ? 'bg-red-100' : 'bg-gray-100';
  
  const [mounted, setMounted] = useState(false);
  const [formattedTime, setFormattedTime] = useState('');

  useEffect(() => {
    setMounted(true);
    setFormattedTime(new Date(data.lastCalculatedAt).toLocaleTimeString());
  }, [data.lastCalculatedAt]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Security Posture Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="md:col-span-2">
            <div className="flex items-center justify-between">
              <div className={`p-4 rounded-xl ${getScoreBgColor(data.currentScore)}`}>
                <p className="text-sm text-dark-600 dark:text-dark-400">Overall Score</p>
                <p className={`text-5xl font-bold ${getScoreColor(data.currentScore)}`}>{data.currentScore}</p>
                <p className="text-xs text-dark-500 mt-1">Out of 100</p>
              </div>
              <div className="ml-4">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${trendBg} dark:bg-opacity-20`}>
                  <TrendIcon className={`h-4 w-4 ${trendColor}`} />
                  <span className={`text-sm font-medium ${trendColor}`}>
                    {data.trend === 'improving' ? `+${data.previousScore ? data.currentScore - data.previousScore : 0}` :
                     data.trend === 'declining' ? `${data.previousScore ? data.currentScore - data.previousScore : 0}` : 'No change'}
                    vs last episode
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-6">
              <MetricBox
                label="Detection Rate"
                value={`${(data.detectionRate * 100).toFixed(1)}%`}
                icon={<Target className="h-5 w-5 text-primary-600" />}
              />
              <MetricBox
                label="Avg MTTR"
                value={`${data.mttrSeconds}s`}
                icon={<Clock className="h-5 w-5 text-primary-600" />}
              />
            </div>
          </div>

          <div className="md:col-span-1 space-y-4">
            <MetricBox
              label="Total Episodes"
              value={data.totalEpisodes.toString()}
              icon={<BarChart3 className="h-5 w-5 text-primary-600" />}
            />
            <MetricBox
              label="Last Updated"
              value={mounted ? formattedTime : '...'}
              icon={<Clock className="h-5 w-5 text-primary-600" />}
            />
          </div>

          <div className="md:col-span-1">
            <div className="bg-dark-50 dark:bg-dark-900 rounded-lg p-4">
              <p className="text-sm text-dark-600 dark:text-dark-400 mb-3">Category Coverage</p>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {Object.entries(data.coverageByCategory)
                  .sort(([, a], [, b]) => a - b)
                  .map(([category, coverage]) => (
                    <CoverageBar key={category} category={category} coverage={coverage} />
                  ))}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function MetricBox({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="bg-dark-50 dark:bg-dark-900 rounded-lg p-4 border border-dark-100 dark:border-dark-800">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-dark-900 dark:text-white mt-1">{value}</p>
        </div>
        <div className="h-10 w-10 rounded-lg bg-white dark:bg-dark-800 border border-dark-100 dark:border-dark-700 flex items-center justify-center shadow-sm">
          {icon}
        </div>
      </div>
    </div>
  );
}

function CoverageBar({ category, coverage }: { category: string; coverage: number }) {
  const getColor = (c: number) => c >= 0.7 ? 'bg-green-500' : c >= 0.4 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium text-dark-700 dark:text-dark-300">{category}</span>
        <span className="text-dark-500 dark:text-dark-400">{(coverage * 100).toFixed(0)}%</span>
      </div>
      <div className="h-2 bg-dark-200 dark:bg-dark-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getColor(coverage)}`}
          style={{ width: `${coverage * 100}%` }}
        />
      </div>
    </div>
  );
}