'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';

export default function GMBLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error' | 'info'>('info');
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loginProgress, setLoginProgress] = useState(0);
  const [darkMode, setDarkMode] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const router = useRouter();

  // Load preferences
  useEffect(() => {
    const savedDarkMode = localStorage.getItem('darkMode');
    const savedEmail = localStorage.getItem('rememberedEmail');
    
    if (savedDarkMode === 'true') setDarkMode(true);
    if (savedEmail) {
      setEmail(savedEmail);
      setRememberMe(true);
    }
  }, []);

  // Save dark mode preference
  useEffect(() => {
    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  useEffect(() => {
    checkBackendStatus();
    const interval = setInterval(checkBackendStatus, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const checkBackendStatus = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const response = await fetch('http://localhost:8000/api/health', {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      await response.json();
      setBackendStatus('online');
    } catch {
      setBackendStatus('offline');
    }
  };

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) {
      setEmailError('Email is required');
      return false;
    }
    if (!emailRegex.test(email)) {
      setEmailError('Invalid email format');
      return false;
    }
    setEmailError('');
    return true;
  };

  const validatePassword = (password: string) => {
    if (!password) {
      setPasswordError('Password is required');
      return false;
    }
    if (password.length < 6) {
      setPasswordError('Password must be at least 6 characters');
      return false;
    }
    setPasswordError('');
    return true;
  };

  const showMessage = (msg: string, type: 'success' | 'error' | 'info') => {
    setMessage(msg);
    setMessageType(type);
  };

  const simulateProgress = () => {
    setLoginProgress(0);
    const interval = setInterval(() => {
      setLoginProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 10;
      });
    }, 500);
    return interval;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateEmail(email) || !validatePassword(password)) {
      return;
    }

    setLoading(true);
    setMessage('');
    showMessage('🔐 Initializing secure login...', 'info');

    const progressInterval = simulateProgress();

    try {
      const url = new URL('http://localhost:8000/api/gmb/stealth-login');
      url.searchParams.append('email', email);
      url.searchParams.append('password', password);
      url.searchParams.append('headless', 'false');

      console.log('🔥 Calling:', url.toString());
      showMessage('🌐 Connecting to server...', 'info');

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      const data = await response.json();
      console.log('📊 Response:', data);

      clearInterval(progressInterval);
      setLoginProgress(100);

      if (data.success) {
        showMessage('✅ ' + (data.message || 'Login successful! Browser opened...'), 'success');
        
        // Save email if remember me is checked
        if (rememberMe) {
          localStorage.setItem('rememberedEmail', email);
        } else {
          localStorage.removeItem('rememberedEmail');
        }

        setTimeout(() => {
          showMessage('✅ Redirecting to dashboard...', 'success');
          setTimeout(() => {
            router.push('/dashboard');
          }, 1500);
        }, 3000);
      } else {
        showMessage(`❌ ${data.message || 'Login failed. Check your credentials.'}`, 'error');
      }
    } catch (err) {
      clearInterval(progressInterval);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Login error:', err);
      showMessage(`❌ Connection failed: ${errorMessage}`, 'error');
    } finally {
      setTimeout(() => setLoading(false), 500);
    }
  };

  const colors = darkMode ? {
    bg: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
    cardBg: '#1e293b',
    text: '#f1f5f9',
    textSecondary: '#94a3b8',
    border: '#334155',
    inputBg: '#0f172a',
    inputBorder: '#334155',
    buttonBg: '#374151'
  } : {
    bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    cardBg: '#ffffff',
    text: '#111827',
    textSecondary: '#6b7280',
    border: '#e5e7eb',
    inputBg: '#ffffff',
    inputBorder: '#e5e7eb',
    buttonBg: '#f3f4f6'
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: colors.bg,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      position: 'relative' as const
    }}>
      {/* Background Animated Circles */}
      <div className="bg-circles" style={{
        position: 'absolute' as const,
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        zIndex: 0
      }}>
        <div className="circle circle1"></div>
        <div className="circle circle2"></div>
        <div className="circle circle3"></div>
      </div>

      <div className="login-card" style={{
        background: colors.cardBg,
        padding: 'clamp(30px, 6vw, 40px)',
        borderRadius: '24px',
        boxShadow: darkMode ? '0 25px 80px rgba(0,0,0,0.5)' : '0 20px 60px rgba(0,0,0,0.3)',
        maxWidth: '550px',
        width: '100%',
        position: 'relative' as const,
        zIndex: 1,
        border: darkMode ? `1px solid ${colors.border}` : 'none'
      }}>
        {/* Dark Mode Toggle - Top Right */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          style={{
            position: 'absolute' as const,
            top: '20px',
            right: '20px',
            padding: '10px 16px',
            background: colors.buttonBg,
            color: colors.text,
            border: darkMode ? `1px solid ${colors.border}` : 'none',
            borderRadius: '10px',
            cursor: 'pointer',
            fontSize: '1rem',
            fontWeight: 600
          }}
          className="dark-mode-btn"
        >
          {darkMode ? '☀️' : '🌙'}
        </button>

        {/* Header with Status */}
        <div style={{ marginBottom: '30px', textAlign: 'center' as const }}>
          <div style={{
            width: '80px',
            height: '80px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px',
            fontSize: '2.5rem',
            boxShadow: '0 10px 30px rgba(102, 126, 234, 0.3)'
          }} className="logo-pulse">
            🔐
          </div>
          
          <h1 style={{ 
            fontSize: 'clamp(1.6rem, 5vw, 2rem)', 
            marginBottom: '10px', 
            fontWeight: 800, 
            color: colors.text 
          }}>
            GMB Stealth Login
          </h1>
          <p style={{ color: colors.textSecondary, marginBottom: '15px', fontSize: 'clamp(0.85rem, 2.5vw, 0.95rem)' }}>
            🛡️ Ultra-Protected | 100% Anti-Detection
          </p>
          
          {/* Backend Status Badge */}
          <div className="status-badge" style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            background: backendStatus === 'online' ? '#f0fdf4' : backendStatus === 'offline' ? '#fef2f2' : '#f0f9ff',
            borderRadius: '10px',
            border: `2px solid ${backendStatus === 'online' ? '#86efac' : backendStatus === 'offline' ? '#fecaca' : '#bae6fd'}`
          }}>
            <span className={backendStatus === 'online' ? 'status-dot pulse-dot' : 'status-dot'} style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: backendStatus === 'online' ? '#22c55e' : backendStatus === 'offline' ? '#ef4444' : '#3b82f6'
            }} />
            <span style={{
              color: backendStatus === 'online' ? '#166534' : backendStatus === 'offline' ? '#991b1b' : '#075985',
              fontWeight: 700,
              fontSize: 'clamp(0.8rem, 2vw, 0.85rem)'
            }}>
              {backendStatus === 'online' ? '✅ Backend Ready' : backendStatus === 'offline' ? '❌ Backend Offline' : '🔄 Checking...'}
            </span>
          </div>
        </div>

        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: colors.text, fontSize: 'clamp(0.85rem, 2.5vw, 0.9rem)' }}>
              📧 Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (emailError) validateEmail(e.target.value);
              }}
              onBlur={() => validateEmail(email)}
              disabled={loading}
              className="input-field"
              style={{
                width: '100%',
                padding: 'clamp(12px, 3vw, 14px)',
                border: `2px solid ${emailError ? '#ef4444' : colors.inputBorder}`,
                borderRadius: '10px',
                fontSize: 'clamp(0.9rem, 2.5vw, 1rem)',
                boxSizing: 'border-box' as const,
                opacity: loading ? 0.6 : 1,
                outline: 'none',
                background: colors.inputBg,
                color: colors.text
              }}
              placeholder="your-email@gmail.com"
            />
            {emailError && (
              <p className="error-msg" style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '5px', marginBottom: 0 }}>
                ⚠️ {emailError}
              </p>
            )}
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: colors.text, fontSize: 'clamp(0.85rem, 2.5vw, 0.9rem)' }}>
              🔑 Password
            </label>
            <div style={{ position: 'relative' as const }}>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (passwordError) validatePassword(e.target.value);
                }}
                onBlur={() => validatePassword(password)}
                disabled={loading}
                className="input-field"
                style={{
                  width: '100%',
                  padding: 'clamp(12px, 3vw, 14px)',
                  paddingRight: '50px',
                  border: `2px solid ${passwordError ? '#ef4444' : colors.inputBorder}`,
                  borderRadius: '10px',
                  fontSize: 'clamp(0.9rem, 2.5vw, 1rem)',
                  boxSizing: 'border-box' as const,
                  opacity: loading ? 0.6 : 1,
                  outline: 'none',
                  background: colors.inputBg,
                  color: colors.text
                }}
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute' as const,
                  right: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '1.2rem',
                  padding: '5px'
                }}
                className="toggle-password"
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            {passwordError && (
              <p className="error-msg" style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '5px', marginBottom: 0 }}>
                ⚠️ {passwordError}
              </p>
            )}
          </div>

          {/* Remember Me */}
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px', gap: '8px' }}>
            <input
              type="checkbox"
              id="rememberMe"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              style={{ width: '18px', height: '18px', cursor: 'pointer' }}
            />
            <label htmlFor="rememberMe" style={{ fontSize: 'clamp(0.85rem, 2vw, 0.9rem)', color: colors.textSecondary, cursor: 'pointer', userSelect: 'none' as const }}>
              Remember me
            </label>
          </div>

          {/* Login Progress Bar */}
          {loading && (
            <div style={{ marginBottom: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                <span style={{ fontSize: '0.8rem', color: colors.textSecondary, fontWeight: 600 }}>Login Progress</span>
                <span style={{ fontSize: '0.8rem', color: colors.text, fontWeight: 700 }}>{loginProgress}%</span>
              </div>
              <div style={{
                width: '100%',
                height: '6px',
                background: darkMode ? '#0f172a' : '#e5e7eb',
                borderRadius: '10px',
                overflow: 'hidden'
              }}>
                <div className="progress-bar-fill" style={{
                  width: `${loginProgress}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || backendStatus === 'offline'}
            className="login-button"
            style={{
              width: '100%',
              padding: 'clamp(14px, 4vw, 16px)',
              background: (loading || backendStatus === 'offline') ? '#d1d5db' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontSize: 'clamp(1rem, 3vw, 1.1rem)',
              fontWeight: 700,
              cursor: (loading || backendStatus === 'offline') ? 'not-allowed' : 'pointer',
              boxShadow: (loading || backendStatus === 'offline') ? 'none' : '0 4px 15px rgba(102, 126, 234, 0.4)',
              position: 'relative' as const
            }}
          >
            {loading ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
                <span className="spinner"></span>
                Logging in...
              </span>
            ) : (
              '🔐 Login Securely'
            )}
          </button>
        </form>

        {/* Message Display */}
        {message && (
          <div className="message-box" style={{
            marginTop: '20px',
            padding: 'clamp(14px, 4vw, 16px)',
            background: messageType === 'success' ? '#f0fdf4' : messageType === 'error' ? '#fef2f2' : '#eff6ff',
            color: messageType === 'success' ? '#166534' : messageType === 'error' ? '#991b1b' : '#1e40af',
            borderRadius: '10px',
            textAlign: 'center' as const,
            fontSize: 'clamp(0.85rem, 2.5vw, 0.95rem)',
            border: `2px solid ${messageType === 'success' ? '#86efac' : messageType === 'error' ? '#fecaca' : '#bfdbfe'}`,
            fontWeight: 600
          }}>
            {message}
          </div>
        )}

        {/* What Happens Next */}
        {loading && (
          <div className="info-box" style={{
            marginTop: '20px',
            padding: 'clamp(14px, 4vw, 16px)',
            background: darkMode ? '#0f172a' : '#eff6ff',
            borderRadius: '10px',
            fontSize: 'clamp(0.8rem, 2vw, 0.9rem)',
            border: `2px solid ${darkMode ? colors.border : '#bfdbfe'}`
          }}>
            <p style={{ fontWeight: 700, marginBottom: '8px', color: darkMode ? '#93c5fd' : '#1e40af' }}>
              📋 What&apos;s happening:
            </p>
            <ul style={{ paddingLeft: '20px', color: darkMode ? colors.textSecondary : '#1e3a8a', margin: 0, lineHeight: 1.8 }}>
              <li>Chrome browser is opening...</li>
              <li>Navigating to Google login</li>
              <li>Enter your credentials in the browser</li>
              <li>Complete 2FA if prompted</li>
              <li>Wait for confirmation</li>
            </ul>
          </div>
        )}

        {/* Collapsible Sections */}
        <details style={{ marginTop: '20px' }} className="collapsible">
          <summary style={{
            padding: '12px',
            background: darkMode ? '#0f172a' : '#f9fafb',
            borderRadius: '10px',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: 'clamp(0.85rem, 2vw, 0.9rem)',
            color: colors.text,
            border: `1px solid ${colors.border}`,
            listStyle: 'none'
          }}>
            🔧 Troubleshooting
          </summary>
          <div style={{
            marginTop: '10px',
            padding: 'clamp(12px, 3vw, 15px)',
            background: darkMode ? '#0f172a' : '#f9fafb',
            borderRadius: '10px',
            fontSize: 'clamp(0.8rem, 2vw, 0.85rem)',
            border: `1px solid ${colors.border}`
          }}>
            <ul style={{ paddingLeft: '20px', color: colors.textSecondary, margin: 0, lineHeight: 1.8 }}>
              <li>Backend: <code style={{ background: darkMode ? '#1e293b' : '#e5e7eb', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem' }}>uvicorn main:app --reload</code></li>
              <li>Install: <code style={{ background: darkMode ? '#1e293b' : '#e5e7eb', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem' }}>pip install undetected-chromedriver</code></li>
              <li>Browser will open (not headless)</li>
              <li>Complete 2FA manually in browser</li>
            </ul>
          </div>
        </details>

        <details style={{ marginTop: '15px' }} className="collapsible">
          <summary style={{
            padding: '12px',
            background: darkMode ? '#0f172a' : '#f0fdf4',
            borderRadius: '10px',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: 'clamp(0.85rem, 2vw, 0.9rem)',
            color: darkMode ? '#86efac' : '#166534',
            border: `1px solid ${darkMode ? colors.border : '#86efac'}`,
            listStyle: 'none'
          }}>
            🛡️ Security Features
          </summary>
          <div style={{
            marginTop: '10px',
            padding: 'clamp(12px, 3vw, 15px)',
            background: darkMode ? '#0f172a' : '#f0fdf4',
            borderRadius: '10px',
            fontSize: 'clamp(0.8rem, 2vw, 0.85rem)',
            border: `1px solid ${darkMode ? colors.border : '#86efac'}`
          }}>
            <ul style={{ paddingLeft: '20px', color: darkMode ? '#86efac' : '#166534', margin: 0, lineHeight: 1.8 }}>
              <li>100+ anti-detection methods active</li>
              <li>Undetectable browser fingerprint</li>
              <li>Human-like behavior simulation</li>
              <li>2FA support enabled</li>
              <li>Session-based authentication</li>
            </ul>
          </div>
        </details>

        {/* Navigation Links */}
        <div style={{ 
          marginTop: '20px', 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '10px',
          flexWrap: 'wrap' as const
        }}>
          <Link href="/dashboard" className="nav-link" style={{
            color: '#667eea',
            textDecoration: 'none',
            fontWeight: 600,
            fontSize: 'clamp(0.85rem, 2vw, 0.9rem)'
          }}>
            ← Back to Dashboard
          </Link>
          
          <button
            onClick={checkBackendStatus}
            className="refresh-btn"
            style={{
              padding: '8px 16px',
              background: colors.buttonBg,
              border: `2px solid ${colors.border}`,
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: 'clamp(0.8rem, 2vw, 0.85rem)',
              fontWeight: 600,
              color: colors.text
            }}
          >
            🔄 Refresh Status
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }

        @keyframes slideDown {
          from { opacity: 0; max-height: 0; }
          to { opacity: 1; max-height: 300px; }
        }

        .login-card {
          animation: fadeIn 0.5s ease-out;
        }

        .logo-pulse {
          animation: float 3s ease-in-out infinite;
        }

        .pulse-dot {
          animation: pulse 2s infinite;
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          display: inline-block;
          animation: spin 0.8s linear infinite;
        }

        .input-field:focus {
          border-color: #667eea !important;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
          transition: all 0.2s ease;
        }

        .login-button:not(:disabled):hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
          transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        .login-button:not(:disabled):active {
          transform: scale(0.98);
        }

        .dark-mode-btn:hover {
          transform: scale(1.05);
          transition: transform 0.2s ease;
        }

        .toggle-password:hover {
          transform: translateY(-50%) scale(1.1);
          transition: transform 0.2s ease;
        }

        .nav-link:hover {
          color: #764ba2;
          transition: color 0.3s ease;
        }

        .refresh-btn:hover {
          border-color: #667eea;
          color: #667eea;
          transform: scale(1.02);
          transition: all 0.2s ease;
        }

        .message-box {
          animation: slideDown 0.3s ease-out;
        }

        .info-box {
          animation: fadeIn 0.4s ease-out;
        }

        .error-msg {
          animation: slideDown 0.2s ease-out;
        }

        .status-badge {
          animation: fadeIn 0.4s ease-out;
        }

        .collapsible[open] > div {
          animation: slideDown 0.3s ease-out;
        }

        .progress-bar-fill {
          position: relative;
        }

        .progress-bar-fill::after {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
          animation: shimmer 1.5s infinite;
        }

        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }

        .circle {
          position: absolute;
          border-radius: 50%;
          opacity: 0.1;
        }

        .circle1 {
          width: 300px;
          height: 300px;
          background: ${darkMode ? '#3b82f6' : '#fff'};
          top: -100px;
          left: -100px;
          animation: float 8s ease-in-out infinite;
        }

        .circle2 {
          width: 200px;
          height: 200px;
          background: ${darkMode ? '#8b5cf6' : '#fff'};
          bottom: -80px;
          right: -80px;
          animation: float 10s ease-in-out infinite reverse;
        }

        .circle3 {
          width: 150px;
          height: 150px;
          background: ${darkMode ? '#ec4899' : '#fff'};
          top: 50%;
          right: 10%;
          animation: float 12s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
