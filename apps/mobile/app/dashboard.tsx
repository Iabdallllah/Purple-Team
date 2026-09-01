import { useEffect, useState } from 'react';
import { View, Text, ScrollView, RefreshControl, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { useApi } from '@/hooks/useApi';
import { api } from '@/lib/api';
import { PostureSummary, Episode } from '@purple/shared/types';
import { useNotifications, scheduleLocalNotification } from '@/hooks/useNotifications';
import { useSocket } from '@/hooks/useSocket';

export default function DashboardScreen() {
  const router = useRouter();
  const { expoPushToken } = useNotifications();
  const { events } = useSocket();
  const [posture, setPosture] = useState<PostureSummary | null>(null);
  const [recentEpisodes, setRecentEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(()=>{
    if(events.length){
      const last=events[0];
      scheduleLocalNotification(`Episode ${last.type}`, `${last.episodeId.slice(0,8)} – ${JSON.stringify(last.data).slice(0,60)}`);
    }
  },[events]);

  const loadData = async () => {
    try {
      const [postureRes, episodesRes] = await Promise.all([
        api.getEpisodes({ page: 1, limit: 5 }),
        api.getEpisodes({ page: 1, limit: 10 }),
      ]);
      // posture endpoint currently reuses episodes; fallback mock if not PostureSummary
      const summary = (postureRes as any)?.currentScore ? postureRes as any : null;
      setPosture(summary);
      setRecentEpisodes(episodesRes.items || []);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      style={styles.container}
      contentContainerStyle={styles.content}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Dashboard</Text>
        <Text style={styles.subtitle}>Purple Platform {expoPushToken ? '• push ready' : ''}</Text>
        <TouchableOpacity onPress={()=>router.push('/dashboard/new-episode' as any)} style={[styles.primaryButton, {marginTop:12}]}>
          <Text style={styles.buttonText}>+ Start Experiment</Text>
        </TouchableOpacity>
      </View>

      {posture && (
        <View style={styles.scoreCard}>
          <Text style={styles.scoreLabel}>Security Posture</Text>
          <Text style={styles.scoreValue}>{posture.currentScore}</Text>
          <Text style={[styles.scoreTrend, { color: posture.trend === 'improving' ? '#22c55e' : posture.trend === 'declining' ? '#ef4444' : '#f59e0b' }]}>
            {posture.trend === 'improving' ? '↑' : posture.trend === 'declining' ? '↓' : '→'} {posture.trend}
          </Text>
        </View>
      )}

      <View style={styles.statsGrid}>
        <StatCard label="Detection Rate" value={`${posture?.detectionRate ? (posture.detectionRate * 100).toFixed(1) : 0}%`} icon="DR" />
        <StatCard label="Avg MTTR" value={`${posture?.mttrSeconds || 0}s`} icon="TM" />
        <StatCard label="Coverage" value={`${posture?.totalEpisodes || 0}%`} icon="CV" />
        <StatCard label="Episodes" value={`${posture?.totalEpisodes || 0}`} icon="EP" />
      </View>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Recent Episodes</Text>
        <TouchableOpacity onPress={() => router.push('/dashboard/episodes')} style={styles.seeAll}>
          <Text style={styles.seeAllText}>See All</Text>
        </TouchableOpacity>
      </View>

      {recentEpisodes.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>No episodes yet</Text>
          <TouchableOpacity onPress={() => router.push('/dashboard/projects')} style={styles.primaryButton}>
            <Text style={styles.buttonText}>Create Project</Text>
          </TouchableOpacity>
        </View>
      ) : (
        recentEpisodes.map((ep) => (
          <TouchableOpacity key={ep.id} onPress={() => router.push(`/dashboard/episodes/${ep.id}`)} style={styles.episodeCard}>
            <View style={styles.episodeInfo}>
              <Text style={styles.episodeProject}>{ep.project || 'Unknown Project'}</Text>
              <View style={styles.episodeMeta}>
                <Text style={styles.episodeTarget}>{ep.targetApp || 'Unknown Target'}</Text>
                <Text style={styles.episodeScenario}>{ep.scenario}</Text>
              </View>
            </View>
            <View style={styles.episodeStatus}>
              <Text style={[styles.episodeStatusText, { color: getStatusColor(ep.status) }]}>
                {ep.status}
              </Text>
              {ep.score !== null && (
                <Text style={styles.episodeScore}>{ep.score}</Text>
              )}
            </View>
          </TouchableOpacity>
        ))}
      )}
    </ScrollView>
  );
}

function StatCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statIcon}>{icon}</Text>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'completed': return '#22c55e';
    case 'running': return '#3b82f6';
    case 'failed': return '#ef4444';
    case 'pending': return '#f59e0b';
    default: return '#64748b';
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f172a',
  },
  loadingText: {
    color: '#94a3b8',
    fontSize: 16,
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#f1f5f9',
  },
  subtitle: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 4,
  },
  scoreCard: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 24,
    marginBottom: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  scoreLabel: {
    fontSize: 14,
    color: '#94a3b8',
    marginBottom: 8,
  },
  scoreValue: {
    fontSize: 56,
    fontWeight: '700',
    color: '#f1f5f9',
  },
  scoreTrend: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 8,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  statIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#f1f5f9',
  },
  statLabel: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 4,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  seeAll: {
    padding: 4,
  },
  seeAllText: {
    color: '#8b5cf6',
    fontSize: 14,
    fontWeight: '500',
  },
  emptyState: {
    alignItems: 'center',
    padding: 32,
    backgroundColor: '#1e293b',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  emptyText: {
    color: '#94a3b8',
    fontSize: 16,
    marginBottom: 16,
  },
  primaryButton: {
    backgroundColor: '#8b5cf6',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  episodeCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  episodeInfo: {
    flex: 1,
  },
  episodeProject: {
    fontSize: 16,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  episodeMeta: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 4,
  },
  episodeTarget: {
    fontSize: 13,
    color: '#64748b',
  },
  episodeScenario: {
    fontSize: 13,
    color: '#8b5cf6',
    fontWeight: '500',
  },
  episodeStatus: {
    alignItems: 'flex-end',
  },
  episodeStatusText: {
    fontSize: 13,
    fontWeight: '600',
  },
  episodeScore: {
    fontSize: 18,
    fontWeight: '700',
    color: '#f1f5f9',
    marginTop: 4,
  },
});