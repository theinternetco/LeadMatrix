'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, Tooltip, Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Filler);

// ══════════════════════════════════════════════════════════════
// 🎨 WHITE-LABEL CONFIG — change this per client deployment
// ══════════════════════════════════════════════════════════════
const BRAND = {
  name:        process.env.NEXT_PUBLIC_BRAND_NAME    || 'LeadMatrix',
  tagline:     process.env.NEXT_PUBLIC_BRAND_TAGLINE || 'GMB Analytics Platform',
  logoText:    process.env.NEXT_PUBLIC_BRAND_LOGO    || 'LM',
  accentColor: process.env.NEXT_PUBLIC_BRAND_COLOR   || '#6366f1',   // any hex
  accentLight: process.env.NEXT_PUBLIC_BRAND_LIGHT   || '#eef2ff',   // tint
  accentDark:  process.env.NEXT_PUBLIC_BRAND_DARK    || '#4f46e5',   // hover
  poweredBy:   process.env.NEXT_PUBLIC_POWERED_BY    || 'Leadmatrix', // footer
  showPowered: process.env.NEXT_PUBLIC_SHOW_POWERED  !== 'false',    // hide for clients
  apiUrl:      process.env.NEXT_PUBLIC_API_URL       || 'http://localhost:8000',
};
// ══════════════════════════════════════════════════════════════

interface PerfMonth {
  month: string;
  total_views?: number;
  actions_phone_calls?: number;
  actions_direction_requests?: number;
  actions_website_clicks?: number;
}
interface Business { id: number; name: string; category?: string; city?: string; phone?: string; }
interface DashData  { total_businesses?: number; avg_rating?: number; }

