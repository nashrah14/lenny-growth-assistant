import React, { useState, useRef, useEffect } from 'react';
import { Send, FileText, Layout, MessageSquare } from 'lucide-react';

interface ComposerProps {
  onSendMessage: (content: string, intent?: 'NORMAL_QA' | 'SHIP30' | 'ARTIFACT') => void;
  isLoading: boolean;
}

export const Composer: React.FC<ComposerProps> = ({ onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');
  const [selectedIntent, setSelectedIntent] = useState<'NORMAL_QA' | 'SHIP30' | 'ARTIFACT'>('NORMAL_QA');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    onSendMessage(input.trim(), selectedIntent);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      style={{
        padding: '16px 24px 20px 24px',
        background: 'linear-gradient(to top, var(--bg-app) 80%, transparent)',
      }}
    >
      <div
        style={{
          maxWidth: '840px',
          margin: '0 auto',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          padding: '10px 14px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)',
        }}
      >
        {/* Intent Chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
          <button
            type="button"
            onClick={() => setSelectedIntent('NORMAL_QA')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '11.5px',
              fontWeight: 500,
              background: selectedIntent === 'NORMAL_QA' ? 'rgba(245, 158, 11, 0.15)' : 'transparent',
              color: selectedIntent === 'NORMAL_QA' ? 'var(--accent-amber)' : 'var(--text-muted)',
              border: selectedIntent === 'NORMAL_QA' ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid transparent',
            }}
          >
            <MessageSquare size={12} />
            Standard Q&A
          </button>

          <button
            type="button"
            onClick={() => setSelectedIntent('SHIP30')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '11.5px',
              fontWeight: 500,
              background: selectedIntent === 'SHIP30' ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
              color: selectedIntent === 'SHIP30' ? 'var(--accent-cyan)' : 'var(--text-muted)',
              border: selectedIntent === 'SHIP30' ? '1px solid rgba(6, 182, 212, 0.4)' : '1px solid transparent',
            }}
          >
            <FileText size={12} />
            Ship 30 Essay (~1250w)
          </button>

          <button
            type="button"
            onClick={() => setSelectedIntent('ARTIFACT')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '11.5px',
              fontWeight: 500,
              background: selectedIntent === 'ARTIFACT' ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
              color: selectedIntent === 'ARTIFACT' ? 'var(--accent-green)' : 'var(--text-muted)',
              border: selectedIntent === 'ARTIFACT' ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid transparent',
            }}
          >
            <Layout size={12} />
            Generate Artifact
          </button>
        </div>

        {/* Input Textarea & Send Button */}
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '10px' }}>
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              selectedIntent === 'SHIP30'
                ? 'Enter topic for a grounded Ship 30 essay...'
                : selectedIntent === 'ARTIFACT'
                ? 'Describe the HTML/JS calculator or Markdown artifact to build...'
                : "Ask anything about Lenny's 300+ podcast episodes..."
            }
            disabled={isLoading}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              color: '#F8FAFC',
              fontSize: '14.5px',
              resize: 'none',
              padding: '6px 4px',
              maxHeight: '180px',
              outline: 'none',
            }}
          />

          <button
            onClick={() => handleSubmit()}
            disabled={!input.trim() || isLoading}
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              background: input.trim() && !isLoading ? 'var(--accent-amber)' : 'rgba(255, 255, 255, 0.08)',
              color: input.trim() && !isLoading ? '#000' : 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              cursor: input.trim() && !isLoading ? 'pointer' : 'not-allowed',
            }}
          >
            <Send size={15} />
          </button>
        </div>

        {/* Shortcuts footer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
          <span>Enter to send, Shift + Enter for new line</span>
          <span>Strictly Grounded in Verified Transcripts</span>
        </div>
      </div>
    </div>
  );
};
