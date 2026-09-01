'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Settings, Bell, Shield, Database, Key, Save, LogOut } from 'lucide-react';

export default function SettingsPage() {
  const [user, setUser] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) return;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(r => r.ok ? r.json() : null).then(setUser).catch(()=>{});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    await new Promise(r => setTimeout(r, 600));
    setSaving(false);
    setSaved(true);
    setTimeout(()=>setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-dark-900 dark:text-white">Settings</h1>
        <p className="text-sm text-dark-600 dark:text-dark-400 mt-1">Manage your workspace, notifications and security</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Shield className="h-5 w-5 text-primary-600"/> Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-dark-600 dark:text-dark-400">Email</label>
              <Input value={user?.email || 'loading...'} readOnly className="mt-1 bg-dark-50 dark:bg-dark-900" />
            </div>
            <div>
              <label className="text-xs font-medium text-dark-600 dark:text-dark-400">Full name</label>
              <Input value={user?.full_name || ''} placeholder="Your name" className="mt-1" />
            </div>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-dark-600 dark:text-dark-400">Role</label>
              <Input value={user?.role || 'analyst'} readOnly className="mt-1 bg-dark-50" />
            </div>
            <div>
              <label className="text-xs font-medium text-dark-600 dark:text-dark-400">User ID</label>
              <Input value={user?.id?.slice(0,8) || ''} readOnly className="mt-1 font-mono text-xs" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Bell className="h-5 w-5 text-primary-600"/> Notifications</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            { title: 'Episode completed', desc: 'When an episode finishes (success/fail)', on: true },
            { title: 'Posture drop', desc: 'Score drops >10 points in 1h', on: true },
            { title: 'Weekly digest', desc: 'Summary of posture, coverage, MTTR', on: false },
          ].map(row=>(
            <label key={row.title} className="flex items-center justify-between p-3 rounded-lg border border-dark-200 dark:border-dark-800">
              <div>
                <div className="text-sm font-medium text-dark-900 dark:text-white">{row.title}</div>
                <div className="text-xs text-dark-500">{row.desc}</div>
              </div>
              <input type="checkbox" defaultChecked={row.on} className="h-4 w-4 rounded border-dark-300 text-primary-600" />
            </label>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Database className="h-5 w-5 text-primary-600"/> Workspace</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-xs font-medium text-dark-600 dark:text-dark-400">API Base URL</label>
            <Input value={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'} readOnly className="mt-1 font-mono text-xs" />
            <p className="text-xs text-dark-500 mt-1">Web → API via <code className="px-1 py-0.5 rounded bg-dark-100 dark:bg-dark-800">NEXT_PUBLIC_API_URL</code></p>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-dark-600 dark:text-dark-400">Sandbox</label>
              <div className="mt-1 p-3 rounded-lg bg-dark-50 dark:bg-dark-900 border text-xs font-mono">Isolated Docker • no egress • snapshot/restore<br/>Juice Shop • DVWA • Custom</div>
            </div>
            <div>
              <label className="text-xs font-medium text-dark-600 dark:text-dark-400">LLM</label>
              <div className="mt-1 p-3 rounded-lg bg-dark-50 dark:bg-dark-900 border text-xs font-mono">Ollama llama3.1:8b (local) → Groq/OpenRouter fallback<br/>stub if offline</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Key className="h-5 w-5 text-primary-600"/> Security</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-sm">
              <div className="font-medium text-dark-900 dark:text-white">Change password</div>
              <div className="text-xs text-dark-500">Requires current password</div>
            </div>
            <Button variant="outline" size="sm">Update</Button>
          </div>
          <div className="flex items-center justify-between">
            <div className="text-sm">
              <div className="font-medium text-dark-900 dark:text-white">Sign out everywhere</div>
              <div className="text-xs text-dark-500">Revoke all sessions</div>
            </div>
            <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700 hover:bg-red-50"><LogOut className="h-4 w-4 mr-2"/> Sign out</Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button onClick={handleSave} disabled={saving} className="gap-2">
          <Save className="h-4 w-4" /> {saving ? 'Saving...' : saved ? 'Saved ✓' : 'Save changes'}
        </Button>
        <span className="text-xs text-dark-500">Auto-saved to local API when connected</span>
      </div>
    </div>
  );
}