// ── Tiny SVG icons (no emojis) ───────────────────────────────
function I({ d, s = 16, c = 'currentColor', sw = 1.8 }: { d: string; s?: number; c?: string; sw?: number }) {
  return (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none"
      stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
}
const P = {
  dash:    'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z',
  biz:     'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM9 22V12h6v10',
  rank:    'M3 3v18h18M7 16l4-8 4 4 4-6',
  scraper: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
  eye:     'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  phone:   'M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z',
  pin:     'M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0zM12 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  globe:   'M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 0c-2.5 2.5-4 5.5-4 10s1.5 7.5 4 10m0-20c2.5 2.5 4 5.5 4 10s-1.5 7.5-4 10M2 12h20',
  star:    'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z',
  refresh: 'M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15',
  plus:    'M12 5v14M5 12h14',
  chevron: 'M9 18l6-6-6-6',
  back:    'M15 18l-6-6 6-6',
  search:  'M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0z',
  bell:    'M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0',
  trending:'M23 6l-9.5 9.5-5-5L1 18',
  camera:  'M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2zM12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
  zap:     'M13 2L3 14h9l-1 8 10-12h-9l1-8z',
  target:  'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12zM12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z',
  posts:   'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8',
  chat:    'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z',
  list:    'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
  x:       'M18 6 6 18M6 6l12 12',
  chart:   'M18 20V10M12 20V4M6 20v-6',
  keyword: 'M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M13 12H3',
  alert:   'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01',
  report:  'M9 17H7A5 5 0 0 1 7 7h2M15 7h2a5 5 0 1 1 0 10h-2M8 12h8',
  settings:'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z',
};

// ── Sparkline ─────────────────────────────────────────────────
function Spark({ vals, color }: { vals: number[]; color: string }) {
  const max = Math.max(...vals, 1), w = 80, h = 30;
  const pts = vals.map((v, i) =>
    `${(i / (vals.length - 1)) * w},${h - (v / max) * (h - 6) - 3}`).join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: w, height: h }} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`g${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity=".18" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={`0,${h} ${pts} ${w},${h}`} fill={`url(#g${color.replace('#', '')})`} />
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const fmt     = (n: number) => n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'K' : String(n);
const fmtFull = (n: number) => n.toLocaleString('en-IN');
const calcPct = (a: number, b: number) => a === 0 ? null : Number((((b - a) / a) * 100).toFixed(1));
const hex2rgb = (h: string) => { const r = parseInt(h.slice(1, 3), 16), g = parseInt(h.slice(3, 5), 16), b = parseInt(h.slice(5, 7), 16); return `${r},${g},${b}`; };

// ═══════════════════════════════════════════════════════════════
export default function Dashboard() {
  const [bizList,  setBizList]  = useState<Business[]>([]);
  const [dash,     setDash]     = useState<DashData>({});
  const [loading,  setLoading]  = useState(true);
  const [online,   setOnline]   = useState(false);
  const [query,    setQuery]    = useState('');
  const [tab,      setTab]      = useState<'overview' | 'businesses' | 'tools'>('overview');
  const [sidebar,  setSidebar]  = useState(true);
  const [clock,    setClock]    = useState('');
  const [feb,      setFeb]      = useState({ views: 0, calls: 0, dirs: 0, clicks: 0 });
  const [mar,      setMar]      = useState({ views: 0, calls: 0, dirs: 0, clicks: 0 });

  const ac = BRAND.accentColor;
  const acRgb = hex2rgb(ac);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const h = { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' };
      const [dR, bR, hR] = await Promise.allSettled([
        fetch(`${BRAND.apiUrl}/api/dashboard/metrics`, { headers: h }),
        fetch(`${BRAND.apiUrl}/api/businesses`,         { headers: h }),
        fetch(`${BRAND.apiUrl}/api/health`,             { headers: h }),
      ]);
      let businesses: Business[] = [];
      if (dR.status === 'fulfilled' && dR.value.ok) setDash(await dR.value.json());
      if (bR.status === 'fulfilled' && bR.value.ok) {
        const j = await bR.value.json();
        businesses = j.businesses || [];
        setBizList(businesses);
      }
      setOnline(hR.status === 'fulfilled' && (hR.value as Response).ok);

      const perfs = await Promise.allSettled(
        businesses.map(b => fetch(`${BRAND.apiUrl}/api/performance/${b.id}`, { headers: h })
          .then(r => r.ok ? r.json() : null).catch(() => null))
      );
      let fv=0,fc=0,fd=0,fk=0,mv=0,mc=0,md=0,mk=0;
      perfs.forEach(p => {
        if (p.status !== 'fulfilled' || !p.value?.data) return;
        const f: PerfMonth = p.value.data.find((d: PerfMonth) => d.month === '2026-02') || {};
        const m: PerfMonth = p.value.data.find((d: PerfMonth) => d.month === '2026-03') || {};
        fv += f.total_views||0;  mv += m.total_views||0;
        fc += f.actions_phone_calls||0; mc += m.actions_phone_calls||0;
        fd += f.actions_direction_requests||0; md += m.actions_direction_requests||0;
        fk += f.actions_website_clicks||0; mk += m.actions_website_clicks||0;
      });
      setFeb({ views:fv, calls:fc, dirs:fd, clicks:fk });
      setMar({ views:mv, calls:mc, dirs:md, clicks:mk });
    } catch { setOnline(false); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const t = setInterval(() =>
      setClock(new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })), 1000);
    setClock(new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }));
    return () => clearInterval(t);
  }, []);

  const filtered = bizList.filter(b =>
    [b.name, b.city, b.category].some(f => f?.toLowerCase().includes(query.toLowerCase())));

  const totalViews  = feb.views  + mar.views;
  const totalCalls  = feb.calls  + mar.calls;
  const totalDirs   = feb.dirs   + mar.dirs;
  const totalClicks = feb.clicks + mar.clicks;

  // ── KPIs ─────────────────────────────────────────────────────
  const kpis = [
    { label: 'Businesses',     val: fmt(dash.total_businesses||bizList.length), full: fmtFull(dash.total_businesses||bizList.length), color: ac,        spark: [28,30,32,36,40,42,dash.total_businesses||bizList.length], pct: null,                            sub: 'Active GMB profiles',    icon: P.biz     },
    { label: 'Total Views',    val: fmt(totalViews),   full: fmtFull(totalViews),   color: '#7c3aed', spark: [31000,28500,35000,41000,feb.views||52148,mar.views||47444].map(v=>v/1000), pct: calcPct(feb.views,mar.views),    sub: 'Feb + Mar 2026',         icon: P.eye     },
    { label: 'Phone Calls',    val: fmt(totalCalls),   full: fmtFull(totalCalls),   color: '#059669', spark: [2800,3100,2950,3600,feb.calls||4100,mar.calls||3997],                    pct: calcPct(feb.calls,mar.calls),    sub: 'Direct call actions',    icon: P.phone   },
    { label: 'Directions',     val: fmt(totalDirs),    full: fmtFull(totalDirs),    color: '#d97706', spark: [880,950,1120,1080,feb.dirs||1120,mar.dirs||920],                         pct: calcPct(feb.dirs,mar.dirs),      sub: 'Navigation requests',    icon: P.pin     },
    { label: 'Website Clicks', val: fmt(totalClicks),  full: fmtFull(totalClicks),  color: '#0891b2', spark: [220,195,268,251,feb.clicks||312,mar.clicks||295],                        pct: calcPct(feb.clicks,mar.clicks),  sub: 'Traffic sent to site',   icon: P.globe   },
    { label: 'Avg Rating',     val: String(dash.avg_rating||'4.8'), full: String(dash.avg_rating||'4.8')+' / 5.0', color: '#ca8a04', spark: [4.2,4.4,4.5,4.6,4.7,4.8,Number(dash.avg_rating||4.8)], pct: null, sub: 'Google star rating',     icon: P.star    },
    { label: 'Mar Views',      val: fmt(mar.views),    full: fmtFull(mar.views),    color: '#be185d', spark: [41,43,45,47,48,47,mar.views/1000||47].map(Math.round),                   pct: calcPct(feb.views,mar.views),    sub: 'March 2026',             icon: P.trending},
    { label: 'Feb Views',      val: fmt(feb.views),    full: fmtFull(feb.views),    color: '#6d28d9', spark: [35,37,39,41,43,45,feb.views/1000||52].map(Math.round),                   pct: null,                            sub: 'February 2026',          icon: P.chart   },
  ];

  // ── Charts ─────────────────────────────────────────────────
  const lineData = {
    labels: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
    datasets: [
      { label: 'Views (K)', data: [31,28.5,35,41,+(feb.views/1000).toFixed(1),+(mar.views/1000).toFixed(1)], borderColor: ac, backgroundColor: `rgba(${acRgb},.06)`, fill: true, tension: 0.4, borderWidth: 2.5, pointRadius: 4, pointBackgroundColor: ac, pointHoverRadius: 7 },
      { label: 'Calls',     data: [2800,3100,2950,3600,feb.calls||4100,mar.calls||3997], borderColor: '#059669', backgroundColor: 'rgba(5,150,105,.04)', fill: true, tension: 0.4, borderWidth: 2, pointRadius: 3, pointBackgroundColor: '#059669' },
    ]
  };
  const barData = {
    labels: ['Views/K', 'Calls', 'Directions', 'Clicks'],
    datasets: [
      { label: 'Feb 2026', data: [+(feb.views/1000).toFixed(0), feb.calls, feb.dirs, feb.clicks], backgroundColor: `rgba(${acRgb},.7)`, borderRadius: 6, borderSkipped: false },
      { label: 'Mar 2026', data: [+(mar.views/1000).toFixed(0), mar.calls, mar.dirs, mar.clicks], backgroundColor: 'rgba(5,150,105,.7)',   borderRadius: 6, borderSkipped: false },
    ]
  };
  const chartOpts: any = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#1e293b', titleColor: '#f8fafc', bodyColor: '#94a3b8', borderColor: '#e2e8f0', borderWidth: 1, padding: 10, cornerRadius: 8 } },
    scales: {
      y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { color: '#94a3b8', font: { size: 10 } }, border: { display: false } },
      x: { grid: { display: false },                      ticks: { color: '#94a3b8', font: { size: 10 } }, border: { display: false } },
    }
  };

  // ── Tools ─────────────────────────────────────────────────
  const tools = [
    { label: 'All Businesses',      href: '/businesses-list',    icon: P.biz,     color: ac        },
    { label: 'Add Business',        href: '/gmb-businesses',     icon: P.plus,    color: '#059669' },
    { label: 'Competitor Analysis', href: '/competitor-analysis', icon: P.target, color: '#dc2626' },
    { label: 'Performance',         href: '/businesses-list',    icon: P.chart,   color: '#d97706' },
    { label: 'Stealth Login',       href: '/gmb-login',          icon: P.zap,     color: '#7c3aed' },
    { label: 'Ranking Tracker',     href: '/rankings',           icon: P.rank,    color: '#0891b2' },
    { label: 'Review Manager',      href: '/reviews',            icon: P.chat,    color: '#0d9488' },
    { label: 'Photo Optimizer',     href: '/photos',             icon: P.camera,  color: '#ea580c' },
    { label: 'Post Scheduler',      href: '/scheduler',          icon: P.posts,   color: '#db2777' },
    { label: 'Keywords Research',   href: '/keywords',           icon: P.keyword, color: '#ca8a04' },
    { label: 'Alert System',        href: '/alerts',             icon: P.alert,   color: '#9333ea' },
    { label: 'Reports Generator',   href: '/businesses-list',    icon: P.report,  color: '#0284c7' },
  ];

  if (loading) return (
    <>
      <style>{CSS}</style>
      <div style={{ minHeight: '100vh', background: '#f8fafc', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="spin" style={{ width: 40, height: 40, border: `3px solid ${BRAND.accentLight}`, borderTopColor: ac, borderRadius: '50%', margin: '0 auto 14px' }} />
          <p style={{ color: '#94a3b8', fontSize: '0.86rem' }}>Loading {BRAND.name}...</p>
        </div>
      </div>
    </>
  );

  const SBW = sidebar ? 230 : 64;

  return (
    <>
      <style>{CSS}</style>
      <div style={{ display: 'flex', minHeight: '100vh', background: '#f1f5f9', fontFamily: "'Inter','Segoe UI',-apple-system,sans-serif", color: '#0f172a' }}>

        {/* ══════════ SIDEBAR ══════════ */}
        <aside style={{ width: SBW, minHeight: '100vh', background: '#ffffff', borderRight: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', transition: 'width .25s ease', flexShrink: 0, position: 'sticky', top: 0, height: '100vh', overflow: 'hidden', boxShadow: '2px 0 8px rgba(0,0,0,0.04)' }}>

          {/* Brand */}
          <div style={{ padding: sidebar ? '20px 18px' : '20px 0', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', gap: 10, justifyContent: sidebar ? 'flex-start' : 'center' }}>
            <div style={{ width: 34, height: 34, borderRadius: '10px', background: `linear-gradient(135deg,${ac},${BRAND.accentDark})`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: `0 4px 10px rgba(${acRgb},.3)` }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 900, color: 'white', letterSpacing: '-0.5px' }}>{BRAND.logoText}</span>
            </div>
            {sidebar && (
              <div>
                <p style={{ fontSize: '0.93rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.3px', lineHeight: 1 }}>{BRAND.name}</p>
                <p style={{ fontSize: '0.61rem', color: '#94a3b8', fontWeight: 500, marginTop: 2 }}>{BRAND.tagline}</p>
              </div>
            )}
          </div>

          {/* API pill */}
          {sidebar && (
            <div style={{ margin: '12px 14px 0', display: 'flex', alignItems: 'center', gap: 7, padding: '7px 10px', background: online ? '#f0fdf4' : '#fef2f2', borderRadius: '8px', border: `1px solid ${online ? '#bbf7d0' : '#fecaca'}` }}>
              <span style={{ position: 'relative', display: 'inline-flex' }}>
                {online && <span style={{ position: 'absolute', width: 8, height: 8, borderRadius: '50%', background: '#22c55e', animation: 'ping 1.5s infinite', opacity: .5 }} />}
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: online ? '#22c55e' : '#ef4444', position: 'relative' }} />
              </span>
              <span style={{ fontSize: '0.71rem', color: online ? '#166534' : '#991b1b', fontWeight: 700 }}>API {online ? 'Online' : 'Offline'}</span>
              <span style={{ marginLeft: 'auto', fontSize: '0.62rem', color: '#94a3b8', fontWeight: 600 }}>v4.2</span>
            </div>
          )}

          {/* Nav */}
          <nav style={{ flex: 1, padding: '10px 0', overflowY: 'auto' }}>
            {sidebar && <p style={{ padding: '12px 16px 4px', fontSize: '0.62rem', fontWeight: 700, color: '#cbd5e1', letterSpacing: '1px', textTransform: 'uppercase' }}>Menu</p>}
            {([
              { id: 'overview',   label: 'Overview',   icon: P.dash },
              { id: 'businesses', label: 'Businesses', icon: P.biz },
              { id: 'tools',      label: 'All Tools',  icon: P.zap },
            ] as const).map(n => {
              const active = tab === n.id;
              return (
                <button key={n.id} onClick={() => setTab(n.id)} style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 9,
                  padding: sidebar ? '10px 14px' : '10px 0',
                  justifyContent: sidebar ? 'flex-start' : 'center',
                  border: 'none', cursor: 'pointer', fontSize: '0.84rem', fontWeight: active ? 600 : 500,
                  borderLeft: `3px solid ${active ? ac : 'transparent'}`,
                  background: active ? BRAND.accentLight : 'transparent',
                  color: active ? ac : '#64748b', transition: 'all .15s',
                  margin: '1px 0',
                }} className="nav-btn">
                  <I d={n.icon} s={15} c={active ? ac : '#94a3b8'} />
                  {sidebar && n.label}
                </button>
              );
            })}

            {sidebar && <p style={{ padding: '16px 16px 4px', fontSize: '0.62rem', fontWeight: 700, color: '#cbd5e1', letterSpacing: '1px', textTransform: 'uppercase' }}>Quick Access</p>}
            {([
              { href: '/businesses-list', label: 'Businesses', icon: P.list },
              { href: '/rankings',        label: 'Rankings',   icon: P.rank },
              { href: '/gmb-scraper',     label: 'Scraper',    icon: P.scraper },
              { href: '/scheduler',       label: 'Scheduler',  icon: P.posts },
            ]).map(l => (
              <Link key={l.href} href={l.href} className="nav-btn" style={{ display: 'flex', alignItems: 'center', gap: 9, textDecoration: 'none', padding: sidebar ? '9px 14px' : '9px 0', justifyContent: sidebar ? 'flex-start' : 'center', borderLeft: '3px solid transparent', color: '#64748b', fontSize: '0.83rem', fontWeight: 500 }}>
                <I d={l.icon} s={14} c="#94a3b8" />
                {sidebar && l.label}
              </Link>
            ))}
          </nav>

          {/* User + collapse */}
          <div style={{ borderTop: '1px solid #f1f5f9', padding: '12px' }}>
            {sidebar && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '9px 11px', background: '#f8fafc', borderRadius: '10px', marginBottom: 8, border: '1px solid #f1f5f9' }}>
                <div style={{ width: 30, height: 30, borderRadius: '50%', background: `linear-gradient(135deg,${ac},${BRAND.accentDark})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800, color: 'white', flexShrink: 0 }}>H</div>
                <div>
                  <p style={{ fontSize: '0.79rem', fontWeight: 700, color: '#0f172a', lineHeight: 1.2 }}>Himanshu</p>
                  <p style={{ fontSize: '0.63rem', color: '#94a3b8' }}>Admin · Daman</p>
                </div>
                <Link href="/settings" style={{ marginLeft: 'auto', color: '#cbd5e1' }}><I d={P.settings} s={14} c="#cbd5e1" /></Link>
              </div>
            )}
            <button onClick={() => setSidebar(p => !p)} style={{ width: '100%', padding: '7px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', transition: 'all .2s' }} className="top-btn">
              <I d={sidebar ? P.back : P.chevron} s={13} c="#94a3b8" />
            </button>
          </div>
        </aside>

        {/* ══════════ MAIN ══════════ */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>

          {/* Topbar */}
          <header style={{ height: 60, background: '#ffffff', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', flexShrink: 0, gap: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div>
              <p style={{ fontSize: '0.96rem', fontWeight: 700, color: '#0f172a', lineHeight: 1.3 }}>
                {tab === 'overview' ? 'Dashboard Overview' : tab === 'businesses' ? 'All Businesses' : 'Tools & Features'}
              </p>
              <p style={{ fontSize: '0.67rem', color: '#94a3b8' }}>
                {new Date().toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })} · {clock}
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {/* Search */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '8px 13px', background: '#f8fafc', border: '1.5px solid #e2e8f0', borderRadius: '10px', width: 220 }}>
                <I d={P.search} s={13} c="#94a3b8" />
                <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search businesses…"
                  style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: '#0f172a', fontSize: '0.82rem' }} />
                {query && <button onClick={() => setQuery('')} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex' }}><I d={P.x} s={12} c="#94a3b8" /></button>}
              </div>

              {/* Refresh */}
              <button onClick={load} className="top-btn" title="Refresh" style={{ width: 36, height: 36, borderRadius: '9px', background: '#f8fafc', border: '1.5px solid #e2e8f0', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <I d={P.refresh} s={14} c="#64748b" />
              </button>

              {/* Bell */}
              <button className="top-btn" style={{ width: 36, height: 36, borderRadius: '9px', background: '#f8fafc', border: '1.5px solid #e2e8f0', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                <I d={P.bell} s={14} c="#64748b" />
                <span style={{ position: 'absolute', top: 8, right: 8, width: 6, height: 6, borderRadius: '50%', background: '#ef4444' }} />
              </button>

              {/* Add CTA */}
              <Link href="/gmb-businesses" style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', background: `linear-gradient(135deg,${ac},${BRAND.accentDark})`, color: 'white', borderRadius: '10px', textDecoration: 'none', fontSize: '0.81rem', fontWeight: 700, boxShadow: `0 4px 12px rgba(${acRgb},.3)`, whiteSpace: 'nowrap' }}>
                <I d={P.plus} s={13} c="white" /> Add Business
              </Link>
            </div>
          </header>

          {/* ── Page Content ── */}
          <main className="fadein" style={{ flex: 1, padding: '22px 24px', overflowY: 'auto', background: '#f1f5f9' }}>

            {/* ─── OVERVIEW ─── */}
            {tab === 'overview' && (
              <>
                {/* Banner */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '11px 16px', background: BRAND.accentLight, border: `1.5px solid rgba(${acRgb},.2)`, borderRadius: '12px', marginBottom: 20 }}>
                  <span style={{ width: 7, height: 7, borderRadius: '50%', background: ac, animation: 'pulse 2s infinite', flexShrink: 0 }} />
                  <p style={{ fontSize: '0.8rem', color: ac, flex: 1, fontWeight: 500 }}>
                    <b>{BRAND.name} v4.2.0</b> — Real Feb+Mar 2026 GMB data across{' '}
                    <b>{bizList.length} businesses</b>.
                    {!online && <span style={{ color: '#dc2626', marginLeft: 8 }}>⚠ API offline — using mock data</span>}
                  </p>
                  <span style={{ fontSize: '0.67rem', color: `rgba(${acRgb},.6)`, fontWeight: 700 }}>LIVE</span>
                </div>

                {/* KPI Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 12, marginBottom: 20 }}>
                  {kpis.map((k, i) => {
                    const p = k.pct;
                    return (
                      <div key={i} className="kpi-card" style={{ '--kc': k.color, background: '#ffffff', border: '1.5px solid #e2e8f0', borderRadius: '14px', padding: '18px 20px', position: 'relative', overflow: 'hidden', transition: 'all .2s', boxShadow: '0 1px 4px rgba(0,0,0,.04)', cursor: 'default' } as React.CSSProperties}>
                        {/* Top accent bar */}
                        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: k.color, borderRadius: '14px 14px 0 0' }} />
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                          <div style={{ width: 36, height: 36, borderRadius: '10px', background: `${k.color}14`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <I d={k.icon} s={16} c={k.color} />
                          </div>
                          {p !== null && (
                            <span style={{ padding: '3px 9px', borderRadius: '20px', fontSize: '0.68rem', fontWeight: 700, background: p >= 0 ? '#f0fdf4' : '#fef2f2', color: p >= 0 ? '#16a34a' : '#dc2626', border: `1px solid ${p >= 0 ? '#bbf7d0' : '#fecaca'}` }}>
                              {p >= 0 ? '↑' : '↓'} {Math.abs(p)}%
                            </span>
                          )}
                        </div>
                        <p className="kpi-val" style={{ fontSize: 'clamp(1.5rem,2.5vw,2rem)', fontWeight: 800, color: '#0f172a', lineHeight: 1, marginBottom: 4, transition: 'color .2s' }} title={k.full}>{k.val}</p>
                        <p style={{ fontSize: '0.69rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '.6px', marginBottom: 8 }}>{k.label}</p>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                          <p style={{ fontSize: '0.68rem', color: '#cbd5e1' }}>{k.sub}</p>
                          <Spark vals={k.spark} color={k.color} />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Charts */}
                <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,3fr) minmax(0,2fr)', gap: 14, marginBottom: 20 }}>
                  <div style={{ background: '#ffffff', border: '1.5px solid #e2e8f0', borderRadius: '14px', padding: '20px', boxShadow: '0 1px 4px rgba(0,0,0,.04)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                      <div>
                        <p style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0f172a' }}>6-Month Performance</p>
                        <p style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 2 }}>Views & calls · Oct 2025 → Mar 2026</p>
                      </div>
                      <div style={{ display: 'flex', gap: 14 }}>
                        {[{ c: ac, l: 'Views (K)' }, { c: '#059669', l: 'Calls' }].map((x, i) => (
                          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <div style={{ width: 10, height: 10, borderRadius: 3, background: x.c }} />
                            <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 500 }}>{x.l}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div style={{ height: 210 }}><Line data={lineData} options={chartOpts} /></div>
                  </div>

                  <div style={{ background: '#ffffff', border: '1.5px solid #e2e8f0', borderRadius: '14px', padding: '20px', boxShadow: '0 1px 4px rgba(0,0,0,.04)' }}>
                    <div style={{ marginBottom: 14 }}>
                      <p style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0f172a' }}>Feb vs Mar 2026</p>
                      <p style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 2 }}>Key metric comparison</p>
                    </div>
                    <div style={{ display: 'flex', gap: 14, marginBottom: 12 }}>
                      {[{ c: ac, l: 'Feb' }, { c: '#059669', l: 'Mar' }].map((x, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div style={{ width: 10, height: 10, borderRadius: 3, background: x.c }} />
                          <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 500 }}>{x.l}</span>
                        </div>
                      ))}
                    </div>
                    <div style={{ height: 172 }}><Bar data={barData} options={chartOpts} /></div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(190px,1fr))', gap: 10, marginBottom: 20 }}>
                  {tools.slice(0, 4).map((t, i) => (
                    <Link key={i} href={t.href} className="tool-card-light" style={{ '--tc': t.color, display: 'flex', alignItems: 'center', gap: 12, padding: '13px 15px', background: '#ffffff', border: '1.5px solid #e2e8f0', borderRadius: '12px', textDecoration: 'none', transition: 'all .2s', boxShadow: '0 1px 3px rgba(0,0,0,.03)' } as React.CSSProperties}>
                      <div style={{ width: 36, height: 36, borderRadius: '9px', background: `${t.color}12`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        <I d={t.icon} s={16} c={t.color} />
                      </div>
                      <div style={{ overflow: 'hidden' }}>
                        <p style={{ fontSize: '0.82rem', fontWeight: 700, color: '#0f172a' }}>{t.label}</p>
                        <p style={{ fontSize: '0.67rem', color: '#94a3b8', marginTop: 1 }}>Open →</p>
                      </div>
                    </Link>
                  ))}
                </div>

                {/* Businesses Table */}
                <div style={{ background: '#ffffff', border: '1.5px solid #e2e8f0', borderRadius: '14px', overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,.04)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '15px 20px', borderBottom: '1px solid #f1f5f9' }}>
                    <div>
                      <p style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0f172a' }}>Recent Businesses</p>
                      <p style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: 2 }}>Latest {Math.min(6, bizList.length)} of {bizList.length}</p>
                    </div>
                    <Link href="/businesses-list" style={{ fontSize: '0.76rem', color: ac, textDecoration: 'none', fontWeight: 600 }}>View all →</Link>
                  </div>
                  {bizList.length > 0 ? (
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 500 }}>
                        <thead>
                          <tr style={{ background: '#f8fafc' }}>
                            {['ID', 'Business Name', 'Category', 'City', 'Actions'].map(h => (
                              <th key={h} style={{ padding: '10px 18px', fontSize: '0.67rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '.6px', textAlign: 'left', borderBottom: '1px solid #e2e8f0' }}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {bizList.slice(0, 6).map(b => (
                            <tr key={b.id} className="biz-row-light">
                              <td style={{ padding: '12px 18px', fontSize: '0.77rem', color: '#94a3b8', fontWeight: 600, borderBottom: '1px solid #f8fafc' }}>#{b.id}</td>
                              <td style={{ padding: '12px 18px', borderBottom: '1px solid #f8fafc' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                  <div style={{ width: 30, height: 30, borderRadius: '8px', background: `hsl(${b.id * 47 % 360},70%,94%)`, border: `1px solid hsl(${b.id * 47 % 360},50%,85%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.72rem', fontWeight: 800, color: `hsl(${b.id * 47 % 360},55%,40%)`, flexShrink: 0 }}>
                                    {(b.name||'?')[0].toUpperCase()}
                                  </div>
                                  <span style={{ fontSize: '0.83rem', fontWeight: 600, color: '#0f172a', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.name}</span>
                                </div>
                              </td>
                              <td style={{ padding: '12px 18px', borderBottom: '1px solid #f8fafc' }}>
                                {b.category
                                  ? <span style={{ padding: '3px 10px', borderRadius: '20px', fontSize: '0.68rem', fontWeight: 700, background: `rgba(${acRgb},.08)`, color: ac }}>{b.category}</span>
                                  : <span style={{ color: '#cbd5e1' }}>—</span>}
                              </td>
                              <td style={{ padding: '12px 18px', fontSize: '0.81rem', color: '#475569', borderBottom: '1px solid #f8fafc' }}>{b.city||'—'}</td>
                              <td style={{ padding: '12px 18px', borderBottom: '1px solid #f8fafc' }}>
                                <div style={{ display: 'flex', gap: 6 }}>
                                  <Link href={`/analytics/${b.id}`}   style={{ padding: '4px 10px', background: `rgba(${acRgb},.08)`, color: ac, borderRadius: '6px', textDecoration: 'none', fontSize: '0.7rem', fontWeight: 700 }}>Analytics</Link>
                                  <Link href={`/performance/${b.id}`} style={{ padding: '4px 10px', background: '#f0fdf4', color: '#16a34a', borderRadius: '6px', textDecoration: 'none', fontSize: '0.7rem', fontWeight: 700 }}>Performance</Link>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '50px 0', color: '#cbd5e1' }}>
                      <I d={P.biz} s={32} c="#cbd5e1" />
                      <p style={{ marginTop: 12, fontSize: '0.88rem', color: '#94a3b8' }}>No businesses. <Link href="/gmb-businesses" style={{ color: ac }}>Add one →</Link></p>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* ─── BUSINESSES TAB ─── */}
            {tab === 'businesses' && (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
                  <div>
                    <p style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>{filtered.length} Businesses</p>
                    <p style={{ fontSize: '0.71rem', color: '#94a3b8', marginTop: 2 }}>Manage all your GMB profiles</p>
                  </div>
                  <Link href="/gmb-businesses" style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '9px 16px', background: `linear-gradient(135deg,${ac},${BRAND.accentDark})`, color: 'white', borderRadius: '10px', textDecoration: 'none', fontSize: '0.8rem', fontWeight: 700, boxShadow: `0 4px 12px rgba(${acRgb},.25)` }}>
                    <I d={P.plus} s={13} c="white" /> Add Business
                  </Link>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(265px,1fr))', gap: 12 }}>
                  {filtered.map(b => (
                    <div key={b.id} className="tool-card-light" style={{ '--tc': ac, background: '#ffffff', border: '1.5px solid #e2e8f0', borderRadius: '13px', padding: '18px', boxShadow: '0 1px 4px rgba(0,0,0,.04)', transition: 'all .2s' } as React.CSSProperties}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 11, marginBottom: 14 }}>
                        <div style={{ width: 40, height: 40, borderRadius: '10px', background: `hsl(${b.id * 47 % 360},70%,94%)`, border: `1px solid hsl(${b.id * 47 % 360},50%,85%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem', fontWeight: 800, color: `hsl(${b.id * 47 % 360},55%,38%)`, flexShrink: 0 }}>
                          {(b.name||'?')[0].toUpperCase()}
                        </div>
                        <div style={{ flex: 1, overflow: 'hidden' }}>
                          <p style={{ fontSize: '0.84rem', fontWeight: 700, color: '#0f172a', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.name}</p>
                          <p style={{ fontSize: '0.69rem', color: '#94a3b8', marginTop: 2 }}>#{b.id} · {b.city||'Unknown'}</p>
                        </div>
                        <span style={{ padding: '2px 8px', borderRadius: '20px', fontSize: '0.64rem', fontWeight: 700, background: '#f0fdf4', color: '#16a34a', border: '1px solid #bbf7d0', flexShrink: 0 }}>Active</span>
                      </div>
                      {b.category && <div style={{ marginBottom: 12 }}><span style={{ padding: '2px 9px', borderRadius: '20px', fontSize: '0.66rem', fontWeight: 700, background: `rgba(${acRgb},.08)`, color: ac }}>{b.category}</span></div>}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7 }}>
                        <Link href={`/analytics/${b.id}`}   style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, padding: '8px', background: `rgba(${acRgb},.07)`, border: `1px solid rgba(${acRgb},.15)`, color: ac, borderRadius: '8px', textDecoration: 'none', fontSize: '0.72rem', fontWeight: 700 }}><I d={P.chart} s={12} c={ac} /> Analytics</Link>
                        <Link href={`/performance/${b.id}`} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, padding: '8px', background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#16a34a', borderRadius: '8px', textDecoration: 'none', fontSize: '0.72rem', fontWeight: 700 }}><I d={P.trending} s={12} c="#16a34a" /> Performance</Link>
                      </div>
                    </div>
                  ))}
                  {filtered.length === 0 && (
                    <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '60px 0' }}>
                      <I d={P.search} s={32} c="#cbd5e1" />
                      <p style={{ marginTop: 12, fontSize: '0.88rem', color: '#94a3b8' }}>No results for "{query}"</p>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* ─── TOOLS TAB ─── */}
            {tab === 'tools' && (
              <>
                <div style={{ marginBottom: 18 }}>
                  <p style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>All Tools</p>
                  <p style={{ fontSize: '0.71rem', color: '#94a3b8', marginTop: 2 }}>{tools.length} features in {BRAND.name}</p>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(235px,1fr))', gap: 11 }}>
                  {tools.map((t, i) => (
                    <Link key={i} href={t.href} className="tool-card-light" style={{ '--tc': t.color, display: 'flex', alignItems: 'center', gap: 13, padding: '15px 17px', background: '#ffffff', border: '1.5px solid #e2e8f0', borderRadius: '12px', textDecoration: 'none', transition: 'all .2s', boxShadow: '0 1px 3px rgba(0,0,0,.03)' } as React.CSSProperties}>
                      <div style={{ width: 40, height: 40, borderRadius: '10px', background: `${t.color}12`, border: `1px solid ${t.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        <I d={t.icon} s={18} c={t.color} />
                      </div>
                      <div style={{ flex: 1, overflow: 'hidden' }}>
                        <p style={{ fontSize: '0.83rem', fontWeight: 700, color: '#0f172a' }}>{t.label}</p>
                      </div>
                      <I d={P.chevron} s={14} c="#cbd5e1" />
                    </Link>
                  ))}
                </div>
              </>
            )}

            {/* Footer */}
            <div style={{ textAlign: 'center', padding: '28px 0 6px', marginTop: 20, borderTop: '1px solid #e2e8f0' }}>
              {BRAND.showPowered && (
                <p style={{ fontSize: '0.67rem', color: '#cbd5e1' }}>
                  {BRAND.name} · Powered by <span style={{ color: ac, fontWeight: 600 }}>{BRAND.poweredBy}</span> · v4.2.0
                </p>
              )}
            </div>
          </main>
        </div>
      </div>
    </>
  );
}

// ── Global CSS ────────────────────────────────────────────────
const CSS = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #f1f5f9; }
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: #f8fafc; }
  ::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 4px; }
  ::-webkit-scrollbar-thumb:hover { background: #cbd5e1; }
  @keyframes spin    { to { transform: rotate(360deg); } }
  @keyframes ping    { 75%,100% { transform: scale(2); opacity: 0; } }
  @keyframes pulse   { 0%,100% { opacity: 1; } 50% { opacity: .4; } }
  @keyframes fadein  { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
  .spin   { animation: spin .7s linear infinite; }
  .fadein { animation: fadein .3s ease both; }
  .nav-btn:hover { background: #f8fafc !important; color: #334155 !important; }
  .top-btn:hover { background: #f1f5f9 !important; border-color: #cbd5e1 !important; }
  .kpi-card:hover { border-color: var(--kc) !important; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,.07) !important; }
  .kpi-card:hover .kpi-val { color: var(--kc) !important; }
  .tool-card-light:hover { border-color: var(--tc) !important; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,.07) !important; }
  .biz-row-light:hover td { background: #f8fafc !important; }
`;
