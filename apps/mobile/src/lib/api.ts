import { useAuthStore } from '@/store/authStore';

const API_BASE = __DEV__ ? 'http://10.0.2.2:8001' : 'https://api.purple-platform.com';

class ApiClient {
  private getAuthHeaders(): Record<string, string> {
    const token = useAuthStore.getState().token;
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE}/api/v1${endpoint}`, {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string; token_type: string; expires_in: number }>(
      '/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }
    );
  }

  async register(data: { email: string; password: string; full_name: string }) {
    return this.request<{ id: string; email: string; full_name: string }>(
      '/auth/register',
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  async refreshToken() {
    const refreshToken = useAuthStore.getState().refreshToken;
    const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    return response.json();
  }

  // Projects
  async getProjects() {
    return this.request<{ items: any[]; total: number }>('/projects');
  }

  async createProject(data: { name: string; description?: string }) {
    return this.request<any>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Targets
  async getTargets(projectId: string) {
    return this.request<{ items: any[]; total: number }>(`/targets?project_id=${projectId}`);
  }

  async createTarget(data: { project_id: string; name: string; type: string; config: any }) {
    return this.request<any>('/targets', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Episodes
  async getEpisodes(params?: { project_id?: string; status?: string; page?: number }) {
    const search = new URLSearchParams();
    if (params?.project_id) search.set('project_id', params.project_id);
    if (params?.status) search.set('status', params.status);
    if (params?.page) search.set('page', params.page.toString());
    return this.request<{ items: any[]; total: number }>(`/episodes?${search}`);
  }

  async createEpisode(data: {
    project_id: string;
    target_app_id: string;
    scenario: string;
    constraints?: any;
  }) {
    return this.request<any>('/episodes', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getEpisode(episodeId: string) {
    return this.request<any>(`/episodes/${episodeId}`);
  }

  async getEpisodeScore(episodeId: string) {
    return this.request<any>(`/episodes/${episodeId}/score`);
  }

  // Real-time: we'll use Socket.io separately
}

export const api = new ApiClient();