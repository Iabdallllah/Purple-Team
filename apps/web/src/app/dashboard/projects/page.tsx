'use client';

import { useState, useEffect } from 'react';
import { Plus, Search, Filter, X, Loader2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { getStatusColor } from '@/lib/utils';
import { RelativeTime } from '@/components/ui/RelativeTime';
import Link from 'next/link';

const mockProjects = [
  { id: '1', name: 'E-commerce Platform', description: 'Main customer-facing application', owner: 'Security Team', status: 'active', targetCount: 3, episodeCount: 47, updatedAt: new Date(Date.now() - 86400000).toISOString() },
  { id: '2', name: 'Payment Gateway', description: 'PCI-DSS compliant payment processing', owner: 'Finance Security', status: 'active', targetCount: 2, episodeCount: 23, updatedAt: new Date(Date.now() - 172800000).toISOString() },
  { id: '3', name: 'Admin Dashboard', description: 'Internal administration panel', owner: 'IT Security', status: 'paused', targetCount: 1, episodeCount: 12, updatedAt: new Date(Date.now() - 172800000).toISOString() },
  { id: '4', name: 'Mobile API', description: 'REST API for mobile applications', owner: 'Mobile Team', status: 'active', targetCount: 2, episodeCount: 31, updatedAt: new Date(Date.now() - 43200000).toISOString() },
  { id: '5', name: 'Legacy Portal', description: 'Deprecated customer portal', owner: 'Legacy Team', status: 'archived', targetCount: 1, episodeCount: 5, updatedAt: new Date(Date.now() - 604800000).toISOString() },
];

export default function ProjectsPage() {
  const [projects, setProjects] = useState(mockProjects);
  const [showNew, setShowNew] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) return;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.items?.length) {
          setProjects(data.items.map((p: any) => ({
            id: p.id,
            name: p.name,
            description: p.description || '',
            owner: 'You',
            status: p.status,
            targetCount: 0,
            episodeCount: 0,
            updatedAt: p.updated_at || p.created_at,
          })));
        }
      })
      .catch(() => {});
  }, []);

  const handleCreate = async () => {
    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) throw new Error('Not authenticated — please sign in');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ name: name.trim(), description: description.trim() || undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to create project');
      setProjects(prev => [{
        id: data.id,
        name: data.name,
        description: data.description || '',
        owner: 'You',
        status: data.status,
        targetCount: 0,
        episodeCount: 0,
        updatedAt: data.updated_at || new Date().toISOString(),
      }, ...prev]);
      setName('');
      setDescription('');
      setShowNew(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create project');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-dark-900 dark:text-white">Projects</h1>
          <p className="text-sm text-dark-600 dark:text-dark-400 mt-1">Manage your security testing projects — per-application SaaS (Enterprise annual)</p>
        </div>
        <Button onClick={() => setShowNew(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          New Project
        </Button>
      </div>

      {showNew && (
        <Card className="border-primary-200 dark:border-primary-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">New Project</CardTitle>
              <button onClick={() => setShowNew(false)} className="p-1 rounded hover:bg-dark-100 dark:hover:bg-dark-800">
                <X className="h-4 w-4" />
              </button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">{error}</div>}
            <div>
              <label className="text-xs font-medium text-dark-600 dark:text-dark-400">Name *</label>
              <Input value={name} onChange={e => setName(e.target.value)} placeholder="E.g. Web App — Production" className="mt-1" />
            </div>
            <div>
              <label className="text-xs font-medium text-dark-600 dark:text-dark-400">Description</label>
              <Input value={description} onChange={e => setDescription(e.target.value)} placeholder="What app will be tested?" className="mt-1" />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={saving} className="gap-2">
                {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                Create project
              </Button>
              <Button variant="ghost" onClick={() => setShowNew(false)}>Cancel</Button>
            </div>
            <p className="text-xs text-dark-500">Creates via <code className="px-1 py-0.5 rounded bg-dark-100 dark:bg-dark-800">POST /api/v1/projects</code> with JWT.</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle>All Projects ({projects.length})</CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-dark-400" />
                <Input placeholder="Search projects..." className="pl-10 w-64" />
              </div>
              <Button variant="ghost">
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-dark-200 dark:border-dark-700">
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Project</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Owner</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Status</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Targets</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Episodes</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Last Activity</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-100 dark:divide-dark-800">
                {projects.map((project) => (
                  <tr key={project.id} className="hover:bg-dark-50 dark:hover:bg-dark-900/50">
                    <td className="py-4 px-4">
                      <Link href={`/dashboard/projects/${project.id}`} className="font-medium text-dark-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400">
                        {project.name}
                      </Link>
                      <p className="text-sm text-dark-500 dark:text-dark-400 truncate max-w-xs">{project.description}</p>
                    </td>
                    <td className="py-4 px-4 text-dark-600 dark:text-dark-300">{project.owner}</td>
                    <td className="py-4 px-4">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                        {project.status}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-dark-600 dark:text-dark-300">{project.targetCount}</td>
                    <td className="py-4 px-4 text-dark-600 dark:text-dark-300">{project.episodeCount}</td>
                    <td className="py-4 px-4 text-dark-500 dark:text-dark-400 text-sm"><RelativeTime date={project.updatedAt} /></td>
                    <td className="py-4 px-4 text-right">
                      <Link href={`/dashboard/projects/${project.id}`} className="text-primary-600 hover:text-primary-700">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}