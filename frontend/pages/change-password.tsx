'use client';

import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import API_BASE from '../lib/api';

export default function ChangePassword() {
  const router = useRouter();
  const [current,  setCurrent]  = useState('');
  const [next,     setNext]     = useState('');
  const [confirm,  setConfirm]  = useState('');
  const [error,    setError]    = useState('');
  const [success,  setSuccess]  = useState('');
  const [loading,  setLoading]  = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (next !== confirm) {
      setError('New passwords do not match');
      return;
    }
    if (next.length < 8) {
      setError('New password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('lm_token');
      const res = await fetch(`${API_BASE}/api/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ current_password: current, new_password: next }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Failed to change password');
        return;
      }
      setSuccess('Password changed successfully! Redirecting…');
      setCurrent(''); setNext(''); setConfirm('');
      setTimeout(() => router.replace('/dashboard'), 1500);
    } catch {
      setError('Cannot reach the server. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.logo}>LM</div>
        <h1 style={styles.title}>Change Password</h1>
        <p style={styles.sub}>Enter your current password and choose a new one</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.field}>
            <label style={styles.label}>Current Password</label>
            <input
              type="password"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              placeholder="••••••••"
              required
              style={styles.input}
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>New Password</label>
            <input
              type="password"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              placeholder="Min. 8 characters"
              required
              style={styles.input}
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Confirm New Password</label>
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="••••••••"
              required
              style={styles.input}
            />
          </div>

          {error   && <div style={styles.error}>{error}</div>}
          {success && <div style={styles.successBox}>{success}</div>}

          <button type="submit" disabled={loading} style={styles.btn}>
            {loading ? 'Updating…' : 'Update Password'}
          </button>

          <Link href="/dashboard" style={styles.back}>← Back to Dashboard</Link>
        </form>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#f1f5f9',
    fontFamily: "'Inter', sans-serif",
  },
  card: {
    background: '#fff',
    borderRadius: 16,
    padding: '40px 36px',
    width: '100%',
    maxWidth: 400,
    boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
    textAlign: 'center',
  },
  logo: {
    width: 48,
    height: 48,
    borderRadius: 12,
    background: '#6366f1',
    color: '#fff',
    fontWeight: 800,
    fontSize: 18,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 16px',
  },
  title: {
    margin: '0 0 4px',
    fontSize: 22,
    fontWeight: 700,
    color: '#0f172a',
  },
  sub: {
    margin: '0 0 28px',
    fontSize: 14,
    color: '#64748b',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    textAlign: 'left',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  label: {
    fontSize: 13,
    fontWeight: 600,
    color: '#374151',
  },
  input: {
    padding: '10px 12px',
    borderRadius: 8,
    border: '1.5px solid #e2e8f0',
    fontSize: 14,
    outline: 'none',
    color: '#0f172a',
  },
  error: {
    background: '#fef2f2',
    color: '#dc2626',
    border: '1px solid #fecaca',
    borderRadius: 8,
    padding: '10px 12px',
    fontSize: 13,
  },
  successBox: {
    background: '#f0fdf4',
    color: '#16a34a',
    border: '1px solid #bbf7d0',
    borderRadius: 8,
    padding: '10px 12px',
    fontSize: 13,
  },
  btn: {
    padding: '11px',
    borderRadius: 8,
    background: '#6366f1',
    color: '#fff',
    fontWeight: 700,
    fontSize: 15,
    border: 'none',
    cursor: 'pointer',
    marginTop: 4,
  },
  back: {
    textAlign: 'center',
    fontSize: 13,
    color: '#6366f1',
    textDecoration: 'none',
  },
};
