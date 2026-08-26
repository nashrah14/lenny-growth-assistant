import React from 'react';
import { Plus, MessageSquare, Trash2, ChevronLeft, ChevronRight, Mic } from 'lucide-react';
import { Session } from '../../types';

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  isCollapsed,
  onToggleCollapse,
}) => {
  return (
    <aside
      className={`sidebar-responsive ${isCollapsed ? 'collapsed' : ''}`}
      style={{
        width: isCollapsed ? '60px' : '260px',
        background: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        transition: 'width 0.2s ease',
        flexShrink: 0,
        position: 'relative',
      }}
    >
      {/* Top action: New Chat */}
      <div style={{ padding: '12px' }}>
        <button
          onClick={onNewChat}
          style={{
            width: '100%',
            height: '38px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            color: '#F8FAFC',
            display: 'flex',
            alignItems: 'center',
            justifyContent: isCollapsed ? 'center' : 'flex-start',
            padding: isCollapsed ? '0' : '0 12px',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 500,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-amber)')}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
        >
          <Plus size={16} color="var(--accent-amber)" />
          {!isCollapsed && <span>New Chat</span>}
        </button>
      </div>

      {/* Sessions list */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0 8px 12px 8px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}
      >
        {!isCollapsed && (
          <div
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              padding: '8px 8px 4px 8px',
            }}
          >
            Conversations
          </div>
        )}

        {sessions.map((session) => {
          const isActive = session.id === activeSessionId;
          return (
            <div
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '8px 10px',
                borderRadius: '6px',
                cursor: 'pointer',
                background: isActive ? 'var(--bg-card-hover)' : 'transparent',
                border: isActive ? '1px solid var(--border-hover)' : '1px solid transparent',
                color: isActive ? '#F8FAFC' : '#94A3B8',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.background = 'transparent';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, flex: 1 }}>
                <MessageSquare size={14} color={isActive ? 'var(--accent-amber)' : '#64748B'} style={{ flexShrink: 0 }} />
                {!isCollapsed && (
                  <span
                    style={{
                      fontSize: '13px',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {session.title || 'Conversation'}
                  </span>
                )}
              </div>

              {!isCollapsed && (
                <button
                  onClick={(e) => onDeleteSession(session.id, e)}
                  title="Delete Session"
                  style={{
                    background: 'transparent',
                    color: '#64748B',
                    padding: '2px',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = '#EF4444')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = '#64748B')}
                >
                  <Trash2 size={13} />
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Collapse Toggle Footer */}
      <div
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: isCollapsed ? 'center' : 'space-between',
        }}
      >
        {!isCollapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
            <Mic size={13} color="var(--accent-amber)" />
            <span>Lenny's Knowledge Base</span>
          </div>
        )}
        <button
          onClick={onToggleCollapse}
          style={{
            background: 'transparent',
            color: '#94A3B8',
            padding: '4px',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </aside>
  );
};
