import React from 'react';
import { BookOpen } from 'lucide-react';
import { SourceCitation } from '../../types';

interface SourceBadgesProps {
  sources: SourceCitation[];
  onSelectSource: (source: SourceCitation) => void;
}

export const SourceBadges: React.FC<SourceBadgesProps> = ({ sources, onSelectSource }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '5px' }}>
        <BookOpen size={12} color="var(--accent-amber)" />
        <span>Grounded Sources ({sources.length})</span>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
        {sources.map((src, idx) => (
          <button
            key={src.chunk_id || idx}
            onClick={() => onSelectSource(src)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle)',
              padding: '4px 10px',
              borderRadius: '12px',
              fontSize: '12px',
              color: '#CBD5E1',
              transition: 'all 0.15s ease',
              maxWidth: '280px',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(245, 158, 11, 0.12)';
              e.currentTarget.style.borderColor = 'rgba(245, 158, 11, 0.4)';
              e.currentTarget.style.color = '#F8FAFC';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
              e.currentTarget.style.borderColor = 'var(--border-subtle)';
              e.currentTarget.style.color = '#CBD5E1';
            }}
          >
            <span style={{ color: 'var(--accent-amber)', fontWeight: 600, fontSize: '11px' }}>
              [{src.rank}]
            </span>
            <span
              style={{
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {src.speaker ? `${src.speaker} - ` : ''}{src.source_title}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};
