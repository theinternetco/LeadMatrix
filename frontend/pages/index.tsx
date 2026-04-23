'use client';

import { useState, useEffect, useMemo, useCallback, memo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

// ── Types ─────────────────────────────────────────────────────────────────────

interface Stat {
  icon: string;
  value: string;
  label: string;
  color: string;
  bg: string;
  trend: string;
}

interface StatCardProps {
  stat: Stat;
  index: number;
  hoveredStat: number | null;
  setHoveredStat: (i: number | null) => void;
  dark: boolean;
}

interface Colors {
  text: string;
  textMuted: string;
  surface: string;
  surfaceStrong: string;
  border: string;
}

// ── StatCard ──────────────────────────────────────────────────────────────────

const StatCard = memo(({ stat, index, hoveredStat, setHoveredStat, dark }: StatCardProps) => {
  const hovered = hoveredStat === index;
  return (
    <div
      onMouseEnter={() => setHoveredStat(index)}
      onMouseLeave={() => setHoveredStat(null)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
        padding: '16px 18px',
        borderRadius: '13px',
        background: hovered
          ? (dark ? 'rgba(99,102,241,0.12)' : 'rgba(99,102,241,0.07)')
          : (dark ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.7)'),
        border: `1px solid ${hovered ? 'rgba(99,102,241,0.4)' : (dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.07)')}`,
        transform: hovered ? 'translateX(5px)' : 'translateX(0)',
        transition: 'all 0.22s cubic-bezier(0.16,1,0.3,1)',
        cursor: 'default',
      }}
    >
      {/* Icon */}
      <div style={{
        width: '44px', height: '44px', borderRadius: '11px',
        background: stat.bg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '1.3rem', flexShrink: 0,
        boxShadow: `0 4px 14px ${stat.color}25`,
        transition: 'transform 0.2s ease',
        transform: hovered ? 'scale(1.08)' : 'scale(1)',
      }}>{stat.icon}</div>

      {/* Label & Value */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: '1.45rem', fontWeight: 800, lineHeight: 1.1,
          color: dark ? '#f1f5f9' : '#0f172a', letterSpacing: '-0.03em',
        }}>{stat.value}</div>
        <div style={{ fontSize: '0.76rem', color: '#64748b', marginTop: '3px', fontWeight: 500 }}>
          {stat.label}
        </div>
      </div>

      {/* Trend */}
      <div style={{
        fontSize: '0.7rem', fontWeight: 700, color: '#10b981',
        background: dark ? 'rgba(16,185,129,0.12)' : 'rgba(16,185,129,0.1)',
        padding: '4px 9px', borderRadius: '99px', whiteSpace: 'nowrap',
        border: '1px solid rgba(16,185,129,0.2)',
      }}>↑ {stat.trend}</div>
    </div>
  );
});
StatCard.displayName = 'StatCard';

// ── CSS ───────────────────────────────────────────────────────────────────────

