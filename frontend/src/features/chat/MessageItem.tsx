import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, Copy, Check, Layers, Cpu, Clock } from 'lucide-react';
import { Message, SourceCitation, Artifact } from '../../types';
import { SourceBadges } from './SourceBadges';

interface MessageItemProps {
  message: Message;
  onSelectSource: (source: SourceCitation) => void;
  onOpenArtifact: (artifact: Artifact) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  onSelectSource,
  onOpenArtifact,
}) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: '12px',
        padding: '20px 24px',
        background: isUser ? 'rgba(255, 255, 255, 0.02)' : 'transparent',
        borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: '32px',
          height: '32px',
          borderRadius: '8px',
          background: isUser ? '#334155' : 'linear-gradient(135deg, #F59E0B, #D97706)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: isUser ? '#F8FAFC' : '#000',
          fontWeight: 'bold',
          flexShrink: 0,
          marginTop: '2px',
        }}
      >
        {isUser ? <User size={16} /> : <Bot size={18} />}
      </div>

      {/* Content Body */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Header meta */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: isUser ? '#94A3B8' : '#F8FAFC' }}>
              {isUser ? 'You' : 'The Lenny Growth Assistant'}
            </span>
            {message.intent_type && message.intent_type !== 'NORMAL_QA' && (
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 600,
                  background: message.intent_type === 'SHIP30' ? 'rgba(6, 182, 212, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                  color: message.intent_type === 'SHIP30' ? 'var(--accent-cyan)' : 'var(--accent-green)',
                  padding: '1px 6px',
                  borderRadius: '4px',
                  border: `1px solid ${message.intent_type === 'SHIP30' ? 'rgba(6, 182, 212, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                }}
              >
                {message.intent_type}
              </span>
            )}
          </div>

          <button
            onClick={handleCopy}
            title="Copy message"
            style={{
              background: 'transparent',
              color: '#64748B',
              padding: '4px',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '11px',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#F8FAFC')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#64748B')}
          >
            {copied ? <Check size={13} color="#10B981" /> : <Copy size={13} />}
          </button>
        </div>

        {/* Message Content */}
        <div className="markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Generated Artifact Card (if attached to this message) */}
        {message.artifacts && message.artifacts.length > 0 && (
          <div style={{ marginTop: '14px' }}>
            {message.artifacts.map((art) => (
              <div
                key={art.id}
                onClick={() => onOpenArtifact(art)}
                className="card-glass"
                style={{
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                  background: 'rgba(245, 158, 11, 0.06)',
                  borderColor: 'rgba(245, 158, 11, 0.3)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(245, 158, 11, 0.12)';
                  e.currentTarget.style.borderColor = 'var(--accent-amber)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(245, 158, 11, 0.06)';
                  e.currentTarget.style.borderColor = 'rgba(245, 158, 11, 0.3)';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ background: 'rgba(245, 158, 11, 0.2)', padding: '6px', borderRadius: '6px' }}>
                    <Layers size={16} color="var(--accent-amber)" />
                  </div>
                  <div>
                    <div style={{ fontSize: '13.5px', fontWeight: 600, color: '#F8FAFC' }}>
                      {art.title}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      Click to open in Artifact Viewer ({art.artifact_type.toUpperCase()})
                    </div>
                  </div>
                </div>

                <span style={{ fontSize: '12px', color: 'var(--accent-amber)', fontWeight: 500 }}>
                  Open Viewer →
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Grounded Source Citations */}
        {message.sources && message.sources.length > 0 && (
          <SourceBadges sources={message.sources} onSelectSource={onSelectSource} />
        )}

        {/* Assistant Metadata Footer */}
        {!isUser && message.model_provider && (
          <div
            style={{
              marginTop: '10px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '11px',
              color: 'var(--text-muted)',
            }}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Cpu size={12} />
              {message.model_provider} ({message.model_name})
            </span>
            {message.latency_ms && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={12} />
                {message.latency_ms}ms
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
