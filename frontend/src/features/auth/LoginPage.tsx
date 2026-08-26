import React, { useState } from 'react';
import { Sparkles, Mail, Lock, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

interface LoginPageProps {
  onSwitchToSignup: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onSwitchToSignup }) => {
  const { login, error, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email.trim()) {
      setLocalError('Please enter your email address.');
      return;
    }
    if (!password) {
      setLocalError('Please enter your password.');
      return;
    }

    try {
      setIsSubmitting(true);
      await login({ email: email.trim(), password });
    } catch (err: any) {
      setLocalError(err.message || 'Invalid email or password.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const displayError = localError || error;

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100vw',
        background: 'radial-gradient(ellipse at 50% 20%, #172338 0%, #0B0F17 70%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
    >
      <div
        className="card-glass"
        style={{
          width: '100%',
          maxWidth: '420px',
          padding: '36px 32px',
          background: 'rgba(19, 27, 42, 0.85)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #F59E0B, #D97706)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#000',
              marginBottom: '14px',
              boxShadow: '0 0 20px rgba(245, 158, 11, 0.4)',
            }}
          >
            <Sparkles size={22} />
          </div>
          <h2 style={{ fontSize: '22px', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: '6px' }}>
            Welcome Back
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px' }}>
            Sign in to access Lenny's Podcast Growth Assistant
          </p>
        </div>

        {/* Error Alert */}
        {displayError && (
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              padding: '10px 14px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              color: '#FCA5A5',
              fontSize: '13px',
            }}
          >
            <AlertCircle size={16} color="#EF4444" style={{ flexShrink: 0 }} />
            <span>{displayError}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Email field */}
          <div>
            <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Email Address
            </label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <div style={{ position: 'absolute', left: '12px', color: 'var(--text-muted)' }}>
                <Mail size={16} />
              </div>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                style={{
                  width: '100%',
                  height: '42px',
                  paddingLeft: '38px',
                  paddingRight: '12px',
                  fontSize: '14px',
                }}
              />
            </div>
          </div>

          {/* Password field */}
          <div>
            <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Password
            </label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <div style={{ position: 'absolute', left: '12px', color: 'var(--text-muted)' }}>
                <Lock size={16} />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: '100%',
                  height: '42px',
                  paddingLeft: '38px',
                  paddingRight: '40px',
                  fontSize: '14px',
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  background: 'transparent',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              height: '42px',
              background: 'linear-gradient(135deg, #F59E0B, #D97706)',
              color: '#000',
              fontWeight: 600,
              fontSize: '14px',
              borderRadius: '8px',
              marginTop: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(245, 158, 11, 0.3)',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
            }}
          >
            {isSubmitting ? <LoadingSpinner size="sm" /> : <span>Sign In</span>}
          </button>
        </form>

        {/* Footer switch */}
        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '13px', color: 'var(--text-secondary)' }}>
          Don't have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToSignup}
            style={{
              background: 'transparent',
              color: 'var(--accent-amber)',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Create an account
          </button>
        </div>
      </div>
    </div>
  );
};