const buildCSS = (dark: boolean): string => {
  const border = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.07)';
  const text   = dark ? '#f1f5f9' : '#0f172a';
  const muted  = '#64748b';
  const surface = dark ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.75)';

  return `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', -apple-system, sans-serif; }

    @keyframes float {
      0%,100% { transform: translateY(0); }
      50%      { transform: translateY(-14px); }
    }
    @keyframes pulseGlow {
      0%,100% { opacity:1; transform:scale(1); }
      50%     { opacity:0.4; transform:scale(0.88); }
    }
    @keyframes fadeUp {
      from { opacity:0; transform:translateY(22px); }
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
      max-width: 1280px; margin: 0 auto;
      padding: 13px 24px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .lm-logo {
      display: flex; align-items: center; gap: 10px; text-decoration: none;
    }
    .lm-logo-icon {
      width: 32px; height: 32px; border-radius: 9px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      display: flex; align-items: center; justify-content: center; font-size: 1rem;
    }
    .lm-logo-text {
      font-weight: 800; font-size: 1.05rem; letter-spacing: -0.02em; color: ${text};
    }
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

    /* ── Hero badge ── */
    .lm-badge {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 6px 15px; border-radius: 99px;
      background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.28);
      font-size: 0.76rem; font-weight: 600; color: #818cf8;
      margin-bottom: 26px; animation: fadeUp 0.5s ease both;
      white-space: nowrap;
    }
    .lm-badge-dot {
      width: 6px; height: 6px; border-radius: 50%;
      background: #6366f1; animation: pulseGlow 2s ease infinite;
    }

    /* ── Title ── */
    .lm-h1 {
      font-size: clamp(3rem, 8.5vw, 5.8rem);
      font-weight: 900; letter-spacing: -0.05em; line-height: 0.95;
      margin-bottom: 22px; animation: fadeUp 0.5s ease 0.08s both;
    }
    .lm-h1-gradient {
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 45%, #ec4899 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .lm-h1-sub {
      color: ${text}; font-size: 0.58em; font-weight: 800;
      letter-spacing: -0.03em; display: block; margin-top: 6px;
    }

    /* ── Subtitle ── */
    .lm-subtitle {
      font-size: clamp(0.95rem, 2.2vw, 1.15rem);
      color: ${muted}; line-height: 1.7; max-width: 460px;
      margin-bottom: 34px; animation: fadeUp 0.5s ease 0.16s both;
    }

    /* ── CTAs ── */
    .lm-ctas { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 32px; animation: fadeUp 0.5s ease 0.24s both; }
    .lm-btn-primary {
      display: inline-flex; align-items: center; gap: 9px;
      padding: 14px 30px; border-radius: 12px;
      background: linear-gradient(135deg,#6366f1,#8b5cf6);
      color: white; font-weight: 700; font-size: 0.97rem;
      border: none; cursor: pointer; text-decoration: none;
      box-shadow: 0 8px 28px rgba(99,102,241,0.35);
      transition: all 0.2s cubic-bezier(0.16,1,0.3,1);
      white-space: nowrap; font-family: inherit;
    }
    .lm-btn-primary:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 14px 38px rgba(99,102,241,0.5); }
    .lm-btn-primary:active { transform: translateY(-1px) scale(0.99); }
    .lm-btn-secondary {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 14px 26px; border-radius: 12px;
      background: transparent; font-weight: 600; font-size: 0.97rem;
      border: 1.5px solid ${border}; cursor: pointer; text-decoration: none;
      color: ${text}; transition: all 0.2s ease; white-space: nowrap; font-family: inherit;
    }
    .lm-btn-secondary:hover {
      border-color: rgba(99,102,241,0.45); background: rgba(99,102,241,0.07);
      transform: translateY(-2px);
    }

    /* ── Pills ── */
    .lm-pills { display: flex; gap: 9px; flex-wrap: wrap; margin-bottom: 52px; animation: fadeUp 0.5s ease 0.3s both; }
    .lm-pill {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 7px 14px; border-radius: 99px; font-size: 0.8rem; font-weight: 600;
      border: 1px solid ${border}; transition: all 0.18s ease; color: ${text};
    }
    .lm-pill:hover { border-color: rgba(99,102,241,0.35); transform: translateY(-2px); }

    /* ── Features ── */
    .lm-features-label {
      font-size: 0.68rem; font-weight: 700; color: ${muted};
      text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 14px;
    }
    .lm-features-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 3px; }
    .lm-feature-item {
      display: flex; align-items: flex-start; gap: 12px;
      padding: 13px 14px; border-radius: 11px; transition: all 0.18s ease; cursor: default;
    }
    .lm-feature-item:hover { background: ${dark ? 'rgba(255,255,255,0.04)' : 'rgba(99,102,241,0.05)'}; }
    .lm-feature-icon {
      width: 36px; height: 36px; border-radius: 9px; flex-shrink: 0;
      display: flex; align-items: center; justify-content: center; font-size: 1.05rem;
      background: ${dark ? 'rgba(99,102,241,0.1)' : 'rgba(99,102,241,0.07)'};
    }
    .lm-feature-title { font-size: 0.83rem; font-weight: 700; color: ${text}; margin-bottom: 2px; }
    .lm-feature-desc  { font-size: 0.73rem; color: ${muted}; line-height: 1.45; }

    /* ── Right Card ── */
    .lm-card {
      border-radius: 20px;
      background: ${dark ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.92)'};
      border: 1px solid ${border};
      backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
      padding: 30px;
      box-shadow: ${dark ? '0 32px 80px rgba(0,0,0,0.65), 0 0 0 1px rgba(255,255,255,0.04)' : '0 24px 60px rgba(0,0,0,0.09), 0 0 0 1px rgba(255,255,255,0.7)'};
      position: sticky; top: 90px;
      animation: fadeUp 0.6s ease 0.12s both;
    }
    .lm-card-header {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 20px;
    }
    .lm-card-title { font-size: 1.05rem; font-weight: 800; color: ${text}; letter-spacing: -0.02em; }
    .lm-card-sub   { font-size: 0.72rem; color: ${muted}; margin-top: 2px; }
    .lm-live-badge {
      display: flex; align-items: center; gap: 6px;
      padding: 5px 11px; border-radius: 99px;
      background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.25);
    }
    .lm-live-dot {
      width: 7px; height: 7px; border-radius: 50%; background: #10b981;
      animation: pulseGlow 2s ease infinite;
    }
    .lm-live-text { font-size: 0.7rem; font-weight: 700; color: #10b981; }

    /* ── Quick Links ── */
    .lm-divider { height: 1px; background: ${border}; margin: 20px 0; }
    .lm-ql-label {
      font-size: 0.68rem; font-weight: 700; color: ${muted};
      text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 11px;
    }
    .lm-ql-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 8px; }
    .lm-ql-item {
      display: flex; flex-direction: column; align-items: center; gap: 7px;
      padding: 14px 8px; border-radius: 12px; text-decoration: none;
      border: 1px solid ${border};
      background: ${dark ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.6)'};
      transition: all 0.22s cubic-bezier(0.16,1,0.3,1);
    }
    .lm-ql-item:hover {
      transform: translateY(-4px);
      border-color: rgba(99,102,241,0.4);
      box-shadow: 0 10px 28px rgba(99,102,241,0.14);
      background: ${dark ? 'rgba(99,102,241,0.08)' : 'rgba(99,102,241,0.05)'};
    }
    .lm-ql-icon {
      width: 34px; height: 34px; border-radius: 9px;
      display: flex; align-items: center; justify-content: center; font-size: 1rem;
    }
    .lm-ql-label-text { font-size: 0.7rem; font-weight: 600; color: ${text}; text-align: center; }

    /* ── Main CTA btn ── */
    .lm-main-cta {
      width: 100%; padding: 14px; border-radius: 12px; border: none;
      background: linear-gradient(135deg,#6366f1,#8b5cf6);
      color: white; font-weight: 700; font-size: 0.92rem; cursor: pointer;
      box-shadow: 0 6px 22px rgba(99,102,241,0.32);
      transition: all 0.2s ease;
      display: flex; align-items: center; justify-content: center; gap: 8px;
      font-family: inherit;
    }
    .lm-main-cta:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(99,102,241,0.45); }
    .lm-trust {
      text-align: center; margin-top: 13px;
      font-size: 0.71rem; color: ${muted};
    }
    .lm-trust strong { color: ${text}; }

    /* ── Toggle ── */
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

    /* ── Layout ── */
    .lm-main {
      max-width: 1280px; margin: 0 auto;
      padding: 64px 24px 80px;
      position: relative; z-index: 1;
    }
    .lm-grid {
      display: grid;
      grid-template-columns: 1fr 420px;
      gap: 60px; align-items: flex-start;
    }
    .lm-left { display: flex; flex-direction: column; align-items: flex-start; padding-top: 18px; }

    /* ── Footer ── */
    .lm-footer {
      border-top: 1px solid ${border};
      padding: 18px 24px;
      display: flex; justify-content: center; align-items: center; gap: 8px;
      font-size: 0.75rem; color: ${muted};
      position: relative; z-index: 1;
    }
    .lm-footer strong { color: ${text}; }

    /* ── Responsive ── */
    @media (max-width: 960px) {
      .lm-grid { grid-template-columns: 1fr !important; gap: 40px !important; }
      .lm-card { position: static !important; }
      .lm-h1, .lm-subtitle, .lm-badge { text-align: center; }
      .lm-ctas, .lm-pills { justify-content: center; }
      .lm-left { align-items: center; }
      .lm-features-grid { grid-template-columns: 1fr; }
      .lm-subtitle { margin-left: auto; margin-right: auto; }
    }
    @media (max-width: 480px) {
      .lm-main { padding: 36px 16px 60px; }
      .lm-ql-grid { grid-template-columns: repeat(2,1fr); }
      .lm-btn-primary, .lm-btn-secondary { width: 100%; justify-content: center; }
      .lm-ctas { flex-direction: column; }
    }

    * { -webkit-tap-highlight-color: transparent; }
    button, a { -webkit-user-select: none; user-select: none; }
  `;
};

