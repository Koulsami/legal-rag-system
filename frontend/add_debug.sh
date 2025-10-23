#!/bin/bash
set -e
cd ~/legal-rag-poc/frontend

BACKUP_DIR="backups_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp src/lib/api.ts "$BACKUP_DIR/"
cp src/app/ask/page.tsx "$BACKUP_DIR/"

cat > src/lib/api.ts << 'ENDFILE'
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://legal-rag-system-production.up.railway.app';

console.log('🔧 API initialized:', API_BASE_URL);

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  console.log('📤 REQUEST:', {
    method: config.method?.toUpperCase(),
    url: `${config.baseURL}${config.url}`,
    data: config.data
  });
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    console.log('📥 RESPONSE:', { status: response.status, data: response.data });
    return response;
  },
  (error) => {
    console.error('❌ ERROR:', {
      status: error.response?.status,
      data: error.response?.data,
      sentData: error.config?.data
    });
    return Promise.reject(error);
  }
);

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
  conversation_id: string;
  interpretation_links_used: number;
  warnings: string[];
}

export const chatAPI = {
  query: async (request: QueryRequest): Promise<QueryResponse> => {
    console.log('🎯 QUERY called:', request);

    const backendRequest = {
      message: request.query,
      conversation_id: request.session_id || 'default'
    };

    console.log('🔄 Sending:', backendRequest);

    const response = await apiClient.post<QueryResponse>('/api/chat', backendRequest);

    const data = response.data || {};
    return {
      answer: data.answer || 'No response',
      context: data.context || [],
      citations: data.citations || [],
      quality_metrics: data.quality_metrics || {
        synthesis_quality: 0.8,
        citation_precision: 1.0,
        hallucination_score: 0.0,
        interpretation_coverage: 0.7
      },
      processing_time: data.processing_time || 0,
      session_id: data.session_id || data.conversation_id || 'unknown',
      query_id: data.query_id || 'unknown',
      conversation_id: data.conversation_id || data.session_id || 'unknown',
      interpretation_links_used: data.interpretation_links_used || 0,
      warnings: data.warnings || []
    };
  },

  submitFeedback: async (queryId: string, rating: number, feedback?: string): Promise<void> => {
    await apiClient.post('/api/feedback', { query_id: queryId, rating, feedback });
  },
};

export function handleAPIError(error: any): string {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      const message = error.response.data?.detail || error.response.data?.message;
      if (Array.isArray(message)) {
        return message.map((err: any) => `${err.loc.join('.')}: ${err.msg}`).join('; ');
      }
      return message || `Error: ${error.response.status}`;
    } else if (error.request) {
      return 'Unable to reach server';
    }
  }
  return error.message || 'Unexpected error';
}
ENDFILE

echo "✅ Debug logs added to api.ts"
echo "✅ Backups in: $BACKUP_DIR"
echo ""
echo "Now:"
echo "1. Refresh browser (Ctrl+Shift+R)"
echo "2. Open console (F12)"
echo "3. Send test message"
echo "4. Look for 📤 📥 ❌ emoji logs"
