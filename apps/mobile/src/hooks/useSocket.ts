import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuthStore } from '@/store/authStore';

interface EpisodeEvent {
  type: 'attack' | 'detection' | 'response' | 'score' | 'status';
  episodeId: string;
  data: any;
  timestamp: string;
}

export function useSocket(episodeId?: string) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState<EpisodeEvent[]>([]);
  const token = useAuthStore((state) => state.token);

  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (!token) return;

    const newSocket = io('http://10.0.2.2:8001', {
      auth: { token },
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    newSocket.on('connect', () => {
      setConnected(true);
      if (episodeId) {
        newSocket.emit('join_episode', episodeId);
      }
    });

    newSocket.on('disconnect', () => {
      setConnected(false);
    });

    newSocket.on('episode_event', (event: EpisodeEvent) => {
      setEvents(prev => [event, ...prev].slice(0, 100));
    });

    newSocket.on('episode_status', (status: { episodeId: string; status: string }) => {
      // Handle status updates
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [token, episodeId]);

  const joinEpisode = useCallback((id: string) => {
    socket?.emit('join_episode', id);
  }, [socket]);

  const leaveEpisode = useCallback((id: string) => {
    socket?.emit('leave_episode', id);
  }, [socket]);

  return {
    socket,
    connected,
    events,
    joinEpisode,
    leaveEpisode,
  };
}