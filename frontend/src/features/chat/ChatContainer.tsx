import React, { useRef, useEffect, useState } from 'react';
import { Message, SourceCitation, Artifact } from '../../types';
import { MessageItem } from './MessageItem';
import { QuickPrompts } from './QuickPrompts';
import { Composer } from './Composer';
import { SourceDrawer } from './SourceDrawer';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

interface ChatContainerProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (content: string, intent?: 'NORMAL_QA' | 'SHIP30' | 'ARTIFACT') => void;
  onOpenArtifact: (artifact: Artifact) => void;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onOpenArtifact,
}) => {
  const [selectedSource, setSelectedSource] = useState<SourceCitation | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Messages Scroll Area */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {messages.length === 0 ? (
          <QuickPrompts onSelectPrompt={onSendMessage} />
        ) : (
          <div style={{ paddingBottom: '20px' }}>
            {messages.map((msg) => (
              <MessageItem
                key={msg.id}
                message={msg}
                onSelectSource={(src) => setSelectedSource(src)}
                onOpenArtifact={onOpenArtifact}
              />
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div
                style={{
                  padding: '20px 24px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                }}
              >
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, #F59E0B, #D97706)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <LoadingSpinner size="sm" />
                </div>
                <div style={{ fontSize: '13.5px', color: 'var(--text-secondary)' }}>
                  Searching 300+ transcripts (Dense + BM25), reranking, and synthesizing response...
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Composer at Bottom */}
      <Composer onSendMessage={onSendMessage} isLoading={isLoading} />

      {/* Grounded Evidence Drawer */}
      <SourceDrawer
        source={selectedSource}
        onClose={() => setSelectedSource(null)}
      />
    </div>
  );
};
