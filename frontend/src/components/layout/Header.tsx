import React from 'react';
import { Sparkles, Bot, Cpu, Layers, LogOut, User as UserIcon } from 'lucide-react';
import { User } from '../../types';

interface HeaderProps {
  user?: User | null;
  onLogout?: () => void;
  activeProvider: 'gemini' | 'ollama';
  onProviderChange: (provider: 'gemini' | 'ollama') => void;
  hasActiveArtifact: boolean;
  isArtifactViewerOpen: boolean;
  onToggleArtifactViewer: () => void;
  systemStatus: string;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  onLogout,
  activeProvider,
  onProviderChange,
  hasActiveArtifact,
  isArtifactViewerOpen,
  onToggleArtifactViewer,
  systemStatus,
}) => {
  return (
    <header
      style={{
        height: '60px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--bg-app)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        flexShrink: 0,
        zIndex: 10,
      }}
    >
      {/* Brand & Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #F59E0B, #D97706)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#000',
            fontWeight: 'bold',
            boxShadow: '0 0 12px rgba(245, 158, 11, 0.3)',
          }}
        >
          <Sparkles size={18} />
        </div>
        <div>
          <h1 style={{ fontSize: '15px', fontWeight: 600, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '6px' }}>
            The Lenny Growth Assistant
            <span
              style={{
                fontSize: '10px',
                background: 'rgba(245, 158, 11, 0.15)',
                color: 'var(--accent-amber)',
                padding: '2px 6px',
                borderRadius: '4px',
                fontWeight: 600,
                border: '1px solid rgba(245, 158, 11, 0.3)',
              }}
            >
              300+ EPS
            </span>
          </h1>
        </div>
      </div>

      {/* Center / Right Controls: Model Selector, Artifact Toggle, User Profile & Logout */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Model Switcher */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '2px',
            gap: '2px',
          }}
        >
          <button
            onClick={() => onProviderChange('gemini')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '12.5px',
              fontWeight: 500,
              background: activeProvider === 'gemini' ? 'var(--bg-card-hover)' : 'transparent',
              color: activeProvider === 'gemini' ? '#F8FAFC' : '#94A3B8',
              border: activeProvider === 'gemini' ? '1px solid var(--border-hover)' : '1px solid transparent',
            }}
          >
            <Bot size={14} color={activeProvider === 'gemini' ? '#F59E0B' : '#94A3B8'} />
            Gemini
          </button>
          <button
            onClick={() => onProviderChange('ollama')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '12.5px',
              fontWeight: 500,
              background: activeProvider === 'ollama' ? 'var(--bg-card-hover)' : 'transparent',
              color: activeProvider === 'ollama' ? '#F8FAFC' : '#94A3B8',
              border: activeProvider === 'ollama' ? '1px solid var(--border-hover)' : '1px solid transparent',
            }}
          >
            <Cpu size={14} color={activeProvider === 'ollama' ? '#06B6D4' : '#94A3B8'} />
            Ollama
          </button>
        </div>

        {/* Artifact Panel Toggle Button */}
        {hasActiveArtifact && (
          <button
            onClick={onToggleArtifactViewer}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              fontSize: '12.5px',
              fontWeight: 500,
              background: isArtifactViewerOpen ? 'rgba(245, 158, 11, 0.15)' : 'var(--bg-card)',
              color: isArtifactViewerOpen ? 'var(--accent-amber)' : '#F8FAFC',
              border: isArtifactViewerOpen ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid var(--border-subtle)',
            }}
          >
            <Layers size={14} />
            {isArtifactViewerOpen ? 'Hide Artifact' : 'View Artifact'}
          </button>
        )}

        {/* User Profile & Logout */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '6px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '4px 10px',
                fontSize: '12.5px',
                color: '#E2E8F0',
              }}
            >
              <UserIcon size={14} color="var(--accent-amber)" />
              <span style={{ fontWeight: 500, maxWidth: '120px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.name}
              </span>
            </div>

            {onLogout && (
              <button
                onClick={onLogout}
                title="Log Out"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  padding: '6px 10px',
                  color: 'var(--text-muted)',
                  fontSize: '12px',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = '#EF4444';
                  e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = 'var(--text-muted)';
                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                }}
              >
                <LogOut size={14} />
                <span>Logout</span>
              </button>
            )}
          </div>
        )}

        {/* System Health Dot */}
        <div
          title={`Status: ${systemStatus}`}
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: systemStatus === 'healthy' ? 'var(--accent-green)' : 'var(--accent-amber)',
            boxShadow: `0 0 8px ${systemStatus === 'healthy' ? 'rgba(16, 185, 129, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`,
          }}
        />
      </div>
    </header>
  );
};
