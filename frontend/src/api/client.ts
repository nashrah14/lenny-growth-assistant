/**
 * API Client for The Lenny Growth Assistant
 * Handles Sessions, Messages, Artifacts, Health, and Cookie-based Authentication.
 */
import {
  User,
  SignupPayload,
  LoginPayload,
  AuthResponse,
  Session,
  SessionDetail,
  Message,
  Artifact,
  ChatResponse,
  SendMessagePayload,
  HealthStatus
} from '../types';

const API_BASE = '/api/v1';

export class ApiError extends Error {
  code: string;
  status: number;
  details?: any;

  constructor(message: string, status: number, code: string = 'API_ERROR', details?: any) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      credentials: 'include', // Ensures HttpOnly auth cookies are sent and received
    });

    if (!res.ok) {
      let errorData: any = {};
      try {
        errorData = await res.json();
      } catch {
        errorData = { error: { message: res.statusText } };
      }
      throw new ApiError(
        errorData.error?.message || `HTTP error ${res.status}`,
        res.status,
        errorData.error?.code || 'UNKNOWN_ERROR',
        errorData.error?.details
      );
    }

    if (res.status === 204) {
      return {} as T;
    }
    return await res.json();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || 'Network connection failed', 0, 'NETWORK_ERROR');
  }
}

export const api = {
  // Authentication
  signup: (payload: SignupPayload) =>
    request<AuthResponse>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  login: (payload: LoginPayload) =>
    request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  logout: () =>
    request<{ message: string }>('/auth/logout', {
      method: 'POST',
    }),

  getMe: () => request<User>('/auth/me'),

  // Sessions (Filtered by authenticated user)
  createSession: (title?: string) =>
    request<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ title: title || 'New Conversation' }),
    }),

  listSessions: () => request<Session[]>('/sessions'),

  getSession: (id: string) => request<SessionDetail>(`/sessions/${id}`),

  updateSessionTitle: (id: string, title: string) =>
    request<Session>(`/sessions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }),

  deleteSession: (id: string) =>
    request<void>(`/sessions/${id}`, {
      method: 'DELETE',
    }),

  // Messages
  sendMessage: (sessionId: string, payload: SendMessagePayload) =>
    request<ChatResponse>(`/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getMessages: (sessionId: string) => request<Message[]>(`/sessions/${sessionId}/messages`),

  // Artifacts
  getArtifact: (id: string) => request<Artifact>(`/artifacts/${id}`),

  // Health
  getHealth: () => request<HealthStatus>('/health'),
};
