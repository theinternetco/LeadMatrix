'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

const buildCSS = (dark: boolean): string => {
  const border  = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.07)';
  const text    = dark ? '#f1f5f9' : '#0f172a';
  const muted   = '#64748b';
  const surface = dark ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.75)';

  return `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', -apple-system, sans-serif; }

    @keyframes pulseGlow {
      0%,100% { opacity:1; transform:scale(1); }
      50%     { opacity:0.4; transform:scale(0.88); }
    }
    @keyframes fadeUp {
      from { opacity:0; transform:translateY(20px); }
      to   { opacity:1; transform:translateY(0); }
    }
    @keyframes orb1 {
      0%,100% { transform:translate(0,0) scale(1); }
      33%     { transform:translate(50px,-40px) scale(1.08); }
      66%     { transform:translate(-30px,30px) scale(0.95); }
    }
    @keyframes orb2 {
      0%,100% { transform:translate(0,0) scale(1); }
      33%     { transform:translate(-40px,50px) scale(0.92); }
      66%     { transform:translate(35px,-20px) scale(1.06); }
    }

    /* ── Navbar ── */
    .lm-nav {
      position: sticky; top: 0; z-index: 100;
      border-bottom: 1px solid ${border};
      backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
      background: ${dark ? 'rgba(11,15,26,0.82)' : 'rgba(241,245,249,0.82)'};
    }
    .lm-nav-inner {
      max-width: 1100px; margin: 0 auto;
      padding: 13px 24px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .lm-logo { display: flex; align-items: center; gap: 10px; text-decoration: none; }
    .lm-logo-icon {
      width: 32px; height: 32px; border-radius: 9px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      display: flex; align-items: center; justify-content: center; font-size: 1rem;
    }
    .lm-logo-text { font-weight: 800; font-size: 1.05rem; letter-spacing: -0.02em; color: ${text}; }
    .lm-logo-text span { color: #6366f1; }
    .lm-nav-links { display: flex; align-items: center; gap: 8px; }
    .lm-nav-ghost {
      padding: 7px 16px; border-radius: 8px; font-size: 0.85rem; font-weight: 600;
      color: ${muted}; text-decoration: none; transition: all 0.18s ease;
    }
    .lm-nav-ghost:hover { color: ${text}; background: ${surface}; }
    .lm-nav-pill {
      padding: 7px 18px; border-radius: 8px; font-size: 0.85rem; font-weight: 700;
      background: linear-gradient(135deg,#6366f1,#8b5cf6); color: white;
      text-decoration: none; box-shadow: 0 4px 14px rgba(99,102,241,0.3);
      transition: all 0.18s ease;
    }
    .lm-nav-pill:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(99,102,241,0.4); }

    /* ── Hero ── */
    .lm-hero {
      text-align: center; max-width: 680px; margin: 0 auto;
      padding: 96px 24px 72px;
      display: flex; flex-direction: column; align-items: center;
      position: relative; z-index: 1;
    }
    .lm-badge {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 6px 15px; border-radius: 99px;
      background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.28);
      font-size: 0.76rem; font-weight: 600; color: #818cf8;
      margin-bottom: 30px; animation: fadeUp 0.5s ease both;
    }
    .lm-badge-dot {
      width: 6px; height: 6px; border-radius: 50%;
      background: #6366f1; animation: pulseGlow 2s ease infinite;
    }
    .lm-h1 {
      font-size: clamp(3rem, 8.5vw, 5.6rem);
      font-weight: 900; letter-spacing: -0.05em; line-height: 0.95;
      margin-bottom: 26px; animation: fadeUp 0.5s ease 0.08s both;
    }
    .lm-h1-gradient {
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 45%, #ec4899 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .lm-h1-sub {
      color: ${text}; font-size: 0.58em; font-weight: 800;
      letter-spacing: -0.03em; display: block; margin-top: 8px;
    }
    .lm-subtitle {
      font-size: clamp(0.95rem, 2.2vw, 1.1rem);
      color: ${muted}; line-height: 1.75; max-width: 460px;
      margin: 0 auto 38px; animation: fadeUp 0.5s ease 0.16s both;
    }
    .lm-btn-primary {
      display: inline-flex; align-items: center; gap: 9px;
      padding: 15px 36px; border-radius: 12px;
      background: linear-gradient(135deg,#6366f1,#8b5cf6);
      color: white; font-weight: 700; font-size: 0.97rem;
      border: none; cursor: pointer; text-decoration: none;
      box-shadow: 0 8px 28px rgba(99,102,241,0.35);
      transition: all 0.2s cubic-bezier(0.16,1,0.3,1);
      font-family: inherit; animation: fadeUp 0.5s ease 0.24s both;
    }
    .lm-btn-primary:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 14px 38px rgba(99,102,241,0.5); }
    .lm-btn-primary:active { transform: translateY(-1px) scale(0.99); }

    /* ── Divider ── */
    .lm-divider {
      height: 1px; background: ${border};
      max-width: 1100px; margin: 0 auto 56px;
      animation: fadeUp 0.5s ease 0.3s both;
    }

    /* ── Quick Access ── */
    .lm-ql-section {
      max-width: 1100px; margin: 0 auto;
      padding: 0 24px 80px;
      position: relative; z-index: 1;
      animation: fadeUp 0.5s ease 0.34s both;
    }
    .lm-ql-label {
      font-size: 0.68rem; font-weight: 700; color: ${muted};
      text-transform: uppercase; letter-spacing: 0.12em;
      margin-bottom: 16px; text-align: center;
    }
    .lm-ql-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; }
    .lm-ql-item {
      display: flex; flex-direction: column; align-items: center; gap: 11px;
      padding: 24px 12px; border-radius: 14px; text-decoration: none;
      border: 1px solid ${border};
      background: ${dark ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.75)'};
      backdrop-filter: blur(10px);
      transition: all 0.22s cubic-bezier(0.16,1,0.3,1);
    }
    .lm-ql-item:hover {
      transform: translateY(-5px);
      border-color: rgba(99,102,241,0.4);
      box-shadow: 0 12px 32px rgba(99,102,241,0.13);
      background: ${dark ? 'rgba(99,102,241,0.08)' : 'rgba(99,102,241,0.05)'};
    }
    .lm-ql-icon {
      width: 46px; height: 46px; border-radius: 13px;
      display: flex; align-items: center; justify-content: center; font-size: 1.25rem;
    }
    .lm-ql-label-text { font-size: 0.8rem; font-weight: 600; color: ${text}; }

    /* ── Dark toggle ── */
    .lm-toggle {
      position: fixed; top: 22px; right: 22px; z-index: 999;
      width: 42px; height: 42px; border-radius: 11px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.05rem; cursor: pointer;
      border: 1px solid ${border};
      background: ${dark ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.9)'};
      backdrop-filter: blur(12px);
      transition: all 0.2s cubic-bezier(0.16,1,0.3,1);
      box-shadow: 0 4px 14px rgba(0,0,0,0.12);
    }
    .lm-toggle:hover { transform: scale(1.08); border-color: rgba(99,102,241,0.45); }

    /* ── Footer ── */
    .lm-footer {
      border-top: 1px solid ${border};
      padding: 20px 24px;
      display: flex; justify-content: center; align-items: center; gap: 8px;
      font-size: 0.75rem; color: ${muted};
      position: relative; z-index: 1;
    }
    .lm-footer strong { color: ${text}; }

    @media (max-width: 640px) {
      .lm-ql-grid { grid-template-columns: repeat(2,1fr); }
      .lm-btn-primary { width: 100%; justify-content: center; }
      .lm-hero { padding: 64px 20px 52px; }
    }

    * { -webkit-tap-highlight-color: transparent; }
    button, a { -webkit-user-select: none; user-select: none; }
  `;
};

