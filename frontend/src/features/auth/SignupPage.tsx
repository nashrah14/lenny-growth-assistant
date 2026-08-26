import React, { useState } from 'react';
import { Sparkles, User as UserIcon, Mail, Lock, Eye, EyeOff, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

interface SignupPageProps {
  onSwitchToLogin: () => void;
}

export const SignupPage: React.FC<SignupPageProps> = ({ onSwitchToLogin }) => {
  const { signup, error, clearError } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  // Compute password strength
  const getPasswordStrength = () => {
    if (!password) return { score: 0, label: 'None', color: 'transparent' };
    let score = 0;
    if (password.length >= 8) score += 1;
    if (/[A-Z]/.test(password) || /[a-z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;

    if (score <= 1) return { score: 1, label: 'Weak', color: '#EF4444' };
    if (score === 2 || score === 3) return { score: 2, label: 'Medium', color: '#F59E0B' };
    return { score: 3, label: 'Strong', color: '#10B981' };
  };

  const strength = getPasswordStrength();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!name.trim()) {
      setLocalError('Please enter your full name.');
      return;
    }
    if (!email.trim()) {
      setLocalError('Please enter your email address.');
      return;
    }
    if (password.length < 8) {
      setLocalError('Password must be at least 8 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setLocalError('Password confirmation does not match.');
      return;
    }

    try {
      setIsSubmitting(true);
      await signup({
        name: name.trim(),
        email: email.trim(),
        password,
        confirm_password: confirmPassword,
      });
    } catch (err: any) {
      setLocalError(err.message || 'Failed to create account.');
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
          maxWidth: '440px',
          padding: '36px 32px',
          background: 'rgba(19, 27, 42, 0.85)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
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
              marginBottom: '12px',
              boxShadow: '0 0 20px rgba(245, 158, 11, 0.4)',
            }}
          >
            <Sparkles size={22} />
          </div>
          <h2 style={{ fontSize: '22px', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: '6px' }}>
            Create an Account
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px' }}>
            Start querying 300+ episodes of Lenny's growth intelligence
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
              marginBottom: '18px',
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
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Full Name */}
          <div>
            <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Full Name
            </label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <div style={{ position: 'absolute', left: '12px', color: 'var(--text-muted)' }}>
                <UserIcon size={16} />
              </div>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Elena Verna"
                required
                style={{
                  width: '100%',
                  height: '40px',
                  paddingLeft: '38px',
                  paddingRight: '12px',
                  fontSize: '14px',
                }}
              />
            </div>
          </div>

          {/* Email */}
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
                placeholder="elena@growth.com"
                required
                style={{
                  width: '100%',
                  height: '40px',
                  paddingLeft: '38px',
                  paddingRight: '12px',
                  fontSize: '14px',
                }}
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Password (min 8 characters)
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
                  height: '40px',
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

            {/* Password strength indicator */}
            {password && (
              <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ display: 'flex', gap: '4px', flex: 1 }}>
                  <div style={{ height: '4px', flex: 1, borderRadius: '2px', background: strength.score >= 1 ? strength.color : 'rgba(255,255,255,0.1)' }} />
                  <div style={{ height: '4px', flex: 1, borderRadius: '2px', background: strength.score >= 2 ? strength.color : 'rgba(255,255,255,0.1)' }} />
                  <div style={{ height: '4px', flex: 1, borderRadius: '2px', background: strength.score >= 3 ? strength.color : 'rgba(255,255,255,0.1)' }} />
                </div>
                <span style={{ fontSize: '11px', color: strength.color, fontWeight: 500 }}>
                  {strength.label}
                </span>
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Confirm Password
            </label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <div style={{ position: 'absolute', left: '12px', color: 'var(--text-muted)' }}>
                <Lock size={16} />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: '100%',
                  height: '40px',
                  paddingLeft: '38px',
                  paddingRight: '12px',
                  fontSize: '14px',
                }}
              />
              {confirmPassword && password === confirmPassword && (
                <div style={{ position: 'absolute', right: '12px', color: '#10B981', display: 'flex', alignItems: 'center' }}>
                  <CheckCircle2 size={16} />
                </div>
              )}
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
            {isSubmitting ? <LoadingSpinner size="sm" /> : <span>Create Account</span>}
          </button>
        </form>

        {/* Footer switch */}
        <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '13px', color: 'var(--text-secondary)' }}>
          Already have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            style={{
              background: 'transparent',
              color: 'var(--accent-amber)',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Sign In
          </button>
        </div>
      </div>
    </div>
  );
};
