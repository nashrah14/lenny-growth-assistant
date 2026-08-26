import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { X, Copy, Check, Download, Eye, Code, Layers, ShieldCheck } from 'lucide-react';
import { Artifact } from '../../types';
import { SandboxedFrame } from './SandboxedFrame';

interface ArtifactViewerProps {
  artifact: Artifact | null;
  onClose: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({ artifact, onClose }) => {
  const [activeTab, setActiveTab] = useState<'preview' | 'code'>('preview');
  const [copied, setCopied] = useState(false);
  const [showSecurityInfo, setShowSecurityInfo] = useState(false);

  if (!artifact) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.raw_content || artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const ext = artifact.artifact_type === 'html' ? 'html' : 'md';
    const blob = new Blob([artifact.raw_content || artifact.content], {
      type: artifact.artifact_type === 'html' ? 'text/html' : 'text/markdown',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifact.title.toLowerCase().replace(/[^a-z0-9]/g, '-')}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <aside
      style={{
        width: '560px',
        maxWidth: '50vw',
        background: '#0D131F',
        borderLeft: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        flexShrink: 0,
        zIndex: 20,
        position: 'relative',
      }}
    >
      {/* Viewer Header */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, flex: 1 }}>
          <div style={{ background: 'rgba(245, 158, 11, 0.15)', padding: '5px', borderRadius: '6px' }}>
            <Layers size={15} color="var(--accent-amber)" />
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <h3
              style={{
                fontSize: '13.5px',
                fontWeight: 600,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {artifact.title}
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
              <span>{artifact.artifact_type.toUpperCase()}</span>
              <span>•</span>
              <button
                onClick={() => setShowSecurityInfo((prev) => !prev)}
                title="Click to view Security & Isolation Details"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px',
                  color: 'var(--accent-green)',
                  background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.25)',
                  padding: '1px 6px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '11px',
                }}
              >
                <ShieldCheck size={11} />
                Sanitized Sandbox {showSecurityInfo ? '▲' : '▼'}
              </button>
            </div>
          </div>
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

      {/* Security & Isolation Inspector Panel */}
      {showSecurityInfo && (
        <div
          style={{
            padding: '12px 16px',
            background: '#0B111E',
            borderBottom: '1px solid var(--border-subtle)',
            fontSize: '11.5px',
            color: '#CBD5E1',
            lineHeight: '1.45',
          }}
        >
          <div style={{ fontWeight: 600, color: '#F8FAFC', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <ShieldCheck size={13} color="var(--accent-green)" />
            Security & Isolation Specification (Untrusted HTML Model)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '6px' }}>
            <div style={{ background: 'rgba(16, 185, 129, 0.08)', padding: '6px 8px', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <strong style={{ color: 'var(--accent-green)' }}>✓ Permitted:</strong>
              <ul style={{ margin: '2px 0 0 14px', padding: 0 }}>
                <li>HTML5 layout & tables</li>
                <li>Forms & interactive inputs</li>
                <li>Local calculation scripts</li>
                <li>SVG & Canvas graphics</li>
              </ul>
            </div>
            <div style={{ background: 'rgba(239, 68, 68, 0.08)', padding: '6px 8px', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
              <strong style={{ color: '#EF4444' }}>✕ Blocked:</strong>
              <ul style={{ margin: '2px 0 0 14px', padding: 0 }}>
                <li>Parent DOM & Cookie access (Null Origin)</li>
                <li>Top-level window navigation</li>
                <li>Outbound fetch / network requests (CSP)</li>
                <li>External plugins & nested iframes</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Tab bar & Actions */}
      <div
        style={{
          padding: '8px 16px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(0, 0, 0, 0.2)',
        }}
      >
        {/* Tabs: Preview / Code */}
        <div
          style={{
            display: 'flex',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            padding: '2px',
            gap: '2px',
          }}
        >
          <button
            onClick={() => setActiveTab('preview')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 10px',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 500,
              background: activeTab === 'preview' ? 'var(--bg-card-hover)' : 'transparent',
              color: activeTab === 'preview' ? '#F8FAFC' : '#94A3B8',
            }}
          >
            <Eye size={13} />
            Live Preview
          </button>
          <button
            onClick={() => setActiveTab('code')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 10px',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 500,
              background: activeTab === 'code' ? 'var(--bg-card-hover)' : 'transparent',
              color: activeTab === 'code' ? '#F8FAFC' : '#94A3B8',
            }}
          >
            <Code size={13} />
            Raw Source
          </button>
        </div>

        {/* Action Buttons: Copy & Download */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={handleCopy}
            title="Copy code"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              padding: '4px 8px',
              borderRadius: '6px',
              color: '#F8FAFC',
              fontSize: '11.5px',
            }}
          >
            {copied ? <Check size={13} color="#10B981" /> : <Copy size={13} />}
            {copied ? 'Copied' : 'Copy'}
          </button>

          <button
            onClick={handleDownload}
            title="Download artifact"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              padding: '4px 8px',
              borderRadius: '6px',
              color: '#F8FAFC',
              fontSize: '11.5px',
            }}
          >
            <Download size={13} />
            Export
          </button>
        </div>
      </div>

      {/* Main View Area */}
      <div style={{ flex: 1, overflow: 'hidden', padding: '16px', position: 'relative' }}>
        {activeTab === 'preview' ? (
          artifact.artifact_type === 'html' ? (
            <SandboxedFrame content={artifact.content} title={artifact.title} />
          ) : (
            <div
              className="markdown-body"
              style={{
                height: '100%',
                overflowY: 'auto',
                padding: '16px',
                background: 'var(--bg-card)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {artifact.content}
              </ReactMarkdown>
            </div>
          )
        ) : (
          <pre
            style={{
              height: '100%',
              overflowY: 'auto',
              padding: '14px',
              background: '#090D14',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              fontSize: '12.5px',
              color: '#F1F5F9',
              lineHeight: '1.5',
              whiteSpace: 'pre-wrap',
            }}
          >
            <code>{artifact.raw_content || artifact.content}</code>
          </pre>
        )}
      </div>
    </aside>
  );
};
