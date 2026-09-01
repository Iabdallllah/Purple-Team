'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { getStatusColor, getScoreColor } from '@/lib/utils';
import { RelativeTime } from '@/components/ui/RelativeTime';
import { Shield, Zap, Eye, Wrench, BarChart3, Clock, AlertTriangle } from 'lucide-react';

type EpisodeDetail = {
  id: string; projectId: string; targetAppId: string; scenario: string; status: string;
  constraints: any; startedAt?: string; completedAt?: string; error?: string;
  targetApp?: {id:string; name:string; type:string};
  attacks: {id:string; technique_id:string; owasp_category:string; success:boolean; confidence:number; timestamp:string}[];
  detections: {id:string; attackId?:string; detected:boolean; detectionType:string; confidence:number; timestamp:string}[];
  responses: {id:string; detectionId?:string; actionType:string; success:boolean; timestamp:string}[];
  score?: {detectionRate:number; mttrSeconds:number; coverage:Record<string,{totalTechniques:number;coveredTechniques:number;coverage:number}>; overallScore:number};
};

export default function EpisodeDetailPage(){
  const { id } = useParams() as {id:string};
  const [data, setData] = useState<EpisodeDetail|null>(null);
  const [err, setErr] = useState<string|null>(null);
  useEffect(()=>{
    const token = typeof window!=='undefined'? localStorage.getItem('access_token'):null;
    fetch(`http://localhost:8001/api/v1/episodes/${id}`, {headers: token?{Authorization:`Bearer ${token}`}: {}}).then(async r=>{
      if(!r.ok) throw new Error(`${r.status} ${await r.text()}`);
      return r.json();
    }).then(setData).catch(e=>setErr(String(e)));
  },[id]);
  if(err) return <div className="p-6"><Card className="p-6 border-red-200"><p className="text-red-600">{err}</p><p className="text-sm text-dark-500">Ensure API on :8001 and token set (login at /auth/login)</p></Card></div>;
  if(!data) return <div className="p-6">Loading episode {id}...</div>;
  const dr = data.score?.detectionRate ?? 0;
  const mttr = data.score?.mttrSeconds ?? 0;
  const cov = data.score?.coverage ?? {};
  const overall = data.score?.overallScore ?? null;
  return (
    <div className="space-y-6 p-1">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold dark:text-white">Episode {data.id.slice(0,8)}</h1>
          <p className="text-dark-500">Scenario <span className="font-mono bg-primary-100 dark:bg-primary-900/30 px-2 py-0.5 rounded text-primary-700">{data.scenario}</span> • Target {data.targetApp?.name||data.targetAppId.slice(0,8)} ({data.targetApp?.type})</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(data.status)}`}>{data.status}</span>
      </div>

      <div className="grid md:grid-cols-4 gap-4">
        <Card className="p-4"><div className="flex items-center gap-2 text-dark-500 text-sm"><BarChart3 className="h-4 w-4"/>Overall Score</div><div className={`text-3xl font-bold ${overall!==null?getScoreColor(overall):''}`}>{overall!==null?overall:'—'}</div></Card>
        <Card className="p-4"><div className="flex items-center gap-2 text-dark-500 text-sm"><Eye className="h-4 w-4"/>Detection Rate</div><div className="text-3xl font-bold">{(dr*100).toFixed(1)}%</div></Card>
        <Card className="p-4"><div className="flex items-center gap-2 text-dark-500 text-sm"><Clock className="h-4 w-4"/>MTTR</div><div className="text-3xl font-bold">{mttr}s</div></Card>
        <Card className="p-4"><div className="text-sm text-dark-500">Duration</div><div className="text-lg font-mono">{data.startedAt? <RelativeTime date={data.startedAt}/>: '—'} → {data.completedAt? <RelativeTime date={data.completedAt}/>: data.status}</div>{data.error && <p className="text-xs text-red-500 mt-1 flex gap-1"><AlertTriangle className="h-3 w-3"/>{data.error}</p>}</Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="flex gap-2"><Zap className="h-5 w-5 text-amber-500"/>Attack Flow ({data.attacks.length})</CardTitle></CardHeader>
        <CardContent>
          {data.attacks.length===0? <p className="text-dark-500">No attacks yet</p> :
          <ol className="space-y-2">
            {data.attacks.map((a,i)=>(
              <li key={a.id} className="flex items-center gap-3 p-3 rounded-lg bg-dark-50 dark:bg-dark-900 border">
                <span className="text-xs font-mono bg-dark-200 dark:bg-dark-700 px-2 py-1 rounded">#{i+1}</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${a.success?'bg-red-100 text-red-700':'bg-dark-100'}`}>{a.success?'SUCCESS':'FAILED'}</span>
                <span className="font-mono text-sm">{a.technique_id}</span>
                <span className="text-xs bg-primary-100 px-2 py-0.5 rounded">{a.owasp_category}</span>
                <span className="text-sm ml-auto opacity-70"><RelativeTime date={a.timestamp}/></span>
              </li>
            ))}
          </ol>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="flex gap-2"><Eye className="h-5 w-5 text-blue-500"/>Detection Outcome ({data.detections.length})</CardTitle></CardHeader>
        <CardContent>
          {data.detections.length===0? <p className="text-dark-500">No detections</p> :
          <ul className="space-y-2">
            {data.detections.map(d=>(
              <li key={d.id} className={`p-3 rounded-lg border ${d.detected?'bg-green-50 dark:bg-green-900/20 border-green-200':'bg-dark-50 dark:bg-dark-900'}`}>
                <div className="flex gap-2 items-center"><span className={`px-2 py-0.5 rounded text-xs ${d.detected?'bg-green-600 text-white':'bg-dark-200'}`}>{d.detected?'DETECTED':'MISSED'}</span><span className="font-mono text-sm">{d.detectionType}</span><span className="text-xs ml-auto">conf {(d.confidence*100).toFixed(0)}%</span><span className="text-xs opacity-60"><RelativeTime date={d.timestamp}/></span></div>
              </li>
            ))}
          </ul>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="flex gap-2"><Wrench className="h-5 w-5 text-emerald-500"/>Response Taken ({data.responses.length})</CardTitle></CardHeader>
        <CardContent>
          {data.responses.length===0? <p className="text-dark-500">No responses (or autonomous hardening pending)</p> :
          <ul className="space-y-2">
            {data.responses.map(r=>(
              <li key={r.id} className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-800">
                <div className="flex gap-2 items-center"><span className={`px-2 py-0.5 rounded text-xs ${r.success?'bg-emerald-600 text-white':'bg-red-500 text-white'}`}>{r.success?'APPLIED':'FAILED'}</span><span className="font-mono text-sm">{r.actionType}</span><span className="text-xs opacity-60 ml-auto"><RelativeTime date={r.timestamp}/></span></div>
              </li>
            ))}
          </ul>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="flex gap-2"><Shield className="h-5 w-5 text-primary-600"/>Coverage (MITRE/OWASP)</CardTitle></CardHeader>
        <CardContent>
          {Object.keys(cov).length===0? <p className="text-dark-500">Coverage calculated after scoring</p> :
          <div className="grid grid-cols-5 gap-2">
            {Object.entries(cov).map(([cat, v])=>(
              <div key={cat} className={`p-3 rounded text-center ${ (v.coverage??0)>=0.7?'bg-green-500 text-white': (v.coverage??0)>=0.4?'bg-yellow-400':'bg-red-400'}`}>
                <div className="font-bold">{cat}</div><div className="text-xs">{((v.coverage??0)*100).toFixed(0)}%</div>
              </div>
            ))}
          </div>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Constraints & Raw</CardTitle></CardHeader>
        <CardContent><pre className="text-xs bg-dark-900 text-dark-100 p-4 rounded overflow-auto">{JSON.stringify({constraints:data.constraints, projectId:data.projectId, targetAppId:data.targetAppId}, null, 2)}</pre></CardContent>
      </Card>
    </div>
  );
}