// ── Main Component ────────────────────────────────────────────────────────────

export default function Home() {
  const [dark, setDark] = useState(true);
  const [hoveredStat, setHoveredStat] = useState<number | null>(null);
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

  const stats = useMemo<Stat[]>(() => [
    { icon: '🏢', value: '44+',   label: 'Active Businesses',    color: '#6366f1', bg: 'rgba(99,102,241,0.14)',  trend: '+12%'  },
    { icon: '📈', value: '102K+', label: 'Data Points Tracked',  color: '#8b5cf6', bg: 'rgba(139,92,246,0.14)', trend: '+28%'  },
    { icon: '⚡', value: '24/7',  label: 'Real-time Monitoring', color: '#ec4899', bg: 'rgba(236,72,153,0.14)', trend: '100%'  },
    { icon: '✅', value: '99.9%', label: 'Uptime Guarantee',     color: '#10b981', bg: 'rgba(16,185,129,0.14)', trend: '+0.2%' },
  ], []);

  const features = [
    { icon: '📍', title: 'GMB Rankings',     desc: 'Track local pack position across all keywords' },
    { icon: '📊', title: 'Deep Analytics',   desc: 'Views, calls, clicks & direction trends' },
    { icon: '🔍', title: 'Keyword Intel',    desc: 'Discover what customers search to find you' },
    { icon: '⭐', title: 'Review Monitor',   desc: 'Ratings, sentiment & response tracking' },
    { icon: '🗺️', title: 'Maps Insights',   desc: 'Platform & device breakdown per listing' },
    { icon: '📅', title: 'Post Scheduler',  desc: 'GMB posts, offers & updates on autopilot' },
  ];

  const quickLinks = [
    { href: '/businesses-list', icon: '🏢', label: 'Businesses', color: '#6366f1' },
    { href: '/gmb-login',       icon: '🔑', label: 'GMB Login',  color: '#8b5cf6' },
    { href: '/dashboard',       icon: '📊', label: 'Dashboard',  color: '#06b6d4' },
    { href: '/rankings',        icon: '📍', label: 'Rankings',   color: '#10b981' },
  ];

  const pills = [
    { icon: '⚡', label: 'Real-time sync',  bg: dark ? 'rgba(245,158,11,0.1)'  : 'rgba(245,158,11,0.08)'  },
    { icon: '🔒', label: 'OAuth secured',   bg: dark ? 'rgba(16,185,129,0.1)'  : 'rgba(16,185,129,0.08)'  },
    { icon: '🏥', label: 'Healthcare-first',bg: dark ? 'rgba(99,102,241,0.1)'  : 'rgba(99,102,241,0.08)'  },
  ];

  const bg = dark ? '#0b0f1a' : '#f1f5f9';
  const orbBg1 = dark ? 'rgba(99,102,241,0.11)'  : 'rgba(99,102,241,0.07)';
  const orbBg2 = dark ? 'rgba(139,92,246,0.09)'  : 'rgba(139,92,246,0.06)';
  const orbBg3 = dark ? 'rgba(236,72,153,0.06)'  : 'rgba(236,72,153,0.04)';

  const handleDashboard = useCallback(() => router.push('/dashboard'), [router]);
  const toggleDark = useCallback(() => setDark(d => !d), []);

  return (
    <div style={{ minHeight: '100vh', background: bg, fontFamily: "'Inter', -apple-system, sans-serif", color: dark ? '#f1f5f9' : '#0f172a', overflowX: 'hidden', position: 'relative' }}>
      <style>{buildCSS(dark)}</style>

      {/* ── Ambient Orbs ── */}
      <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
        <div style={{ position: 'absolute', top: '-18%', left: '-12%', width: '640px', height: '640px', borderRadius: '50%', background: `radial-gradient(circle, ${orbBg1} 0%, transparent 70%)`, animation: 'orb1 20s ease-in-out infinite' }} />
        <div style={{ position: 'absolute', bottom: '-22%', right: '-12%', width: '720px', height: '720px', borderRadius: '50%', background: `radial-gradient(circle, ${orbBg2} 0%, transparent 70%)`, animation: 'orb2 26s ease-in-out infinite' }} />
        <div style={{ position: 'absolute', top: '35%', left: '38%', width: '420px', height: '420px', borderRadius: '50%', background: `radial-gradient(circle, ${orbBg3} 0%, transparent 70%)`, animation: 'orb1 16s ease-in-out infinite reverse' }} />
      </div>

      {/* ── Dark Mode Toggle ── */}
      <button className="lm-toggle" onClick={toggleDark} aria-label="Toggle theme">
        {dark ? '☀️' : '🌙'}
      </button>

      {/* ── Navbar ── */}
      <nav className="lm-nav">
        <div className="lm-nav-inner">
          <Link href="/" className="lm-logo">
            <div className="lm-logo-icon">⚡</div>
            <span className="lm-logo-text">Lead<span>Matrix</span></span>
          </Link>
          <div className="lm-nav-links">
            <Link href="/businesses-list" className="lm-nav-ghost">Businesses</Link>
            <Link href="/rankings"        className="lm-nav-ghost">Rankings</Link>
            <Link href="/gmb-login"       className="lm-nav-ghost">Login</Link>
            <Link href="/dashboard"       className="lm-nav-pill">Dashboard →</Link>
          </div>
        </div>
      </nav>

      {/* ── Main ── */}
      <div className="lm-main">
        <div className="lm-grid">

          {/* LEFT — Hero */}
          <div className="lm-left">

            {/* Badge */}
            <div className="lm-badge">
              <span className="lm-badge-dot" />
              v4.2.0 — GMB Analytics Platform
            </div>

            {/* Title */}
            <h1 className="lm-h1">
              <span className="lm-h1-gradient">LeadMatrix</span>
              <span className="lm-h1-sub">GMB Intelligence<br />Platform</span>
            </h1>

            {/* Subtitle */}
            <p className="lm-subtitle">
              Track rankings, monitor reviews, and unlock deep GMB analytics for healthcare businesses — all in one place.
            </p>

            {/* CTAs */}
            <div className="lm-ctas">
              <button className="lm-btn-primary" onClick={handleDashboard}>
                🚀 Go to Dashboard
              </button>
              <Link href="/gmb-login" className="lm-btn-secondary">
                🔑 Connect GMB
              </Link>
            </div>

            {/* Pills */}
            <div className="lm-pills">
              {pills.map((p, i) => (
                <div key={i} className="lm-pill" style={{ background: p.bg }}>
                  {p.icon} {p.label}
                </div>
              ))}
            </div>

            {/* Features */}
            <div style={{ width: '100%' }}>
              <div className="lm-features-label">Platform Capabilities</div>
              <div className="lm-features-grid">
                {features.map((f, i) => (
                  <div key={i} className="lm-feature-item">
                    <div className="lm-feature-icon">{f.icon}</div>
                    <div>
                      <div className="lm-feature-title">{f.title}</div>
                      <div className="lm-feature-desc">{f.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT — Metrics Card */}
          <div className="lm-card">

            {/* Card Header */}
            <div className="lm-card-header">
              <div>
                <div className="lm-card-title">Platform Metrics</div>
                <div className="lm-card-sub">Live data · Updated in real-time</div>
              </div>
              <div className="lm-live-badge">
                <div className="lm-live-dot" />
                <span className="lm-live-text">LIVE</span>
              </div>
            </div>

            {/* Stats */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', marginBottom: '20px' }}>
              {stats.map((stat, i) => (
                <StatCard
                  key={i}
                  stat={stat}
                  index={i}
                  hoveredStat={hoveredStat}
                  setHoveredStat={setHoveredStat}
                  dark={dark}
                />
              ))}
            </div>

            <div className="lm-divider" />

            {/* Quick Links */}
            <div style={{ marginBottom: '20px' }}>
              <div className="lm-ql-label">Quick Access</div>
              <div className="lm-ql-grid">
                {quickLinks.map((l, i) => (
                  <Link key={i} href={l.href} className="lm-ql-item">
                    <div className="lm-ql-icon" style={{ background: `${l.color}14` }}>{l.icon}</div>
                    <span className="lm-ql-label-text">{l.label}</span>
                  </Link>
                ))}
              </div>
            </div>

            <div className="lm-divider" />

            {/* Main CTA */}
            <button className="lm-main-cta" onClick={handleDashboard}>
              Open Dashboard <span>→</span>
            </button>

            {/* Trust line */}
            <div className="lm-trust">
              Trusted by <strong>Digiscrub</strong> · Managing <strong>44+</strong> healthcare listings
            </div>
          </div>
        </div>
      </div>

      {/* ── Footer ── */}
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
