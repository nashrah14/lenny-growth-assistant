/**
 * TypeScript Type Definitions for The Lenny Growth Assistant
 */

export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  created_at: string;
  last_login_at?: string | null;
}

export interface SignupPayload {
  name: string;
  email: string;
  password: string;
  confirm_password?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  message: string;
}

export interface SourceCitation {
  id?: string;
  chunk_id: string;
  source_title: string;
  source_url?: string | null;
  speaker?: string | null;
  source_type: string;
  relevance_score?: number | null;
  rank: number;
  snippet: string;
}

export interface Artifact {
  id: string;
  session_id: string;
  message_id?: string | null;
  artifact_type: 'html' | 'markdown';
  title: string;
  content: string;
  raw_content: string;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  model_provider?: string | null;
  model_name?: string | null;
  latency_ms?: number | null;
  intent_type?: 'NORMAL_QA' | 'SHIP30' | 'ARTIFACT' | string | null;
  sources: SourceCitation[];
  artifacts: Artifact[];
}

export interface Session {
  id: string;
  user_id?: string | null;
  title: string;
  created_at: string;
  updated_at: string;
  user_metadata?: Record<string, any>;
}

export interface SessionDetail extends Session {
  messages: Message[];
  artifacts: Artifact[];
}

export interface SendMessagePayload {
  content: string;
  provider?: 'gemini' | 'ollama';
  model?: string;
  intent?: 'NORMAL_QA' | 'SHIP30' | 'ARTIFACT';
}

export interface ChatResponse {
  session_id: string;
  message_id: string;
  role: string;
  content: string;
  intent_type: string;
  model_provider: string;
  model_name: string;
  latency_ms: number;
  sources: SourceCitation[];
  artifact?: Artifact | null;
  diagnostics?: {
    query: string;
    dense_latency_ms: number;
    bm25_latency_ms: number;
    rrf_latency_ms: number;
    rerank_latency_ms: number;
    total_latency_ms: number;
    dense_candidate_count: number;
    bm25_candidate_count: number;
    fused_candidate_count: number;
    final_context_count: number;
  };
}

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  timestamp: string;
  database: string;
  qdrant: string;
  llm_providers: Record<string, boolean>;
}
