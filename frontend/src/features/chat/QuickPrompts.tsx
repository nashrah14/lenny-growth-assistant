import React from 'react';
import { Target, FileText, Layout, TrendingUp } from 'lucide-react';

interface QuickPromptsProps {
  onSelectPrompt: (prompt: string, intent?: 'NORMAL_QA' | 'SHIP30' | 'ARTIFACT') => void;
}

export const QuickPrompts: React.FC<QuickPromptsProps> = ({ onSelectPrompt }) => {
  const prompts = [
    {
      icon: <Target size={18} color="#F59E0B" />,
      title: "Superhuman PMF Engine",
      subtitle: "How did Rahul Vohra measure PMF and reverse-engineer the 40% rule?",
      prompt: "How did Superhuman measure and optimize Product-Market Fit using Rahul Vohra's framework?",
      intent: "NORMAL_QA" as const,
    },
    {
      icon: <FileText size={18} color="#06B6D4" />,
      title: "Ship 30: B2B PLG Loops",
      subtitle: "Write a ~1,250-word essay on Elena Verna's product-led growth mechanics.",
      prompt: "Write a Ship 30 for 30 essay explaining Elena Verna's B2B product-led growth loops and pipeline model.",
      intent: "SHIP30" as const,
    },
    {
      icon: <Layout size={18} color="#10B981" />,
      title: "Interactive CAC/LTV Model",
      subtitle: "Generate an interactive HTML/JS growth calculator artifact.",
      prompt: "Create an interactive HTML and JavaScript CAC payback and LTV growth model calculator component.",
      intent: "ARTIFACT" as const,
    },
    {
      icon: <TrendingUp size={18} color="#A855F7" />,
      title: "Brian Chesky's 11-Star Model",
      subtitle: "How Airbnb designs 11-star experiences beyond customer expectations.",
      prompt: "Explain Brian Chesky's 11-star experience framework and how to apply it to modern software products.",
      intent: "NORMAL_QA" as const,
    },
  ];

  return (
    <div style={{ maxWidth: '800px', margin: '40px auto', padding: '0 20px', textAlign: 'center' }}>
      <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px', letterSpacing: '-0.02em' }}>
        What growth challenge are you tackling today?
      </h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '32px' }}>
        Grounded directly in 300+ episodes of Lenny's Podcast transcripts with zero fluff.
      </p>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px',
          textAlign: 'left',
        }}
      >
        {prompts.map((p, idx) => (
          <div
            key={idx}
            onClick={() => onSelectPrompt(p.prompt, p.intent)}
            className="card-glass"
            style={{
              padding: '16px',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.borderColor = 'var(--accent-amber)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.borderColor = 'var(--border-subtle)';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '6px', borderRadius: '6px' }}>
                {p.icon}
              </div>
              <h3 style={{ fontSize: '14px', fontWeight: 600 }}>{p.title}</h3>
            </div>
            <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              {p.subtitle}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
