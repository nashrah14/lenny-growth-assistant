import React from 'react';
import { X, ExternalLink, User, Award } from 'lucide-react';
import { SourceCitation } from '../../types';

interface SourceDrawerProps {
  source: SourceCitation | null;
  onClose: () => void;
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({ source, onClose }) => {
  if (!source) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '420px',
        maxWidth: '90vw',
        background: '#0D131F',
        borderLeft: '1px solid var(--border-subtle)',
        boxShadow: '-8px 0 24px rgba(0, 0, 0, 0.6)',
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        animation: 'slideIn 0.2s ease',
      }}
    >
      {/* Drawer Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 600,
              background: 'rgba(245, 158, 11, 0.15)',
              color: 'var(--accent-amber)',
              padding: '2px 8px',
              borderRadius: '4px',
            }}
          >
            Rank #{source.rank}
          </span>
          <h3 style={{ fontSize: '14px', fontWeight: 600 }}>Grounding Evidence</h3>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            color: '#94A3B8',
            padding: '4px',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#fff')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#94A3B8')}
        >
          <X size={18} />
        </button>
      </div>

      {/* Drawer Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Episode Title Card */}
        <div className="card-glass" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>
            Episode
          </div>
          <h4 style={{ fontSize: '15px', fontWeight: 600, lineHeight: 1.4, marginBottom: '8px' }}>
            {source.source_title}
          </h4>

          {source.source_url && (
            <a
              href={source.source_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                color: 'var(--accent-cyan)',
                fontSize: '12.5px',
                textDecoration: 'none',
                marginTop: '4px',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
              onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
            >
              <span>Watch on YouTube / Listen</span>
              <ExternalLink size={13} />
            </a>
          )}
        </div>

        {/* Metadata stats */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div className="card-glass" style={{ padding: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '11px', marginBottom: '4px' }}>
              <User size={13} />
              <span>Speaker</span>
            </div>
            <div style={{ fontSize: '13px', fontWeight: 500 }}>
              {source.speaker || 'Lenny Rachitsky'}
            </div>
          </div>

          <div className="card-glass" style={{ padding: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '11px', marginBottom: '4px' }}>
              <Award size={13} />
              <span>Match Score</span>
            </div>
            <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--accent-green)' }}>
              {source.relevance_score ? source.relevance_score.toFixed(4) : 'High'}
            </div>
          </div>
        </div>

        {/* Transcript Snippet */}
        <div className="card-glass" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>
            Verbatim Transcript Excerpt
          </div>
          <div
            style={{
              fontSize: '13.5px',
              lineHeight: '1.6',
              color: '#CBD5E1',
              background: 'rgba(0, 0, 0, 0.25)',
              padding: '12px',
              borderRadius: '6px',
              borderLeft: '3px solid var(--accent-amber)',
              whiteSpace: 'pre-wrap',
            }}
          >
            "{source.snippet}"
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}</style>
    </div>
  );
};
