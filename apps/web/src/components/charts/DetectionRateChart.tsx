'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area } from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const mockDetectionData = [
  { episode: 1, detectionRate: 0.45, mttr: 120 },
  { episode: 2, detectionRate: 0.52, mttr: 95 },
  { episode: 3, detectionRate: 0.58, mttr: 85 },
  { episode: 4, detectionRate: 0.63, mttr: 72 },
  { episode: 5, detectionRate: 0.71, mttr: 65 },
  { episode: 6, detectionRate: 0.74, mttr: 58 },
  { episode: 7, detectionRate: 0.78, mttr: 52 },
  { episode: 8, detectionRate: 0.82, mttr: 45 },
  { episode: 9, detectionRate: 0.81, mttr: 48 },
  { episode: 10, detectionRate: 0.83, mttr: 42 },
];

export function DetectionRateChart({ data }: { data?: { episode: number; detectionRate: number; mttr: number }[] }) {
  const chartData = data && data.length ? data : mockDetectionData;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Learning Curve</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <defs>
                <linearGradient id="detectionGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="episode"
                tick={{ fill: '#64748b', fontSize: 12 }}
                axisLine={{ stroke: '#e2e8f0' }}
                label={{ value: 'Episode', position: 'insideBottom', offset: -10, fill: '#64748b' }}
              />
              <YAxis
                domain={[0, 1]}
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                tick={{ fill: '#64748b', fontSize: 12 }}
                axisLine={{ stroke: '#e2e8f0' }}
                label={{ value: 'Detection Rate', angle: -90, position: 'insideLeft', offset: 10, fill: '#64748b' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: 'none',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                }}
                labelStyle={{ color: '#f1f5f9' }}
                itemStyle={{ color: '#f1f5f9' }}
                formatter={(value: number) => [(value * 100).toFixed(1) + '%', 'Detection Rate']}
              />
              <Area
                type="monotone"
                dataKey="detectionRate"
                stroke="#8b5cf6"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#detectionGradient)"
                dot={{ r: 4, strokeWidth: 2, stroke: '#8b5cf6', fill: '#fff' }}
                activeDot={{ r: 6, strokeWidth: 2, stroke: '#8b5cf6', fill: '#fff' }}
              />
              <Line
                type="monotone"
                dataKey="mttr"
                yAxisId="right"
                stroke="#f59e0b"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                domain={[0, 150]}
                tickFormatter={(v) => `${v}s`}
                tick={{ fill: '#64748b', fontSize: 12 }}
                axisLine={{ stroke: '#e2e8f0' }}
                label={{ value: 'MTTR (seconds)', angle: 90, position: 'insideRight', offset: -10, fill: '#64748b' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-6 mt-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-primary-500 rounded" />
            <span className="text-dark-600 dark:text-dark-400">Detection Rate</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-2 bg-amber-500 rounded" style={{ borderTop: '2px dashed #f59e0b' }} />
            <span className="text-dark-600 dark:text-dark-400">MTTR (s)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}