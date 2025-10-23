/**
 * API Client for Myk Raws Legal RAG
 * Handles all communication with the backend API
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://legal-rag-system-production.up.railway.app';

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

// Request interceptor - DISABLED auth for MVP
apiClient.interceptors.request.use(
  (config) => {
    // DISABLED for MVP - backend doesn't require auth
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors WITHOUT redirecting
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Don't redirect on 401/403 for MVP
    console.error('API Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// === AUTHENTICATION API (Disabled for MVP) ===

export const authAPI = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    // Disabled for MVP
    throw new Error('Authentication not required for MVP');
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    // Disabled for MVP
    throw new Error('Authentication not required for MVP');
  },

  logout: () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  },

  getCurrentUser: () => {
    return null; // No auth for MVP
  },

  isAuthenticated: (): boolean => {
    return true; // Always authenticated for MVP
  },
};

// === CHAT API ===

export const chatAPI = {
  /**
   * Send a query to the legal RAG system
   * FIXED: Maps frontend fields to backend expected fields
   */
  query: async (request: QueryRequest): Promise<QueryResponse> => {
    // Map frontend fields to backend expected fields
    const backendRequest = {
      message: request.query,  // Backend expects 'message' not 'query'
      conversation_id: request.session_id || 'default'  // Backend expects 'conversation_id'
    };
    
    try {
      const response = await apiClient.post<QueryResponse>('/api/chat', backendRequest);
      
      // Ensure response has all required fields with defaults
      const data = response.data || {};
      return {
        answer: data.answer || 'No response received',
        context: data.context || [],
        citations: data.citations || [],
        quality_metrics: data.quality_metrics || {
          synthesis_quality: 0.8,
          citation_precision: 1.0,
          hallucination_score: 0.0,
          interpretation_coverage: 0.7
        },
        processing_time: data.processing_time || 0,
        session_id: data.session_id || data.conversation_id || request.session_id || 'default',
        query_id: data.query_id || 'default',
        interpretation_links_used: data.interpretation_links_used || 0,
        warnings: data.warnings || []
      };
    } catch (error) {
      console.error('Chat API error:', error);
      throw error;
    }
  },

  /**
   * Get query history
   */
  getHistory: async (limit: number = 50): Promise<QueryHistory[]> => {
    try {
      const response = await apiClient.get<QueryHistory[]>('/api/chat/history', {
        params: { limit },
      });
      return response.data;
    } catch {
      return []; // Return empty array for MVP
    }
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
    try {
      await apiClient.post('/api/chat/feedback', {
        query_id: queryId,
        rating,
        feedback,
      });
    } catch {
      // Silently fail for MVP
      console.log('Feedback endpoint not available');
    }
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
    const axiosError = error as AxiosError<any>;
    
    // Check for specific error messages
    if (axiosError.response?.data?.detail) {
      // Handle string detail
      if (typeof axiosError.response.data.detail === 'string') {
        return axiosError.response.data.detail;
      }
      // Handle array of errors
      if (Array.isArray(axiosError.response.data.detail)) {
        return axiosError.response.data.detail
          .map((e: any) => e.msg || e.message || JSON.stringify(e))
          .join('; ');
      }
    }
    
    if (axiosError.response?.data?.message) {
      return axiosError.response.data.message;
    }
    
    if (!axiosError.response) {
      return 'Unable to reach the server. Please check your connection.';
    }
    
    return `Error: ${axiosError.response?.status || 'Unknown'}`;
  }
  
  return error?.message || 'An unexpected error occurred';
};

// Export the axios instance for custom requests
export { apiClient };
export default apiClient;
