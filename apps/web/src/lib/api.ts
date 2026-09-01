'use client';

export function getApiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
}

export function getAuthHeaders(): Record<string, string> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

export async function apiFetch(path: string, init?: RequestInit) {
  const url = `${getApiUrl()}${path}`;
  const headers = { ...getAuthHeaders(), ...(init?.headers as Record<string, string> || {}) };
  const res = await fetch(url, { ...init, headers });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`${res.status} ${text.slice(0,300)}`);
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res.text();
}

export type PostureSummary = {
  currentScore: number;
  previousScore: number;
  trend: 'improving' | 'stable' | 'degrading' | string;
  detectionRate: number;
  mttrSeconds: number;
  coverageByCategory: Record<string, number>;
  totalEpisodes: number;
  lastCalculatedAt: string | null;
  history: { episode: number; detectionRate: number; mttr: number; overall: number; calculatedAt: string }[];
};

export type EpisodeListItem = {
  id: string;
  project_id: string;
  target_app_id: string;
  scenario: string;
  status: string;
  score?: { overall_score: number } | null;
  started_at?: string | null;
  created_at: string;
  completed_at?: string | null;
};
