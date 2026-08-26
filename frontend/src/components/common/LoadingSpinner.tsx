import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', text }) => {
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
      <div
        style={{
          width: size === 'sm' ? '14px' : size === 'md' ? '20px' : '28px',
          height: size === 'sm' ? '14px' : size === 'md' ? '20px' : '28px',
          borderRadius: '50%',
          border: '2px solid rgba(245, 158, 11, 0.2)',
          borderTopColor: '#F59E0B',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      {text && <span style={{ fontSize: '13px', color: '#94A3B8' }}>{text}</span>}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
