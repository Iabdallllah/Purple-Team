'use client';

import { Plus, FolderGit2, Search, Filter } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { formatRelativeTime, getStatusColor } from '@/lib/utils';
import Link from 'next/link';

const mockProjects = [
  { id: '1', name: 'E-commerce Platform', description: 'Main customer-facing application', owner: 'Security Team', status: 'active', targetCount: 3, episodeCount: 47, updatedAt: new Date(Date.now() - 86400000).toISOString() },
  { id: '2', name: 'Payment Gateway', description: 'PCI-DSS compliant payment processing', owner: 'Finance Security', status: 'active', targetCount: 2, episodeCount: 23, updatedAt: new Date(Date.now() - 172800000).toISOString() },
  { id: '3', name: 'Admin Dashboard', description: 'Internal administration panel', owner: 'IT Security', status: 'paused', targetCount: 1, episodeCount: 12, updatedAt: new Date(Date.now() - 259200000).toISOString() },
  { id: '4', name: 'Mobile API', description: 'REST API for mobile applications', owner: 'Mobile Team', status: 'active', targetCount: 2, episodeCount: 31, updatedAt: new Date(Date.now() - 43200000).toISOString() },
  { id: '5', name: 'Legacy Portal', description: 'Deprecated customer portal', owner: 'Legacy Team', status: 'archived', targetCount: 1, episodeCount: 5, updatedAt: new Date(Date.now() - 604800000).toISOString() },
];

export default function ProjectsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Projects</h1>
          <p className="text-dark-600 dark:text-dark-400">Manage your security testing projects</p>
        </div>
        <Button className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          New Project
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle>All Projects ({mockProjects.length})</CardTitle>
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
                {mockProjects.map((project) => (
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
                    <td className="py-4 px-4 text-dark-500 dark:text-dark-400 text-sm">{formatRelativeTime(project.updatedAt)}</td>
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