export default function Home() {
  const [dark, setDark] = useState(true);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    try {
      const saved = localStorage.getItem('lm_dark');
      if (saved !== null) setDark(saved === 'true');
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    if (!mounted) return;
    try { localStorage.setItem('lm_dark', String(dark)); } catch { /* ignore */ }
  }, [dark, mounted]);

  const quickLinks = [
    { href: '/businesses-list', icon: '🏢', label: 'Businesses', color: '#6366f1' },
    { href: '/login',           icon: '🔑', label: 'Login',      color: '#8b5cf6' },
    { href: '/dashboard',       icon: '📊', label: 'Dashboard',  color: '#06b6d4' },
    { href: '/rankings',        icon: '📍', label: 'Rankings',   color: '#10b981' },
  ];

  const bg    = dark ? '#0b0f1a' : '#f1f5f9';
  const orb1  = dark ? 'rgba(99,102,241,0.11)'  : 'rgba(99,102,241,0.07)';
  const orb2  = dark ? 'rgba(139,92,246,0.09)'  : 'rgba(139,92,246,0.06)';
  const orb3  = dark ? 'rgba(236,72,153,0.06)'  : 'rgba(236,72,153,0.04)';

  const handleDashboard = useCallback(() => router.push('/dashboard'), [router]);
  const toggleDark      = useCallback(() => setDark(d => !d), []);

  return (
    <div style={{ minHeight: '100vh', background: bg, fontFamily: "'Inter', -apple-system, sans-serif", color: dark ? '#f1f5f9' : '#0f172a', overflowX: 'hidden', position: 'relative' }}>
      <style>{buildCSS(dark)}</style>

      {/* Ambient orbs */}
      <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
        <div style={{ position: 'absolute', top: '-18%', left: '-12%', width: '640px', height: '640px', borderRadius: '50%', background: `radial-gradient(circle, ${orb1} 0%, transparent 70%)`, animation: 'orb1 20s ease-in-out infinite' }} />
        <div style={{ position: 'absolute', bottom: '-22%', right: '-12%', width: '720px', height: '720px', borderRadius: '50%', background: `radial-gradient(circle, ${orb2} 0%, transparent 70%)`, animation: 'orb2 26s ease-in-out infinite' }} />
        <div style={{ position: 'absolute', top: '35%', left: '38%', width: '420px', height: '420px', borderRadius: '50%', background: `radial-gradient(circle, ${orb3} 0%, transparent 70%)`, animation: 'orb1 16s ease-in-out infinite reverse' }} />
      </div>

      {/* Dark mode toggle */}
      <button className="lm-toggle" onClick={toggleDark} aria-label="Toggle theme">
        {dark ? '☀️' : '🌙'}
      </button>

      {/* Navbar */}
      <nav className="lm-nav">
        <div className="lm-nav-inner">
          <Link href="/" className="lm-logo">
            <div className="lm-logo-icon">⚡</div>
            <span className="lm-logo-text">Lead<span>Matrix</span></span>
          </Link>
          <div className="lm-nav-links">
            <Link href="/businesses-list" className="lm-nav-ghost">Businesses</Link>
            <Link href="/rankings"        className="lm-nav-ghost">Rankings</Link>
            <Link href="/login"           className="lm-nav-ghost">Login</Link>
            <Link href="/dashboard"       className="lm-nav-pill">Dashboard →</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <div className="lm-hero">
        <div className="lm-badge">
          <span className="lm-badge-dot" />
          v4.2.0 — GMB Analytics Platform
        </div>
        <h1 className="lm-h1">
          <span className="lm-h1-gradient">LeadMatrix</span>
          <span className="lm-h1-sub">GMB Intelligence<br />Platform</span>
        </h1>
        <p className="lm-subtitle">
          Track rankings, monitor reviews, and unlock deep GMB analytics for healthcare businesses — all in one place.
        </p>
        <button className="lm-btn-primary" onClick={handleDashboard}>
          🚀 Go to Dashboard
        </button>
      </div>

      {/* Divider */}
      <div className="lm-divider" />

      {/* Quick Access */}
      <div className="lm-ql-section">
        <div className="lm-ql-label">Quick Access</div>
        <div className="lm-ql-grid">
          {quickLinks.map((l, i) => (
            <Link key={i} href={l.href} className="lm-ql-item">
              <div className="lm-ql-icon" style={{ background: `${l.color}18` }}>{l.icon}</div>
              <span className="lm-ql-label-text">{l.label}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="lm-footer">
        <span>LeadMatrix</span>
        <span>·</span>
        <span>Built by <strong>Himanshu</strong></span>
        <span>·</span>
        <span>v4.2.0</span>
      </footer>
    </div>
  );
}
