'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const owaspCategories = [
  { id: 'A01', name: 'Broken Access Control' },
  { id: 'A02', name: 'Cryptographic Failures' },
  { id: 'A03', name: 'Injection' },
  { id: 'A04', name: 'Insecure Design' },
  { id: 'A05', name: 'Security Misconfiguration' },
  { id: 'A06', name: 'Vulnerable Components' },
  { id: 'A07', name: 'Auth Failures' },
  { id: 'A08', name: 'Integrity Failures' },
  { id: 'A09', name: 'Logging Failures' },
  { id: 'A10', name: 'SSRF' },
];

interface CoverageHeatmapProps {
  data: Record<string, number>;
}

export function CoverageHeatmap({ data }: CoverageHeatmapProps) {
  const getColor = (coverage: number) => {
    if (coverage >= 0.8) return 'bg-green-500';
    if (coverage >= 0.6) return 'bg-green-400';
    if (coverage >= 0.4) return 'bg-yellow-400';
    if (coverage >= 0.2) return 'bg-orange-400';
    return 'bg-red-400';
  };

  const getTextColor = (coverage: number) => coverage >= 0.5 ? 'text-white' : 'text-dark-900 dark:text-dark-100';

  return (
    <Card>
      <CardHeader>
        <CardTitle>MITRE ATT&CK Coverage</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {owaspCategories.map((cat) => {
            const coverage = data[cat.id] || 0;
            return (
              <div
                key={cat.id}
                className={`relative aspect-square rounded-lg p-4 text-center ${getColor(coverage)} ${getTextColor(coverage)}`}
                title={`${cat.id}: ${cat.name} - ${(coverage * 100).toFixed(0)}%`}
              >
                <div className="text-2xl font-bold">{cat.id}</div>
                <div className="text-xs opacity-90 mt-1 truncate">{cat.name}</div>
                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs font-medium">
                  {(coverage * 100).toFixed(0)}%
                </div>
              </div>
            );
          })}
        </div>
        <div className="mt-4 flex items-center justify-center gap-4 text-xs text-dark-600 dark:text-dark-400">
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 bg-red-400 rounded" />
            <span>0-20%</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 bg-orange-400 rounded" />
            <span>20-40%</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 bg-yellow-400 rounded" />
            <span>40-60%</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 bg-green-400 rounded" />
            <span>60-80%</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 bg-green-500 rounded" />
            <span>80-100%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}