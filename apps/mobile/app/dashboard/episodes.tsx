import { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, FlatList, ActivityIndicator, RefreshControl, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { api } from '@/lib/api';
import { Episode } from '@purple/shared/types';

export default function EpisodesScreen() {
  const router = useRouter();
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);

  const loadEpisodes = async (pageNum = 1) => {
    try {
      const res = await api.getEpisodes({ page: pageNum, limit: 20 });
      if (pageNum === 1) {
        setEpisodes(res.items || []);
      } else {
        setEpisodes(prev => [...prev, ...(res.items || [])]);
      }
      setPage(pageNum);
    } catch (error) {
      Alert.alert('Error', 'Failed to load episodes');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadEpisodes(1);
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadEpisodes(1);
  };

  const onEndReached = () => {
    loadEpisodes(page + 1);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#22c55e';
      case 'running': return '#3b82f6';
      case 'failed': return '#ef4444';
      case 'pending': return '#f59e0b';
      default: return '#64748b';
    }
  };

  if (loading && episodes.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading episodes...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Episodes</Text>
      </View>

      {episodes.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>No episodes yet</Text>
          <Text style={styles.emptySubtext}>Create a project and start an episode to see results here</Text>
        </View>
      ) : (
        <FlatList
          data={episodes}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity onPress={() => console.log('episode', item.id)} style={styles.episodeCard}>
              <View style={styles.episodeInfo}>
                <Text style={styles.episodeProject}>{item.project || 'Unknown Project'}</Text>
                <View style={styles.episodeMeta}>
                  <Text style={styles.episodeTarget}>{item.targetApp || 'Unknown Target'}</Text>
                  <Text style={styles.episodeScenario}>{item.scenario}</Text>
                </View>
              </View>
              <View style={styles.episodeStatus}>
                <Text style={[styles.episodeStatusText, { color: getStatusColor(item.status) }]}>
                  {item.status}
                </Text>
                {item.score !== null && (
                  <Text style={styles.episodeScore}>{item.score}</Text>
                )}
              </View>
            </TouchableOpacity>
          )}
          keyExtractor={(item) => item.id}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          onEndReached={onEndReached}
          onEndReachedThreshold={0.5}
          contentContainerStyle={styles.listContent}
        />
      )}
    </View>
  );
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return '#22c55e';
    case 'running': return '#3b82f6';
    case 'failed': return '#ef4444';
    case 'pending': return '#f59e0b';
    default: return '#64748b';
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#f1f5f9',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 8,
  },
  emptySubtext: {
    color: '#64748b',
    textAlign: 'center',
  },
  listContent: {
    padding: 16,
    gap: 12,
  },
  episodeCard: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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