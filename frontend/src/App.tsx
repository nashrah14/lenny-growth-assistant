import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './features/auth/LoginPage';
import { SignupPage } from './features/auth/SignupPage';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { ChatContainer } from './features/chat/ChatContainer';
import { ArtifactViewer } from './features/artifacts/ArtifactViewer';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { useSessions } from './hooks/useSessions';
import { useChat } from './hooks/useChat';
import { api } from './api/client';

function MainApp() {
  const { user, logout } = useAuth();
  const [activeProvider, setActiveProvider] = useState<'gemini' | 'ollama'>('gemini');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [systemStatus, setSystemStatus] = useState<string>('healthy');

  const {
    sessions,
    activeSessionId,
    setActiveSessionId,
    createNewSession,
    deleteSession,
    refreshSessions,
  } = useSessions();

  // IMPORTANT: Pass refreshSessions (sidebar-only metadata update) as the
  // onSessionMetaRefresh callback. useChat will call this after a successful
  // send to keep the sidebar session list fresh (updated title/timestamp).
  // It must NOT trigger loadMessages — that would wipe the local optimistic state.
  const {
    messages,
    activeArtifact,
    isArtifactViewerOpen,
    isLoading,
    sendMessage,
    openArtifact,
    toggleArtifactViewer,
    setIsArtifactViewerOpen,
  } = useChat(activeSessionId, createNewSession, refreshSessions);

  // Check health on mount
  useEffect(() => {
    api.getHealth()
      .then((h) => setSystemStatus(h.status))
      .catch(() => setSystemStatus('degraded'));
  }, []);

  const handleSendMessage = (content: string, intent?: 'NORMAL_QA' | 'SHIP30' | 'ARTIFACT') => {
    sendMessage(content, activeProvider, intent);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Header */}
      <Header
        user={user}
        onLogout={logout}
        activeProvider={activeProvider}
        onProviderChange={setActiveProvider}
        hasActiveArtifact={activeArtifact !== null}
        isArtifactViewerOpen={isArtifactViewerOpen}
        onToggleArtifactViewer={toggleArtifactViewer}
        systemStatus={systemStatus}
        onToggleSidebar={() => setIsSidebarCollapsed((prev) => !prev)}
      />

      {/* Main 3-Column Layout */}
      <div className="app-main-layout" style={{ display: 'flex', flex: 1, height: 'calc(100vh - 60px)', overflow: 'hidden' }}>
        {/* Backdrop for mobile drawer */}
        {!isSidebarCollapsed && (
          <div className="sidebar-backdrop" onClick={() => setIsSidebarCollapsed(true)} />
        )}

        {/* Left: Sidebar */}
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={(id) => {
            setActiveSessionId(id);
            setIsSidebarCollapsed(true); // Close sidebar on mobile after selecting chat
          }}
          onNewChat={() => {
            createNewSession();
            setIsSidebarCollapsed(true); // Close sidebar on mobile after creating new chat
          }}
          onDeleteSession={deleteSession}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        />

        {/* Center: Main Chat Area */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
          <ChatContainer
            messages={messages}
            isLoading={isLoading}
            onSendMessage={handleSendMessage}
            onOpenArtifact={openArtifact}
          />
        </main>

        {/* Right: In-App Sandboxed Artifact Viewer */}
        {isArtifactViewerOpen && (
          <ArtifactViewer
            artifact={activeArtifact}
            onClose={() => setIsArtifactViewerOpen(false)}
          />
        )}
      </div>
    </div>
  );
}

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const [authView, setAuthView] = useState<'login' | 'signup'>('login');

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          width: '100vw',
          background: 'var(--bg-app)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
        }}
      >
        <LoadingSpinner size="lg" />
        <div style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Connecting to Lenny Growth Assistant...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (authView === 'signup') {
      return <SignupPage onSwitchToLogin={() => setAuthView('login')} />;
    }
    return <LoginPage onSwitchToSignup={() => setAuthView('signup')} />;
  }

  return <MainApp />;
}

export function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
