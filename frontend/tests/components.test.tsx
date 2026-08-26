import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Header } from '../src/components/layout/Header';
import { QuickPrompts } from '../src/features/chat/QuickPrompts';
import { SandboxedFrame } from '../src/features/artifacts/SandboxedFrame';
import { LoginPage } from '../src/features/auth/LoginPage';
import { SignupPage } from '../src/features/auth/SignupPage';
import { AuthProvider } from '../src/context/AuthContext';

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  Sparkles: () => <span>Sparkles</span>,
  Bot: () => <span>Bot</span>,
  Cpu: () => <span>Cpu</span>,
  Layers: () => <span>Layers</span>,
  ExternalLink: () => <span>ExternalLink</span>,
  Target: () => <span>Target</span>,
  FileText: () => <span>FileText</span>,
  Layout: () => <span>Layout</span>,
  TrendingUp: () => <span>TrendingUp</span>,
  X: () => <span>X</span>,
  Copy: () => <span>Copy</span>,
  Check: () => <span>Check</span>,
  Download: () => <span>Download</span>,
  Eye: () => <span>Eye</span>,
  EyeOff: () => <span>EyeOff</span>,
  Code: () => <span>Code</span>,
  ShieldCheck: () => <span>ShieldCheck</span>,
  Plus: () => <span>Plus</span>,
  MessageSquare: () => <span>MessageSquare</span>,
  Trash2: () => <span>Trash2</span>,
  ChevronLeft: () => <span>ChevronLeft</span>,
  ChevronRight: () => <span>ChevronRight</span>,
  Mic: () => <span>Mic</span>,
  Send: () => <span>Send</span>,
  BookOpen: () => <span>BookOpen</span>,
  User: () => <span>User</span>,
  Award: () => <span>Award</span>,
  Mail: () => <span>Mail</span>,
  Lock: () => <span>Lock</span>,
  AlertCircle: () => <span>AlertCircle</span>,
  CheckCircle2: () => <span>CheckCircle2</span>,
  LogOut: () => <span>LogOut</span>,
}));

describe('Frontend Component & Auth Tests', () => {
  it('Header renders user profile and switches models', () => {
    const handleProviderChange = vi.fn();
    const handleLogout = vi.fn();
    const mockUser = {
      id: '123',
      email: 'elena@growth.com',
      name: 'Elena Verna',
      is_active: true,
      created_at: new Date().toISOString(),
    };

    const { getByText } = render(
      <Header
        user={mockUser}
        onLogout={handleLogout}
        activeProvider="gemini"
        onProviderChange={handleProviderChange}
        hasActiveArtifact={false}
        isArtifactViewerOpen={false}
        onToggleArtifactViewer={() => {}}
        systemStatus="healthy"
      />
    );

    expect(getByText(/The Lenny Growth Assistant/i)).toBeDefined();
    expect(getByText('Elena Verna')).toBeDefined();

    const ollamaBtn = getByText('Ollama');
    fireEvent.click(ollamaBtn);
    expect(handleProviderChange).toHaveBeenCalledWith('ollama');

    const logoutBtn = getByText('Logout');
    fireEvent.click(logoutBtn);
    expect(handleLogout).toHaveBeenCalled();
  });

  it('LoginPage renders fields and submit button', () => {
    const handleSwitch = vi.fn();
    const { getByPlaceholderText, getByText } = render(
      <AuthProvider>
        <LoginPage onSwitchToSignup={handleSwitch} />
      </AuthProvider>
    );

    expect(getByPlaceholderText('you@company.com')).toBeDefined();
    expect(getByText('Sign In')).toBeDefined();

    const createAccBtn = getByText('Create an account');
    fireEvent.click(createAccBtn);
    expect(handleSwitch).toHaveBeenCalled();
  });

  it('SignupPage renders name, email, password and strength meter', () => {
    const handleSwitch = vi.fn();
    const { getByPlaceholderText, getByText } = render(
      <AuthProvider>
        <SignupPage onSwitchToLogin={handleSwitch} />
      </AuthProvider>
    );

    expect(getByPlaceholderText('Elena Verna')).toBeDefined();
    expect(getByPlaceholderText('elena@growth.com')).toBeDefined();
    expect(getByText('Create Account')).toBeDefined();
  });

  it('QuickPrompts renders 4 cards and triggers callback', () => {
    const handleSelectPrompt = vi.fn();
    const { getByText } = render(<QuickPrompts onSelectPrompt={handleSelectPrompt} />);

    expect(getByText(/Superhuman PMF Engine/i)).toBeDefined();
    expect(getByText(/Ship 30: B2B PLG Loops/i)).toBeDefined();

    fireEvent.click(getByText(/Superhuman PMF Engine/i));
    expect(handleSelectPrompt).toHaveBeenCalled();
  });

  it('SandboxedFrame sets sandbox allow-scripts attribute', () => {
    const { container } = render(
      <SandboxedFrame content="<div>Test Artifact</div>" title="Test Title" />
    );

    const iframe = container.querySelector('iframe');
    expect(iframe).not.toBeNull();
    expect(iframe?.getAttribute('sandbox')).toBe('allow-scripts');
  });
});
