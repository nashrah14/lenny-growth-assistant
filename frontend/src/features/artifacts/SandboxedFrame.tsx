import React from 'react';

interface SandboxedFrameProps {
  content: string;
  title: string;
}

export const SandboxedFrame: React.FC<SandboxedFrameProps> = ({ content, title }) => {
  return (
    <iframe
      srcDoc={content}
      title={title}
      sandbox="allow-scripts"
      style={{
        width: '100%',
        height: '100%',
        border: 'none',
        background: '#0F172A',
        borderRadius: '8px',
      }}
    />
  );
};
