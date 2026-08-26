import { useState, useEffect, useCallback, useRef } from 'react';
import { Message, Artifact, SendMessagePayload } from '../types';
import { api } from '../api/client';

// Local storage helper functions for offline/instant persistence
const getLocalMessages = (sessionId: string): Message[] => {
  try {
    const raw = localStorage.getItem(`lenny_msgs_${sessionId}`);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    console.warn('Failed to read messages from localStorage', e);
    return [];
  }
};

const saveLocalMessages = (sessionId: string, msgs: Message[]) => {
  try {
    localStorage.setItem(`lenny_msgs_${sessionId}`, JSON.stringify(msgs));
  } catch (e) {
    console.warn('Failed to save messages to localStorage', e);
  }
};

const getLocalArtifact = (sessionId: string): Artifact | null => {
  try {
    const raw = localStorage.getItem(`lenny_art_${sessionId}`);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const saveLocalArtifact = (sessionId: string, art: Artifact | null) => {
  try {
    if (art) {
      localStorage.setItem(`lenny_art_${sessionId}`, JSON.stringify(art));
    } else {
      localStorage.removeItem(`lenny_art_${sessionId}`);
    }
  } catch (e) {
    console.warn('Failed to save artifact to localStorage', e);
  }
};

export function useChat(
  activeSessionId: string | null,
  onCreateSession: () => Promise<any>,
  onSessionMetaRefresh: () => void // Only refreshes sidebar session list metadata
) {
  const [messages, setMessages] = useState<Message[]>(() => {
    return activeSessionId ? getLocalMessages(activeSessionId) : [];
  });
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(() => {
    return activeSessionId ? getLocalArtifact(activeSessionId) : null;
  });
  const [isArtifactViewerOpen, setIsArtifactViewerOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ─── Race-condition guard ─────────────────────────────────────────────
  const stateVersionRef = useRef(0);
  const loadedSessionIdRef = useRef<string | null>(null);
  const loadAbortRef = useRef<AbortController | null>(null);

  // Fetch messages from the server when the active session changes.
  const loadMessages = useCallback(async (sessionId: string) => {
    // Abort any previous in-flight load.
    loadAbortRef.current?.abort();
    const abortController = new AbortController();
    loadAbortRef.current = abortController;

    const versionAtStart = stateVersionRef.current;
    loadedSessionIdRef.current = sessionId;

    // Instant local restore from localStorage if present
    const cachedMsgs = getLocalMessages(sessionId);
    if (cachedMsgs.length > 0) {
      setMessages(cachedMsgs);
      const cachedArt = getLocalArtifact(sessionId);
      if (cachedArt) {
        setActiveArtifact(cachedArt);
      }
    }

    try {
      setIsLoading(true);
      setError(null);
      const detail = await api.getSession(sessionId);

      // Guard 1: component was aborted / session changed.
      if (abortController.signal.aborted) return;

      // Guard 2: session changed while fetch was in-flight.
      if (loadedSessionIdRef.current !== sessionId) return;

      // Guard 3: a sendMessage started (or finished) while this fetch
      // was in-flight — the local optimistic state is fresher.
      if (stateVersionRef.current !== versionAtStart) return;

      const serverMessages = detail.messages || [];
      setMessages(serverMessages);
      saveLocalMessages(sessionId, serverMessages);

      if (detail.artifacts && detail.artifacts.length > 0) {
        const topArtifact = detail.artifacts[0];
        setActiveArtifact(topArtifact);
        saveLocalArtifact(sessionId, topArtifact);
      } else {
        setActiveArtifact(null);
        saveLocalArtifact(sessionId, null);
        setIsArtifactViewerOpen(false);
      }
    } catch (err: any) {
      if (abortController.signal.aborted) return; // expected abort
      console.error('Failed to load session messages:', err);
      // If we have cached messages locally, don't show a blocking error
      if (cachedMsgs.length === 0) {
        setError(err.message || 'Could not load conversation history.');
      }
    } finally {
      if (!abortController.signal.aborted) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      // Instantly load local cached history first to prevent blank screen
      const cached = getLocalMessages(activeSessionId);
      if (cached.length > 0) {
        setMessages(cached);
      }
      loadMessages(activeSessionId);
    } else {
      setMessages([]);
      setActiveArtifact(null);
      setIsArtifactViewerOpen(false);
    }
  }, [activeSessionId, loadMessages]);

  const sendMessage = async (
    content: string,
    provider: 'gemini' | 'ollama' = 'gemini',
    intent?: 'NORMAL_QA' | 'SHIP30' | 'ARTIFACT'
  ) => {
    if (!content.trim() || isLoading) return;

    // === SESSION CREATION (if needed) ===
    let targetSessionId = activeSessionId;
    if (!targetSessionId) {
      try {
        const newSession = await onCreateSession();
        if (!newSession) {
          setError('Could not initialize a new conversation session.');
          return;
        }
        targetSessionId = newSession.id;
        setMessages([]);
      } catch (err: any) {
        setError(err.message || 'Failed to create session');
        return;
      }
    }

    // ── BEGIN SEND ──────────────────────────────────────────────────────
    stateVersionRef.current += 1;
    loadAbortRef.current?.abort();
    loadAbortRef.current = null;

    // Step 1: Optimistically append user message immediately.
    const tempUserMsgId = `temp-${Date.now()}-user`;
    const userMsg: Message = {
      id: tempUserMsgId,
      session_id: targetSessionId!,
      role: 'user',
      content: content.trim(),
      created_at: new Date().toISOString(),
      sources: [],
      artifacts: [],
    };

    setMessages((prev) => {
      const next = [...prev, userMsg];
      saveLocalMessages(targetSessionId!, next);
      return next;
    });
    setIsLoading(true);
    setError(null);

    // Step 2: Send request to backend.
    try {
      const payload: SendMessagePayload = {
        content: content.trim(),
        provider,
        intent,
      };

      const response = await api.sendMessage(targetSessionId!, payload);

      const asstMsg: Message = {
        id: response.message_id,
        session_id: response.session_id,
        role: 'assistant',
        content: response.content,
        created_at: new Date().toISOString(),
        model_provider: response.model_provider,
        model_name: response.model_name,
        latency_ms: response.latency_ms,
        intent_type: response.intent_type,
        sources: response.sources || [],
        artifacts: response.artifact ? [response.artifact] : [],
      };

      setMessages((prev) => {
        const next = [
          ...prev.filter((m) => m.id !== tempUserMsgId),
          userMsg,
          asstMsg,
        ];
        saveLocalMessages(targetSessionId!, next);
        return next;
      });

      if (response.artifact) {
        setActiveArtifact(response.artifact);
        saveLocalArtifact(targetSessionId!, response.artifact);
        setIsArtifactViewerOpen(true);
      }

      onSessionMetaRefresh();
    } catch (err: any) {
      console.error('Failed to send message:', err);
      const errMsg = err.message || 'Error communicating with assistant. Please try again.';
      setError(errMsg);

      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        session_id: targetSessionId!,
        role: 'assistant',
        content: `⚠️ **Error**: ${errMsg}`,
        created_at: new Date().toISOString(),
        sources: [],
        artifacts: [],
      };
      setMessages((prev) => {
        const next = [...prev, errorMsg];
        saveLocalMessages(targetSessionId!, next);
        return next;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const openArtifact = (artifact: Artifact) => {
    setActiveArtifact(artifact);
    setIsArtifactViewerOpen(true);
  };

  const toggleArtifactViewer = () => {
    setIsArtifactViewerOpen((prev) => !prev);
  };

  return {
    messages,
    activeArtifact,
    isArtifactViewerOpen,
    isLoading,
    error,
    sendMessage,
    openArtifact,
    toggleArtifactViewer,
    setIsArtifactViewerOpen,
  };
}
