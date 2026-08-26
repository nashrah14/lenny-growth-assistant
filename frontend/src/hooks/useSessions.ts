import { useState, useEffect, useCallback } from 'react';
import { Session } from '../types';
import { api } from '../api/client';

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);

  // CRITICAL: No [activeSessionId] dependency here.
  // fetchSessions must NOT depend on activeSessionId because that causes a
  // new function ref every time activeSessionId changes, which triggers useChat's
  // useEffect to re-run loadMessages, blowing away the local optimistic state.
  const fetchSessions = useCallback(async () => {
    try {
      setIsLoadingSessions(true);
      const data = await api.listSessions();
      setSessions(data);
      // Only auto-select on initial empty state, NOT on every refresh.
      // We use a functional updater to avoid a stale closure.
      setActiveSessionId((currentId) => {
        if (!currentId && data.length > 0) {
          return data[0].id;
        }
        return currentId;
      });
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setIsLoadingSessions(false);
    }
  }, []); // Empty deps — stable across renders, never recreated

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]); // fetchSessions is stable, so this only runs once on mount

  const createNewSession = async (title?: string) => {
    try {
      const newSession = await api.createSession(title || 'New Conversation');
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      return newSession;
    } catch (err) {
      console.error('Failed to create session:', err);
      return null;
    }
  };

  const deleteSession = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      await api.deleteSession(id);
      try {
        localStorage.removeItem(`lenny_msgs_${id}`);
        localStorage.removeItem(`lenny_art_${id}`);
      } catch {}
      setSessions((prev) => {
        const remaining = prev.filter((s) => s.id !== id);
        // If we're deleting the active session, switch to the next one.
        setActiveSessionId((currentId) => {
          if (currentId === id) {
            return remaining.length > 0 ? remaining[0].id : null;
          }
          return currentId;
        });
        return remaining;
      });
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };


  // refreshSessions: used by the session list sidebar to pull updated titles/timestamps.
  // IMPORTANT: This must NOT be used as onSessionUpdated in useChat, because doing so
  // would trigger a loadMessages reload after every sent message (wiping the local state).
  const refreshSessions = useCallback(async () => {
    try {
      const data = await api.listSessions();
      setSessions(data);
    } catch (err) {
      console.error('Failed to refresh sessions:', err);
    }
  }, []);

  return {
    sessions,
    activeSessionId,
    setActiveSessionId,
    isLoadingSessions,
    createNewSession,
    deleteSession,
    refreshSessions,
  };
}
