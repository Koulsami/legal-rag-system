/**
 * API Client for Myk Raws Legal RAG
 * Handles all communication with the backend API
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api.mykraws.com';

// Types
export interface QueryRequest {
  query: string;
  session_id?: string;
  include_interpretive_cases?: boolean;
  max_results?: number;
  enable_synthesis?: boolean;
}

export interface ContextDocument {
  doc_id: string;
  doc_type: 'statute' | 'case';
  title: string;
  text: string;
  citation: string;
  score: number;
  is_interpretive?: boolean;
  interprets_statute_id?: string;
  interpretation_type?: string;
}

export interface QueryResponse {
  answer: string;
  context: ContextDocument[];
  citations: string[];
  quality_metrics: {
    synthesis_quality: number;
    citation_precision: number;
    hallucination_score: number;
    interpretation_coverage: number;
  };
  processing_time: number;
  session_id: string;
  query_id: string;
  interpretation_links_used: number;
  warnings: string[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    email: string;
    name: string;
  };
}

export interface QueryHistory {
  query_id: string;
  query_text: string;
  timestamp: string;
  processing_time: number;
  quality_score: number;
}

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for long queries
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// === AUTHENTICATION API ===

export const authAPI = {
  /**
   * Login user
   */
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/auth/login', data);
    
    // Store token and user info
    localStorage.setItem('auth_token', response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));
    
    return response.data;
  },

  /**
   * Register new user
   */
  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/auth/register', data);
    
    // Store token and user info
    localStorage.setItem('auth_token', response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));
    
    return response.data;
  },

  /**
   * Logout user
   */
  logout: () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  },

  /**
   * Get current user info
   */
  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('auth_token');
  },
};

// === CHAT API ===

export const chatAPI = {
  /**
   * Send a query to the legal RAG system
   */
  query: async (request: QueryRequest): Promise<QueryResponse> => {
    const response = await apiClient.post<QueryResponse>('/api/chat/query', request);
    return response.data;
  },

  /**
   * Get query history
   */
  getHistory: async (limit: number = 50): Promise<QueryHistory[]> => {
    const response = await apiClient.get<QueryHistory[]>('/api/chat/history', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Export conversation
   */
  exportConversation: async (
    sessionId: string,
    format: 'pdf' | 'markdown' | 'json' = 'pdf',
    includeContext: boolean = true
  ): Promise<any> => {
    const response = await apiClient.post('/api/chat/export', {
      session_id: sessionId,
      format,
      include_context: includeContext,
    });
    return response.data;
  },

  /**
   * Submit feedback on a query
   */
  submitFeedback: async (
    queryId: string,
    rating: number,
    feedback?: string
  ): Promise<void> => {
    await apiClient.post('/api/chat/feedback', {
      query_id: queryId,
      rating,
      feedback,
    });
  },
};

// === HEALTH CHECK API ===

export const healthAPI = {
  /**
   * Check API health
   */
  check: async (): Promise<{
    status: string;
    database: string;
    retrieval_service: boolean;
    interpretation_links: boolean;
  }> => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  /**
   * Get API status
   */
  status: async (): Promise<any> => {
    const response = await apiClient.get('/api/status');
    return response.data;
  },
};

// === ERROR HANDLING UTILITIES ===

export const handleAPIError = (error: any): string => {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      // Server responded with error
      const message = error.response.data?.message || error.response.data?.detail;
      return message || `Error: ${error.response.status}`;
    } else if (error.request) {
      // Request made but no response
      return 'Unable to reach the server. Please check your connection.';
    }
  }
  return error.message || 'An unexpected error occurred';
};

// Export the axios instance for custom requests
export { apiClient };
export default apiClient;
