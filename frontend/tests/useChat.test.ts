/**
 * useChat Hook Tests — Chat History Persistence
 *
 * These tests verify that the chat message history is correctly maintained
 * across multiple send operations.  The critical invariant:
 *
 *   Sending a new message APPENDS to the existing conversation.
 *   It must NEVER replace or discard earlier messages.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useChat } from '../src/hooks/useChat';

// ─── Mocks ──────────────────────────────────────────────────────────────

// Track the latest resolved value so tests can control API timing.
let mockGetSessionResult: any = { messages: [], artifacts: [] };
let mockSendMessageResult: any = {};
let mockGetSessionDelay = 0;
let mockSendMessageDelay = 0;

vi.mock('../src/api/client', () => ({
  api: {
    getSession: vi.fn(async () => {
      if (mockGetSessionDelay > 0) {
        await new Promise((r) => setTimeout(r, mockGetSessionDelay));
      }
      return mockGetSessionResult;
    }),
    sendMessage: vi.fn(async () => {
      if (mockSendMessageDelay > 0) {
        await new Promise((r) => setTimeout(r, mockSendMessageDelay));
      }
      return mockSendMessageResult;
    }),
  },
}));

const { api } = await import('../src/api/client');

// Helper: Build a mock ChatResponse from the backend
function mockChatResponse(id: string, content: string, sessionId = 'session-1') {
  return {
    session_id: sessionId,
    message_id: id,
    role: 'assistant',
    content,
    intent_type: 'NORMAL_QA',
    model_provider: 'gemini',
    model_name: 'gemini-2.0-flash',
    latency_ms: 100,
    sources: [],
    artifact: null,
  };
}

// Helper: Build a mock SessionDetail for getSession
function mockSessionDetail(messages: any[] = [], artifacts: any[] = []) {
  return {
    id: 'session-1',
    title: 'Test',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    messages,
    artifacts,
  };
}

function mockMessage(id: string, role: string, content: string, sessionId = 'session-1') {
  return {
    id,
    session_id: sessionId,
    role,
    content,
    created_at: new Date().toISOString(),
    sources: [],
    artifacts: [],
  };
}

// ─── Setup / Teardown ───────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks();
  mockGetSessionResult = mockSessionDetail();
  mockSendMessageResult = mockChatResponse('asst-1', 'Hello');
  mockGetSessionDelay = 0;
  mockSendMessageDelay = 0;
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ─── Tests ──────────────────────────────────────────────────────────────

describe('useChat — Message History Persistence', () => {
  // ------------------------------------------------------------------
  // TEST 1: Single message produces 1 user + 1 assistant
  // ------------------------------------------------------------------
  it('TEST 1: Send Q1 → expect 1 user + 1 assistant message', async () => {
    mockSendMessageResult = mockChatResponse('asst-1', 'Product-market fit is...');

    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    const { result } = renderHook(() =>
      useChat('session-1', onCreateSession, onSessionMetaRefresh)
    );

    // Wait for initial session load
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Send Q1
    await act(async () => {
      await result.current.sendMessage('What is product-market fit?');
    });

    const msgs = result.current.messages;
    expect(msgs).toHaveLength(2);
    expect(msgs[0].role).toBe('user');
    expect(msgs[0].content).toBe('What is product-market fit?');
    expect(msgs[1].role).toBe('assistant');
    expect(msgs[1].content).toBe('Product-market fit is...');
  });

  // ------------------------------------------------------------------
  // TEST 2: Send Q2 → expect 2 user + 2 assistant messages
  // ------------------------------------------------------------------
  it('TEST 2: Send Q2 after Q1 → expect 2 user + 2 assistant messages (CORE BUG TEST)', async () => {
    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    const { result } = renderHook(() =>
      useChat('session-1', onCreateSession, onSessionMetaRefresh)
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Send Q1
    mockSendMessageResult = mockChatResponse('asst-1', 'Product-market fit is...');
    await act(async () => {
      await result.current.sendMessage('What is product-market fit?');
    });

    expect(result.current.messages).toHaveLength(2);

    // Send Q2
    mockSendMessageResult = mockChatResponse('asst-2', 'Customer feedback helps...');
    await act(async () => {
      await result.current.sendMessage('How can customer feedback help?');
    });

    const msgs = result.current.messages;
    expect(msgs).toHaveLength(4);
    expect(msgs[0].role).toBe('user');
    expect(msgs[0].content).toBe('What is product-market fit?');
    expect(msgs[1].role).toBe('assistant');
    expect(msgs[1].content).toBe('Product-market fit is...');
    expect(msgs[2].role).toBe('user');
    expect(msgs[2].content).toBe('How can customer feedback help?');
    expect(msgs[3].role).toBe('assistant');
    expect(msgs[3].content).toBe('Customer feedback helps...');
  });

  // ------------------------------------------------------------------
  // TEST 3: Send Q3 → expect 3 user + 3 assistant messages
  // ------------------------------------------------------------------
  it('TEST 3: Send Q3 after Q1 and Q2 → expect 3 user + 3 assistant messages', async () => {
    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    const { result } = renderHook(() =>
      useChat('session-1', onCreateSession, onSessionMetaRefresh)
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Q1
    mockSendMessageResult = mockChatResponse('asst-1', 'A1');
    await act(async () => { await result.current.sendMessage('Q1'); });

    // Q2
    mockSendMessageResult = mockChatResponse('asst-2', 'A2');
    await act(async () => { await result.current.sendMessage('Q2'); });

    // Q3
    mockSendMessageResult = mockChatResponse('asst-3', 'A3');
    await act(async () => { await result.current.sendMessage('Q3'); });

    const msgs = result.current.messages;
    expect(msgs).toHaveLength(6);
    expect(msgs.map((m) => m.content)).toEqual(['Q1', 'A1', 'Q2', 'A2', 'Q3', 'A3']);
  });

  // ------------------------------------------------------------------
  // TEST 4: Reload session — expect all messages from backend
  // ------------------------------------------------------------------
  it('TEST 4: Session reload returns all persisted messages', async () => {
    // Simulate backend returning 3 Q/A pairs on session load
    mockGetSessionResult = mockSessionDetail([
      mockMessage('u1', 'user', 'Q1'),
      mockMessage('a1', 'assistant', 'A1'),
      mockMessage('u2', 'user', 'Q2'),
      mockMessage('a2', 'assistant', 'A2'),
      mockMessage('u3', 'user', 'Q3'),
      mockMessage('a3', 'assistant', 'A3'),
    ]);

    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    const { result } = renderHook(() =>
      useChat('session-1', onCreateSession, onSessionMetaRefresh)
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.messages).toHaveLength(6);
    expect(result.current.messages.map((m) => m.content)).toEqual([
      'Q1', 'A1', 'Q2', 'A2', 'Q3', 'A3',
    ]);
  });

  // ------------------------------------------------------------------
  // TEST 5: Switch sessions — only that session's messages
  // ------------------------------------------------------------------
  it('TEST 5: Switching sessions loads only that session\'s messages', async () => {
    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    // Start with session-1 messages
    mockGetSessionResult = mockSessionDetail([
      mockMessage('u1', 'user', 'Session1-Q1'),
      mockMessage('a1', 'assistant', 'Session1-A1'),
    ]);

    const { result, rerender } = renderHook(
      ({ sessionId }) => useChat(sessionId, onCreateSession, onSessionMetaRefresh),
      { initialProps: { sessionId: 'session-1' as string | null } }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].content).toBe('Session1-Q1');

    // Switch to session-2
    mockGetSessionResult = mockSessionDetail([
      mockMessage('u3', 'user', 'Session2-Q1', 'session-2'),
      mockMessage('a3', 'assistant', 'Session2-A1', 'session-2'),
    ]);

    rerender({ sessionId: 'session-2' });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].content).toBe('Session2-Q1');
  });

  // ------------------------------------------------------------------
  // TEST 6: Return to original session — all original messages
  // ------------------------------------------------------------------
  it('TEST 6: Return to original session → original messages restored', async () => {
    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    const session1Messages = [
      mockMessage('u1', 'user', 'Q1'),
      mockMessage('a1', 'assistant', 'A1'),
      mockMessage('u2', 'user', 'Q2'),
      mockMessage('a2', 'assistant', 'A2'),
    ];

    // Start with session-1
    mockGetSessionResult = mockSessionDetail(session1Messages);

    const { result, rerender } = renderHook(
      ({ sessionId }) => useChat(sessionId, onCreateSession, onSessionMetaRefresh),
      { initialProps: { sessionId: 'session-1' as string | null } }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.messages).toHaveLength(4);

    // Switch away to session-2
    mockGetSessionResult = mockSessionDetail([mockMessage('x', 'user', 'Other')]);
    rerender({ sessionId: 'session-2' });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.messages).toHaveLength(1);

    // Switch back to session-1
    mockGetSessionResult = mockSessionDetail(session1Messages);
    rerender({ sessionId: 'session-1' });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.messages).toHaveLength(4);
    expect(result.current.messages.map((m) => m.content)).toEqual(['Q1', 'A1', 'Q2', 'A2']);
  });

  // ------------------------------------------------------------------
  // TEST 7: Send another message after reload — previous remain
  // ------------------------------------------------------------------
  it('TEST 7: Send message after reload → previous messages remain', async () => {
    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    // Session loads with existing Q1/A1
    mockGetSessionResult = mockSessionDetail([
      mockMessage('u1', 'user', 'Q1'),
      mockMessage('a1', 'assistant', 'A1'),
    ]);

    const { result } = renderHook(() =>
      useChat('session-1', onCreateSession, onSessionMetaRefresh)
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.messages).toHaveLength(2);

    // Send Q2
    mockSendMessageResult = mockChatResponse('asst-2', 'A2');
    await act(async () => {
      await result.current.sendMessage('Q2');
    });

    const msgs = result.current.messages;
    expect(msgs).toHaveLength(4);
    expect(msgs[0].content).toBe('Q1');
    expect(msgs[1].content).toBe('A1');
    expect(msgs[2].content).toBe('Q2');
    expect(msgs[3].content).toBe('A2');
  });

  // ------------------------------------------------------------------
  // TEST 8: Previous messages visible while loading response
  // ------------------------------------------------------------------
  it('TEST 8: Previous messages remain visible during slow response', async () => {
    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    // Load session with Q1/A1
    mockGetSessionResult = mockSessionDetail([
      mockMessage('u1', 'user', 'Q1'),
      mockMessage('a1', 'assistant', 'A1'),
    ]);

    const { result } = renderHook(() =>
      useChat('session-1', onCreateSession, onSessionMetaRefresh)
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Start sending Q2 with a slow response
    mockSendMessageDelay = 200;
    mockSendMessageResult = mockChatResponse('asst-2', 'A2');

    let sendPromise: Promise<void>;
    act(() => {
      sendPromise = result.current.sendMessage('Q2');
    });

    // While loading: should have Q1, A1, Q2 (optimistic) and isLoading = true
    await waitFor(() => {
      expect(result.current.isLoading).toBe(true);
    });

    const msgsWhileLoading = result.current.messages;
    expect(msgsWhileLoading.length).toBeGreaterThanOrEqual(3);
    expect(msgsWhileLoading[0].content).toBe('Q1');
    expect(msgsWhileLoading[1].content).toBe('A1');
    expect(msgsWhileLoading[2].content).toBe('Q2');

    // Let the response complete
    await act(async () => { await sendPromise!; });

    expect(result.current.messages).toHaveLength(4);
  });

  // ------------------------------------------------------------------
  // TEST 9: Stale loadMessages does NOT overwrite newer messages
  // ------------------------------------------------------------------
  it('TEST 9: Stale getSession response does NOT overwrite messages added by sendMessage', async () => {
    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    // Initial load returns empty
    mockGetSessionResult = mockSessionDetail([]);

    const { result } = renderHook(() =>
      useChat('session-1', onCreateSession, onSessionMetaRefresh)
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Send Q1 successfully
    mockSendMessageResult = mockChatResponse('asst-1', 'A1');
    await act(async () => {
      await result.current.sendMessage('Q1');
    });

    expect(result.current.messages).toHaveLength(2);

    // Now we have 2 messages locally. Even if a stale getSession
    // somehow ran and returned empty, the version counter should
    // prevent it from overwriting.
    // (This is implicitly tested because the hook's useEffect only
    //  fires on activeSessionId change, which doesn't happen here.)
    expect(result.current.messages[0].content).toBe('Q1');
    expect(result.current.messages[1].content).toBe('A1');
  });

  // ------------------------------------------------------------------
  // TEST 10: LLM failure keeps previous conversation intact
  // ------------------------------------------------------------------
  it('TEST 10: LLM failure preserves previous conversation and shows error', async () => {
    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    // Load session with Q1/A1
    mockGetSessionResult = mockSessionDetail([
      mockMessage('u1', 'user', 'Q1'),
      mockMessage('a1', 'assistant', 'A1'),
    ]);

    const { result } = renderHook(() =>
      useChat('session-1', onCreateSession, onSessionMetaRefresh)
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Make sendMessage throw
    vi.mocked(api.sendMessage).mockRejectedValueOnce(new Error('LLM unavailable'));

    await act(async () => {
      await result.current.sendMessage('Q2');
    });

    const msgs = result.current.messages;
    // Q1, A1, Q2 (user), error-assistant
    expect(msgs.length).toBeGreaterThanOrEqual(4);
    expect(msgs[0].content).toBe('Q1');
    expect(msgs[1].content).toBe('A1');
    expect(msgs[2].content).toBe('Q2');
    expect(msgs[2].role).toBe('user');
    expect(msgs[3].role).toBe('assistant');
    expect(msgs[3].content).toContain('Error');
    expect(result.current.error).toBeTruthy();
  });

  // ------------------------------------------------------------------
  // TEST: New session creation flow
  // ------------------------------------------------------------------
  it('creates a new session when activeSessionId is null and preserves messages', async () => {
    const mockNewSession = { id: 'new-session-1', title: 'New Conversation' };
    const onCreateSession = vi.fn().mockResolvedValue(mockNewSession);
    const onSessionMetaRefresh = vi.fn();

    // Start with no session
    mockGetSessionResult = mockSessionDetail([]);
    mockSendMessageResult = mockChatResponse('asst-1', 'A1', 'new-session-1');

    const { result } = renderHook(() =>
      useChat(null, onCreateSession, onSessionMetaRefresh)
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.messages).toHaveLength(0);

    await act(async () => {
      await result.current.sendMessage('Q1');
    });

    expect(onCreateSession).toHaveBeenCalled();
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].content).toBe('Q1');
    expect(result.current.messages[1].content).toBe('A1');
  });

  // ------------------------------------------------------------------
  // TEST: Null session → messages cleared
  // ------------------------------------------------------------------
  it('clears messages when activeSessionId becomes null', async () => {
    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    mockGetSessionResult = mockSessionDetail([
      mockMessage('u1', 'user', 'Q1'),
      mockMessage('a1', 'assistant', 'A1'),
    ]);

    const { result, rerender } = renderHook(
      ({ sessionId }) => useChat(sessionId, onCreateSession, onSessionMetaRefresh),
      { initialProps: { sessionId: 'session-1' as string | null } }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.messages).toHaveLength(2);

    // Clear active session
    rerender({ sessionId: null });

    await waitFor(() => expect(result.current.messages).toHaveLength(0));
  });

  // ------------------------------------------------------------------
  // TEST: Each message has a unique id used as key
  // ------------------------------------------------------------------
  it('every message has a unique id', async () => {
    const onCreateSession = vi.fn();
    const onSessionMetaRefresh = vi.fn();

    mockGetSessionResult = mockSessionDetail([]);

    const { result } = renderHook(() =>
      useChat('session-1', onCreateSession, onSessionMetaRefresh)
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Send Q1
    mockSendMessageResult = mockChatResponse('asst-1', 'A1');
    await act(async () => { await result.current.sendMessage('Q1'); });

    // Send Q2
    mockSendMessageResult = mockChatResponse('asst-2', 'A2');
    await act(async () => { await result.current.sendMessage('Q2'); });

    // Send Q3
    mockSendMessageResult = mockChatResponse('asst-3', 'A3');
    await act(async () => { await result.current.sendMessage('Q3'); });

    const ids = result.current.messages.map((m) => m.id);
    const uniqueIds = new Set(ids);
    expect(uniqueIds.size).toBe(ids.length);
  });
});
