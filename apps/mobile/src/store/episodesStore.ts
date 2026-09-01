import { create } from 'zustand';
import { Episode, EpisodeDetail, PostureSummary } from '@purple/shared/types';

interface EpisodesState {
  episodes: Episode[];
  currentEpisode: EpisodeDetail | null;
  postureSummary: PostureSummary | null;
  isLoading: boolean;
  error: string | null;
  setEpisodes: (episodes: Episode[]) => void;
  setCurrentEpisode: (episode: EpisodeDetail | null) => void;
  setPostureSummary: (summary: PostureSummary | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addEpisode: (episode: Episode) => void;
  updateEpisode: (id: string, updates: Partial<Episode>) => void;
}

export const useEpisodesStore = create<EpisodesState>((set) => ({
  episodes: [],
  currentEpisode: null,
  postureSummary: null,
  isLoading: false,
  error: null,

  setEpisodes: (episodes) => set({ episodes }),
  setCurrentEpisode: (episode) => set({ currentEpisode: episode }),
  setPostureSummary: (summary) => set({ postureSummary: summary }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  addEpisode: (episode) => set((state) => ({ episodes: [episode, ...state.episodes] })),
  updateEpisode: (id, updates) =>
    set((state) => ({
      episodes: state.episodes.map((e) => (e.id === id ? { ...e, ...updates } : e)),
    })),
}));