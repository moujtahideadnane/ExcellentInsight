import axios from 'axios';
import { useAuthStore } from '@/stores/auth-store';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000, 
  headers: {
    'Content-Type': 'application/json',
  },
});

interface QueuedRequest {
  resolve: (token: string | null) => void;
  reject: (error: unknown) => void;
}

let isRefreshing = false;
let failedQueue: QueuedRequest[] = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

/**
 * Returns a valid access token. If the current one is expired or missing,
 * it attempts to refresh it using the refresh token.
 */
export async function getValidToken(): Promise<string | null> {
  const { accessToken, refreshToken, user, setAuth, logout } = useAuthStore.getState();
  
  if (!accessToken) return null;

  // Simple JWT expiration check
  try {
    const parts = accessToken.split('.');
    if (parts.length === 3) {
      const part = parts[1];
      if (part) {
        const payload = JSON.parse(atob(part.replace(/-/g, '+').replace(/_/g, '/')));
        const now = Math.floor(Date.now() / 1000);
        // If token is valid for more than 30 seconds, return it
        if (payload.exp && payload.exp - now > 30) {
          return accessToken;
        }
      }
    }
  } catch {
    // If parsing fails, proceed to refresh
  }

  if (!refreshToken) {
    logout();
    return null;
  }

  // Handle concurrent refresh requests
  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve, reject });
    });
  }

  isRefreshing = true;

  try {
    const response = await axios.post(`${BASE_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });

    const { access_token, refresh_token: new_refresh_token, user: freshUser } = response.data;
    setAuth(freshUser || user, access_token, new_refresh_token || refreshToken);
    processQueue(null, access_token);
    return access_token;
  } catch (refreshError) {
    processQueue(refreshError, null);
    logout();
    if (typeof window !== 'undefined') window.location.href = '/login';
    return null;
  } finally {
    isRefreshing = false;
  }
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status ?? 0;
    if (status >= 500) return 'Something went wrong on our end. Please try again in a moment.';
    if (error.code === 'ECONNABORTED') return 'The request timed out. Please check your connection.';
    return error.response?.data?.detail ?? (error as Error).message ?? 'An unexpected error occurred.';
  }
  return 'An unexpected error occurred.';
}

api.interceptors.request.use(
  async (config) => {
    // Proactively get a valid token if possible
    const token = await getValidToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If we get a 401 and haven't retried yet, try one manual refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const token = await getValidToken();
      if (token) {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return api(originalRequest);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
