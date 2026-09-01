import { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert, ActivityIndicator, TextInput } from 'react-native';
import { useRouter } from 'expo-router';
import { api } from '@/lib/api';

const SCENARIOS = [
  { id: 'idor', label: 'IDOR / Auth Abuse (A01/A07)', desc: 'Horizontal/vertical IDOR, BOLA' },
  { id: 'injection', label: 'Injection (A03)', desc: 'SQL/NoSQL/Command/LDAP/XSS' },
  { id: 'business_logic', label: 'Business Logic (A04)', desc: 'Race, price manipulation, workflow bypass' },
  { id: 'ssrf', label: 'SSRF (A10)', desc: 'Cloud metadata, port scan, file scheme' },
  { id: 'broken_auth', label: 'Broken Auth (A07)', desc: 'JWT, credential stuffing, session fixation' },
];

export default function NewEpisodeScreen(){
  const router=useRouter();
  const [projects,setProjects]=useState<any[]>([]);
  const [targets,setTargets]=useState<any[]>([]);
  const [projectId,setProjectId]=useState<string>('');
  const [targetId,setTargetId]=useState<string>('');
  const [scenario,setScenario]=useState('idor');
  const [maxDuration,setMaxDuration]=useState('30');
  const [safety,setSafety]=useState<'passive'|'active'|'aggressive'>('active');
  const [loading,setLoading]=useState(false);

  useEffect(()=>{ api.getProjects().then(r=>{ setProjects(r.items||[]); if(r.items?.[0]) setProjectId(r.items[0].id); }).catch(()=>{}); },[]);
  useEffect(()=>{
    if(!projectId) return;
    api.getTargets(projectId).then(r=>{ setTargets(r.items||[]); if(r.items?.[0]) setTargetId(r.items[0].id); }).catch(()=>setTargets([]));
  },[projectId]);

  const start = async()=>{
    if(!projectId||!targetId) return Alert.alert('Error','Select project & target');
    setLoading(true);
    try{
      const ep=await api.createEpisode({
        project_id: projectId,
        target_app_id: targetId,
        scenario,
        constraints: { max_duration_minutes: parseInt(maxDuration)||30, safety_level: safety, max_iterations: 10 }
      });
      Alert.alert('Episode started', `ID ${String(ep.id).slice(0,8)} — tracking in real-time`, [{text:'View', onPress:()=>router.replace('/dashboard/episodes')}]);
      router.push('/dashboard/episodes');
    }catch(e:any){ Alert.alert('Failed', e.message); } finally{ setLoading(false); }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Start Experiment</Text>
      <Text style={styles.subtitle}>Define scenario + constraints (operator interface)</Text>

      <Text style={styles.label}>Project</Text>
      <View style={styles.pickerBox}>
        {projects.length===0? <Text style={styles.hint}>Create a project first (web dashboard)</Text> : projects.map(p=>(
          <TouchableOpacity key={p.id} onPress={()=>setProjectId(p.id)} style={[styles.opt, projectId===p.id && styles.optActive]}><Text style={styles.optText}>{p.name}</Text></TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Target App</Text>
      <View style={styles.pickerBox}>
        {targets.length===0? <Text style={styles.hint}>No targets for project</Text> : targets.map(t=>(
          <TouchableOpacity key={t.id} onPress={()=>setTargetId(t.id)} style={[styles.opt, targetId===t.id && styles.optActive]}><Text style={styles.optText}>{t.name} ({t.type})</Text></TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Scenario</Text>
      {SCENARIOS.map(s=>(
        <TouchableOpacity key={s.id} onPress={()=>setScenario(s.id)} style={[styles.card, scenario===s.id && styles.cardActive]}>
          <Text style={styles.cardTitle}>{s.label}</Text><Text style={styles.cardDesc}>{s.desc}</Text>
        </TouchableOpacity>
      ))}

      <Text style={styles.label}>Max duration (minutes, ≤30 per KPI)</Text>
      <TextInput value={maxDuration} onChangeText={setMaxDuration} keyboardType="number-pad" style={styles.input} placeholder="30" placeholderTextColor="#64748b"/>

      <Text style={styles.label}>Safety level</Text>
      <View style={styles.row}>
        {(['passive','active','aggressive'] as const).map(v=>(
          <TouchableOpacity key={v} onPress={()=>setSafety(v)} style={[styles.chip, safety===v && styles.chipActive]}><Text style={styles.chipText}>{v}</Text></TouchableOpacity>
        ))}
      </View>

      {loading? <ActivityIndicator color="#8b5cf6" style={{marginTop:16}}/> :
        <TouchableOpacity onPress={start} style={styles.primaryBtn}><Text style={styles.primaryTxt}>Start Episode</Text></TouchableOpacity>
      }
      <TouchableOpacity onPress={()=>router.back()} style={styles.ghostBtn}><Text style={styles.ghostTxt}>Cancel</Text></TouchableOpacity>
    </ScrollView>
  );
}
const styles=StyleSheet.create({
  container:{flex:1, backgroundColor:'#0f172a'}, content:{padding:16, gap:8, paddingBottom:32},
  title:{fontSize:22, fontWeight:'700', color:'#f1f5f9'}, subtitle:{color:'#64748b', marginBottom:8},
  label:{color:'#94a3b8', fontSize:13, fontWeight:'600', marginTop:8}, hint:{color:'#64748b'},
  pickerBox:{gap:6, marginTop:4}, opt:{padding:10, borderRadius:8, backgroundColor:'#1e293b', borderWidth:1, borderColor:'#334155'}, optActive:{borderColor:'#8b5cf6', backgroundColor:'#2e1065'}, optText:{color:'#f1f5f9'},
  card:{padding:12, borderRadius:10, backgroundColor:'#1e293b', borderWidth:1, borderColor:'#334155', marginTop:6}, cardActive:{borderColor:'#8b5cf6'}, cardTitle:{color:'#f1f5f9', fontWeight:'600'}, cardDesc:{color:'#94a3b8', fontSize:12},
  input:{backgroundColor:'#1e293b', borderWidth:1, borderColor:'#334155', borderRadius:8, padding:12, color:'#f1f5f9', marginTop:4},
  row:{flexDirection:'row', gap:8, marginTop:4}, chip:{paddingVertical:8, paddingHorizontal:14, borderRadius:999, backgroundColor:'#1e293b', borderWidth:1, borderColor:'#334155'}, chipActive:{backgroundColor:'#8b5cf6', borderColor:'#8b5cf6'}, chipText:{color:'#f1f5f9', fontSize:13},
  primaryBtn:{backgroundColor:'#8b5cf6', padding:14, borderRadius:10, alignItems:'center', marginTop:16}, primaryTxt:{color:'#fff', fontWeight:'700'},
  ghostBtn:{padding:12, alignItems:'center'}, ghostTxt:{color:'#94a3b8'}
});
