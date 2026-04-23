'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Types ─────────────────────────────────────────────────────────────────────
interface Business {
  id: number;
  name?: string;
  business_name?: string;
  gmb_url?: string;
  city?: string;
  category?: string;
}

interface GMBPost {
  id: number;
  business_id: number;
  title?: string;
  description: string;
  post_type: string;
  cta_type?: string;
  cta_value?: string;
  media_url?: string;
  status: 'draft' | 'scheduled' | 'published' | 'failed' | 'pending';
  scheduled_date?: string;
  published_date?: string;
  profile_id?: string;
  error_log?: string;
  created_at: string;
  updated_at: string;
  ai_generated?: boolean;
  ai_topic?: string;
  content_angle?: string;
}

interface PostStats {
  total: number;
  published: number;
  scheduled: number;
  failed: number;
  draft: number;
  pending: number;
  ai_generated: number;
}

interface AutoPostPreview {
  post_id: number;
  business_id: number;
  topic: string;
  description: string;
  image_url: string;
  scheduled_at: string;
  content_angle: string;
  status: string;
}

type StatusFilter = 'all' | 'published' | 'scheduled' | 'failed' | 'draft' | 'pending';
type PostType = 'update' | 'offer' | 'event';
type FormMode = 'manual' | 'auto';

const CTA_OPTIONS = [
  { value: '', label: 'No CTA' },
  { value: 'call', label: '📞 Call Now' },
  { value: 'book', label: '📅 Book' },
  { value: 'learn_more', label: 'ℹ️ Learn More' },
  { value: 'order', label: '🛒 Order' },
  { value: 'shop', label: '🏪 Shop' },
  { value: 'sign_up', label: '✍️ Sign Up' },
  { value: 'get_offer', label: '🎁 Get Offer' },
];

const ANGLE_LABELS: Record<string, string> = {
  seasonal_offer: '🌿 Seasonal Offer',
  service_highlight: '⭐ Service Highlight',
  before_after: '🔄 Before & After',
  tips_faq: '💡 Tips & FAQ',
  client_result: '🏆 Client Result',
  why_choose_us: '🎯 Why Choose Us',
};

// ── Icons ─────────────────────────────────────────────────────────────────────
const Icon = ({ d, size = 16, color = 'currentColor' }: { d: string; size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

const IC = {
  back: 'M19 12H5M12 5l-7 7 7 7',
  refresh: 'M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15',
  plus: 'M12 5v14M5 12h14',
  calendar: 'M8 2v4M16 2v4M3 10h18M3 6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2H3z',
  image: 'M21 19V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2zM8.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM21 15l-5-5L5 21',
  post: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8',
  check: 'M20 6L9 17l-5-5',
  clock: 'M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 4v4l3 3',
  trash: 'M3 6h18M8 6V4h8v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6',
  zap: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z',
  alert: 'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01',
  search: 'M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0z',
  chevron: 'M6 9l6 6 6-6',
  trend: 'M22 7l-9.2 9.2-4.8-4.8L2 18',
  eye: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  x: 'M18 6 6 18M6 6l12 12',
  upload: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12',
  link: 'M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71',
  sparkles: 'M5 3v4M3 5h4M6.5 17.5l-2.5 2.5M17.5 6.5l2.5-2.5M19 3v4M17 5h4M6.5 6.5 4 4M17.5 17.5l2.5 2.5M12 2l1.5 4.5L18 8l-4.5 1.5L12 14l-1.5-4.5L6 8l4.5-1.5L12 2z',
  robot: 'M12 2a2 2 0 0 1 2 2v1h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2V4a2 2 0 0 1 2-2zM9 11a1 1 0 1 0 2 0 1 1 0 0 0-2 0zm4 0a1 1 0 1 0 2 0 1 1 0 0 0-2 0zM9 15h6',
  edit: 'M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z',
};

// ── CSS ───────────────────────────────────────────────────────────────────────
const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', -apple-system, sans-serif; }
  :root {
    --bg: #f8fafc;
    --surface: #ffffff;
    --border: #e2e8f0;
    --border2: #f1f5f9;
    --text1: #0f172a;
    --text2: #475569;
    --text3: #94a3b8;
    --accent: #6366f1;
    --accentL: #eef2ff;
    --green: #10b981;
    --amber: #f59e0b;
    --cyan: #06b6d4;
    --purple: #8b5cf6;
    --red: #ef4444;
    --orange: #f97316;
    --ai: #7c3aed;
    --aiL: #f5f3ff;
  }
  .sc-page { min-height:100vh; background:var(--bg); color:var(--text1); font-family:'Inter',-apple-system,sans-serif; }
  .sc-topbar { position:sticky; top:0; z-index:100; background:var(--surface); border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; padding:0 24px; height:58px; gap:12px; }
  .sc-topbar-left  { display:flex; align-items:center; gap:10px; min-width:0; }
  .sc-topbar-right { display:flex; align-items:center; gap:8px; }
  .sc-brand { display:flex; align-items:center; gap:8px; text-decoration:none; }
  .sc-brand-dot { width:28px; height:28px; border-radius:8px; background:linear-gradient(135deg,#6366f1,#8b5cf6); display:flex; align-items:center; justify-content:center; }
  .sc-brand-name { font-size:.88rem; font-weight:700; color:var(--text1); }
  .sc-divider { width:1px; height:20px; background:var(--border); }
  .sc-pg-label { font-size:.82rem; color:var(--text2); font-weight:500; }
  .sc-btn { display:inline-flex; align-items:center; gap:6px; padding:0 14px; height:34px; border-radius:8px; font-size:.79rem; font-weight:600; cursor:pointer; border:1.5px solid transparent; transition:all .14s; font-family:inherit; white-space:nowrap; text-decoration:none; }
  .sc-btn-ghost { background:transparent; border-color:var(--border); color:var(--text2); }
  .sc-btn-ghost:hover { background:var(--bg); color:var(--text1); }
  .sc-btn-primary { background:var(--accent); color:white; border-color:var(--accent); box-shadow:0 2px 8px rgba(99,102,241,.2); }
  .sc-btn-primary:hover { opacity:.9; }
  .sc-btn-sm { height:28px; padding:0 10px; font-size:.73rem; }
  .sc-btn-danger { background:#fef2f2; color:#be123c; border-color:#fecdd3; }
  .sc-btn-danger:hover { background:#fee2e2; }
  .sc-btn-success { background:#f0fdf4; color:#15803d; border-color:#bbf7d0; }
  .sc-btn-success:hover { background:#dcfce7; }
  .sc-btn-disabled { opacity:.5; cursor:not-allowed; pointer-events:none; }
  .sc-btn-ai { background:linear-gradient(135deg,#7c3aed,#6366f1); color:white; border:none; box-shadow:0 2px 12px rgba(124,58,237,.3); }
  .sc-btn-ai:hover { opacity:.9; box-shadow:0 4px 18px rgba(124,58,237,.4); transform:translateY(-1px); }
  .sc-main { max-width:1400px; margin:0 auto; padding:24px 24px 56px; }
  .sc-stats-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-bottom:24px; }
  .sc-stat-card { background:var(--surface); border:1.5px solid var(--border); border-radius:13px; padding:16px 18px; position:relative; overflow:hidden; transition:box-shadow .15s; cursor:default; }
  .sc-stat-card:hover { box-shadow:0 4px 16px rgba(0,0,0,.07); }
  .sc-stat-bar { position:absolute; top:0; left:0; right:0; height:3px; border-radius:13px 13px 0 0; }
  .sc-stat-icon { width:34px; height:34px; border-radius:9px; display:flex; align-items:center; justify-content:center; margin-bottom:12px; }
  .sc-stat-val { font-size:1.75rem; font-weight:800; color:var(--text1); letter-spacing:-1px; line-height:1; margin-bottom:4px; }
  .sc-stat-label { font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:var(--text3); }
  .sc-stat-sub { font-size:.67rem; color:var(--text3); margin-top:2px; }
  .sc-grid { display:grid; grid-template-columns:420px 1fr; gap:20px; align-items:start; }
  .sc-card { background:var(--surface); border:1.5px solid var(--border); border-radius:13px; overflow:hidden; }
  .sc-card-head { padding:16px 20px; border-bottom:1px solid var(--border2); display:flex; align-items:center; justify-content:space-between; }
  .sc-card-head-left { display:flex; align-items:center; gap:10px; }
  .sc-card-icon { width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center; }
  .sc-card-title { font-size:.88rem; font-weight:700; color:var(--text1); }
  .sc-card-sub { font-size:.72rem; color:var(--text3); margin-top:1px; }
  .sc-card-body { padding:20px; }

  /* ── Mode Switcher ── */
  .sc-mode-switch { display:flex; background:var(--bg); border:1.5px solid var(--border); border-radius:10px; padding:3px; gap:3px; margin-bottom:20px; }
  .sc-mode-btn { flex:1; display:flex; align-items:center; justify-content:center; gap:6px; padding:8px 12px; border-radius:8px; border:none; font-size:.78rem; font-weight:600; cursor:pointer; font-family:inherit; transition:all .18s; color:var(--text2); background:transparent; }
  .sc-mode-btn.active { background:var(--surface); color:var(--text1); box-shadow:0 1px 4px rgba(0,0,0,.08); }
  .sc-mode-btn.active.auto { color:var(--ai); background:var(--aiL); }
  .sc-mode-btn.active.manual { color:var(--accent); }

  /* ── Auto Post Panel ── */
  .sc-auto-panel { display:flex; flex-direction:column; gap:16px; }
  .sc-auto-hero { background:linear-gradient(135deg,#f5f3ff,#eef2ff); border:1.5px solid #ddd6fe; border-radius:12px; padding:18px; display:flex; gap:14px; align-items:flex-start; }
  .sc-auto-hero-icon { width:42px; height:42px; border-radius:11px; background:linear-gradient(135deg,#7c3aed,#6366f1); display:flex; align-items:center; justify-content:center; flex-shrink:0; box-shadow:0 4px 12px rgba(124,58,237,.3); }
  .sc-auto-hero-title { font-size:.9rem; font-weight:700; color:#3b0764; margin-bottom:4px; }
  .sc-auto-hero-sub { font-size:.75rem; color:#6d28d9; line-height:1.5; }
  .sc-auto-steps { display:flex; flex-direction:column; gap:8px; padding:4px 0; }
  .sc-auto-step { display:flex; align-items:center; gap:10px; font-size:.76rem; color:var(--text2); }
  .sc-auto-step-num { width:20px; height:20px; border-radius:50%; background:linear-gradient(135deg,#7c3aed,#6366f1); color:white; font-size:.65rem; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
  .sc-auto-field { margin-bottom:14px; }
  .sc-auto-submit { width:100%; height:46px; border-radius:11px; background:linear-gradient(135deg,#7c3aed,#6366f1); color:white; border:none; font-size:.88rem; font-weight:700; font-family:inherit; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px; transition:all .15s; box-shadow:0 3px 12px rgba(124,58,237,.3); }
  .sc-auto-submit:hover { opacity:.92; box-shadow:0 6px 20px rgba(124,58,237,.4); transform:translateY(-1px); }
  .sc-auto-submit:disabled { background:#cbd5e1; box-shadow:none; cursor:not-allowed; transform:none; }
  .sc-auto-progress { display:flex; flex-direction:column; gap:12px; padding:18px; background:linear-gradient(135deg,#f5f3ff,#eef2ff); border:1.5px solid #ddd6fe; border-radius:12px; }
  .sc-auto-progress-title { font-size:.82rem; font-weight:700; color:#3b0764; display:flex; align-items:center; gap:8px; }
  .sc-auto-progress-steps { display:flex; flex-direction:column; gap:8px; }
  .sc-auto-progress-step { display:flex; align-items:center; gap:10px; font-size:.76rem; }
  .sc-auto-progress-step.done { color:#15803d; }
  .sc-auto-progress-step.active { color:#3b0764; font-weight:600; }
  .sc-auto-progress-step.pending { color:var(--text3); }
  .sc-step-icon { width:18px; height:18px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex-shrink:0; font-size:.6rem; font-weight:700; }
  .sc-step-icon.done { background:#dcfce7; color:#15803d; }
  .sc-step-icon.active { background:linear-gradient(135deg,#7c3aed,#6366f1); color:white; animation:sc-pulse 1.5s ease-in-out infinite; }
  .sc-step-icon.pending { background:var(--border2); color:var(--text3); }

  /* ── AI Preview Card ── */
  .sc-preview-card { border:1.5px solid #ddd6fe; border-radius:12px; overflow:hidden; background:var(--surface); }
  .sc-preview-head { padding:12px 16px; background:linear-gradient(135deg,#f5f3ff,#eef2ff); border-bottom:1px solid #ddd6fe; display:flex; align-items:center; justify-content:space-between; }
  .sc-preview-head-title { font-size:.8rem; font-weight:700; color:#3b0764; display:flex; align-items:center; gap:6px; }
  .sc-preview-img { width:100%; height:170px; object-fit:cover; display:block; background:var(--bg); }
  .sc-preview-img-fallback { width:100%; height:170px; background:linear-gradient(135deg,#f5f3ff,#eef2ff); display:flex; align-items:center; justify-content:center; color:#a78bfa; font-size:.8rem; }
  .sc-preview-body { padding:14px 16px; display:flex; flex-direction:column; gap:10px; }
  .sc-preview-topic { font-size:.88rem; font-weight:700; color:var(--text1); line-height:1.3; }
  .sc-preview-desc { font-size:.76rem; color:var(--text2); line-height:1.6; display:-webkit-box; -webkit-line-clamp:4; -webkit-box-orient:vertical; overflow:hidden; }
  .sc-preview-meta { display:flex; flex-wrap:wrap; gap:6px; }
  .sc-preview-chip { display:inline-flex; align-items:center; gap:4px; padding:2px 8px; border-radius:20px; font-size:.65rem; font-weight:600; background:var(--aiL); color:var(--ai); border:1px solid #ddd6fe; }
  .sc-preview-actions { display:flex; gap:8px; padding:12px 16px; border-top:1px solid var(--border2); background:var(--bg); }
  .sc-preview-confirm { flex:1; height:36px; border-radius:8px; background:linear-gradient(135deg,#10b981,#059669); color:white; border:none; font-size:.78rem; font-weight:700; font-family:inherit; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:6px; transition:all .14s; }
  .sc-preview-confirm:hover { opacity:.9; }
  .sc-preview-discard { height:36px; padding:0 14px; border-radius:8px; background:transparent; color:var(--text2); border:1.5px solid var(--border); font-size:.78rem; font-weight:600; font-family:inherit; cursor:pointer; transition:all .14s; }
  .sc-preview-discard:hover { background:#fef2f2; color:var(--red); border-color:#fecdd3; }
  .sc-preview-edit-btn { height:36px; padding:0 14px; border-radius:8px; background:var(--accentL); color:var(--accent); border:1.5px solid #c7d2fe; font-size:.78rem; font-weight:600; font-family:inherit; cursor:pointer; transition:all .14s; display:flex; align-items:center; gap:5px; }
  .sc-preview-edit-btn:hover { background:#e0e7ff; }

  .sc-field { margin-bottom:16px; }
  .sc-label { display:flex; align-items:center; justify-content:space-between; font-size:.7rem; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:var(--text3); margin-bottom:6px; }
  .sc-label-note { font-size:.67rem; font-weight:400; text-transform:none; color:var(--text3); letter-spacing:0; }
  .sc-input { width:100%; height:38px; padding:0 12px; background:var(--bg); border:1.5px solid var(--border); border-radius:9px; font-size:.82rem; color:var(--text1); outline:none; font-family:inherit; transition:border-color .14s,box-shadow .14s; }
  .sc-input:focus { border-color:var(--accent); box-shadow:0 0 0 3px rgba(99,102,241,.1); background:var(--surface); }
  .sc-input::placeholder { color:var(--text3); }
  .sc-textarea { width:100%; padding:10px 12px; background:var(--bg); border:1.5px solid var(--border); border-radius:9px; font-size:.82rem; color:var(--text1); outline:none; font-family:inherit; resize:vertical; line-height:1.6; transition:border-color .14s,box-shadow .14s; }
  .sc-textarea:focus { border-color:var(--accent); box-shadow:0 0 0 3px rgba(99,102,241,.1); background:var(--surface); }
  .sc-textarea::placeholder { color:var(--text3); }
  .sc-select { width:100%; height:38px; padding:0 12px; background:var(--bg); border:1.5px solid var(--border); border-radius:9px; font-size:.82rem; color:var(--text1); outline:none; font-family:inherit; cursor:pointer; transition:border-color .14s; appearance:none; background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E"); background-repeat:no-repeat; background-position:right 10px center; padding-right:32px; }
  .sc-select:focus { border-color:var(--accent); box-shadow:0 0 0 3px rgba(99,102,241,.1); background-color:var(--surface); }
  .sc-input-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  .sc-char-row { display:flex; align-items:center; justify-content:space-between; margin-top:5px; }
  .sc-char-count { font-size:.67rem; color:var(--text3); font-variant-numeric:tabular-nums; }
  .sc-char-count.warn { color:#f59e0b; }
  .sc-char-count.over { color:#ef4444; }
  .sc-char-bar-wrap { flex:1; height:2px; background:var(--border2); border-radius:99px; margin:0 10px; overflow:hidden; }
  .sc-char-bar { height:100%; border-radius:99px; background:var(--accent); transition:width .3s,background .3s; }
  .sc-char-bar.warn { background:#f59e0b; }
  .sc-char-bar.over { background:#ef4444; }
  .sc-type-pills { display:flex; gap:8px; }
  .sc-type-pill { flex:1; display:flex; align-items:center; justify-content:center; gap:5px; padding:8px 4px; border-radius:9px; border:1.5px solid var(--border); background:var(--bg); color:var(--text2); font-size:.75rem; font-weight:600; cursor:pointer; transition:all .14s; font-family:inherit; }
  .sc-type-pill:hover { border-color:var(--accent); color:var(--accent); }
  .sc-type-pill.active { background:var(--accentL); border-color:var(--accent); color:var(--accent); }
  .sc-toggle-row { display:flex; align-items:center; justify-content:space-between; padding:12px 14px; background:var(--bg); border:1.5px solid var(--border); border-radius:10px; margin-bottom:12px; }
  .sc-toggle-info { display:flex; flex-direction:column; gap:2px; }
  .sc-toggle-title { font-size:.82rem; font-weight:600; color:var(--text1); }
  .sc-toggle-sub { font-size:.71rem; color:var(--text3); }
  .sc-toggle-btn { position:relative; width:40px; height:22px; border-radius:99px; border:none; cursor:pointer; transition:background .2s; flex-shrink:0; }
  .sc-toggle-btn.on { background:var(--accent); }
  .sc-toggle-btn.off { background:var(--border); }
  .sc-toggle-thumb { position:absolute; top:3px; left:3px; width:16px; height:16px; border-radius:50%; background:white; box-shadow:0 1px 3px rgba(0,0,0,.2); transition:transform .2s cubic-bezier(.34,1.56,.64,1); }
  .sc-toggle-btn.on .sc-toggle-thumb { transform:translateX(18px); }
  .sc-schedule-panel { background:#fffbeb; border:1.5px solid #fde68a; border-radius:10px; padding:14px; margin-bottom:12px; }
  .sc-schedule-panel-title { font-size:.75rem; font-weight:700; color:#92400e; margin-bottom:10px; display:flex; align-items:center; gap:6px; }
  .sc-img-tabs { display:flex; gap:6px; margin-bottom:8px; }
  .sc-img-tab { display:flex; align-items:center; gap:5px; padding:5px 12px; border-radius:8px; font-size:.73rem; font-weight:600; cursor:pointer; border:1.5px solid var(--border); background:var(--bg); color:var(--text2); font-family:inherit; transition:all .14s; }
  .sc-img-tab:hover { border-color:var(--accent); color:var(--accent); }
  .sc-img-tab.active { background:var(--accentL); border-color:var(--accent); color:var(--accent); }
  .sc-dropzone { width:100%; padding:20px 16px; background:var(--bg); border:2px dashed var(--border); border-radius:10px; cursor:pointer; font-family:inherit; transition:all .2s; display:flex; flex-direction:column; align-items:center; gap:6px; }
  .sc-dropzone:hover, .sc-dropzone.drag { border-color:var(--accent); background:var(--accentL); }
  .sc-dropzone-icon { width:38px; height:38px; border-radius:10px; background:white; border:1.5px solid var(--border); display:flex; align-items:center; justify-content:center; box-shadow:0 1px 4px rgba(0,0,0,.06); }
  .sc-dropzone-title { font-size:.82rem; font-weight:600; color:var(--text1); }
  .sc-dropzone-sub { font-size:.7rem; color:var(--text3); text-align:center; }
  .sc-dropzone-btn { margin-top:4px; display:inline-flex; align-items:center; gap:5px; padding:5px 14px; border-radius:8px; background:var(--accent); color:white; font-size:.75rem; font-weight:700; border:none; font-family:inherit; cursor:pointer; transition:opacity .14s; }
  .sc-dropzone-btn:hover { opacity:.88; }
  .sc-uploading-box { padding:16px; border:1.5px solid #c7d2fe; background:#eef2ff; border-radius:10px; display:flex; align-items:center; gap:10px; }
  .sc-uploading-text { font-size:.78rem; color:var(--accent); font-weight:700; }
  .sc-uploading-sub { font-size:.68rem; color:#6366f1; margin-top:2px; }
  .sc-inline-error { margin-top:8px; padding:9px 10px; border-radius:8px; background:#fef2f2; border:1px solid #fecaca; color:#b91c1c; font-size:.72rem; line-height:1.45; }
  .sc-img-preview-wrap { position:relative; border-radius:10px; overflow:hidden; border:1.5px solid var(--border); background:var(--bg); }
  .sc-img-preview-wrap img { width:100%; height:150px; object-fit:cover; display:block; }
  .sc-img-overlay { position:absolute; inset:0; background:rgba(15,23,42,.0); transition:background .2s; display:flex; align-items:center; justify-content:center; gap:8px; opacity:0; }
  .sc-img-preview-wrap:hover .sc-img-overlay { background:rgba(15,23,42,.45); opacity:1; }
  .sc-img-overlay-btn { display:flex; align-items:center; gap:5px; padding:6px 14px; border-radius:8px; font-size:.75rem; font-weight:700; border:none; font-family:inherit; cursor:pointer; transition:all .14s; }
  .sc-img-overlay-change { background:white; color:var(--text1); }
  .sc-img-overlay-change:hover { background:var(--accentL); color:var(--accent); }
  .sc-img-overlay-remove { background:rgba(239,68,68,.9); color:white; }
  .sc-img-overlay-remove:hover { background:#dc2626; }
  .sc-img-info { display:flex; align-items:center; justify-content:space-between; padding:6px 10px; background:var(--bg); border-top:1px solid var(--border2); gap:10px; }
  .sc-img-name { font-size:.72rem; color:var(--text2); font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:200px; }
  .sc-img-size { font-size:.67rem; color:var(--text3); white-space:nowrap; }
  .sc-img-source-badge { display:inline-flex; align-items:center; gap:3px; padding:2px 7px; border-radius:20px; font-size:.63rem; font-weight:700; }
  .sc-img-source-file { background:#f0fdf4; color:#15803d; border:1px solid #bbf7d0; }
  .sc-img-source-url { background:var(--accentL); color:var(--accent); border:1px solid #c7d2fe; }
  .sc-url-input-wrap { display:flex; flex-direction:column; gap:8px; }
  .sc-url-preview { border-radius:10px; overflow:hidden; border:1.5px solid var(--border); margin-top:4px; }
  .sc-url-preview img { width:100%; height:130px; object-fit:cover; display:block; }
  .sc-url-clear { width:100%; display:flex; align-items:center; justify-content:center; gap:5px; padding:6px; background:var(--bg); border:none; border-top:1px solid var(--border2); font-size:.72rem; color:var(--text3); font-family:inherit; cursor:pointer; transition:all .14s; }
  .sc-url-clear:hover { color:var(--red); background:#fef2f2; }
  .sc-submit { width:100%; height:42px; border-radius:10px; background:var(--accent); color:white; border:none; font-size:.84rem; font-weight:700; font-family:inherit; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px; transition:all .15s; box-shadow:0 2px 8px rgba(99,102,241,.25); }
  .sc-submit:hover { opacity:.9; box-shadow:0 4px 16px rgba(99,102,241,.3); }
  .sc-submit:disabled { background:#cbd5e1; box-shadow:none; cursor:not-allowed; }
  .sc-submit-schedule { background:linear-gradient(135deg,#f59e0b,#f97316); box-shadow:0 2px 8px rgba(245,158,11,.25); }
  .sc-submit-schedule:hover { opacity:.9; box-shadow:0 4px 16px rgba(245,158,11,.3); }
  .sc-spinner { width:14px; height:14px; border:2px solid rgba(255,255,255,.4); border-top-color:white; border-radius:50%; animation:sc-spin .7s linear infinite; }
  @keyframes sc-spin { to { transform:rotate(360deg); } }
  .sc-toast { position:fixed; bottom:24px; right:24px; z-index:9999; display:flex; align-items:center; gap:10px; padding:12px 18px; border-radius:12px; font-size:.82rem; font-weight:600; color:white; box-shadow:0 8px 32px rgba(0,0,0,.18); animation:sc-toast-in .3s cubic-bezier(.16,1,.3,1); max-width:360px; }
  .sc-toast-success { background:linear-gradient(135deg,#10b981,#059669); }
  .sc-toast-error { background:linear-gradient(135deg,#ef4444,#dc2626); }
  .sc-toast-info { background:linear-gradient(135deg,#6366f1,#4f46e5); }
  .sc-toast-close { background:none; border:none; color:rgba(255,255,255,.7); cursor:pointer; padding:0; display:flex; line-height:1; font-size:16px; margin-left:4px; }
  .sc-toast-close:hover { color:white; }
  @keyframes sc-toast-in { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
  .sc-status-tabs { display:flex; background:var(--bg); border-bottom:1px solid var(--border2); overflow-x:auto; }
  .sc-status-tab { display:flex; align-items:center; gap:5px; padding:10px 16px; font-size:.78rem; font-weight:500; color:var(--text2); cursor:pointer; border:none; background:transparent; border-bottom:2px solid transparent; white-space:nowrap; transition:all .14s; font-family:inherit; }
  .sc-status-tab:hover { color:var(--text1); background:var(--surface); }
  .sc-status-tab.active { color:var(--accent); border-bottom-color:var(--accent); background:var(--surface); font-weight:700; }
  .sc-tab-badge { display:inline-flex; align-items:center; justify-content:center; min-width:18px; height:18px; padding:0 5px; border-radius:99px; font-size:.63rem; font-weight:700; }
  .sc-tab-badge-default { background:var(--border2); color:var(--text3); }
  .sc-tab-badge-active { background:var(--accentL); color:var(--accent); }
  .sc-toolbar { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:12px 16px; border-bottom:1px solid var(--border2); flex-wrap:wrap; }
  .sc-toolbar-left { display:flex; align-items:center; gap:8px; }
  .sc-toolbar-right { display:flex; align-items:center; gap:8px; }
  .sc-count-badge { font-size:.79rem; font-weight:700; background:var(--accentL); color:var(--accent); padding:2px 9px; border-radius:99px; }
  .sc-search-wrap { position:relative; }
  .sc-search-ico { position:absolute; left:10px; top:50%; transform:translateY(-50%); pointer-events:none; }
  .sc-search-input { height:32px; padding:0 12px 0 32px; background:var(--bg); border:1.5px solid var(--border); border-radius:8px; font-size:.78rem; color:var(--text1); outline:none; font-family:inherit; width:180px; transition:border-color .14s,width .2s; }
  .sc-search-input:focus { border-color:var(--accent); width:220px; }
  .sc-search-input::placeholder { color:var(--text3); }
  .sc-filter-select { height:32px; padding:0 10px; background:var(--bg); border:1.5px solid var(--border); border-radius:8px; font-size:.78rem; color:var(--text1); outline:none; font-family:inherit; cursor:pointer; }
  .sc-filter-select:focus { border-color:var(--accent); }
  .sc-table-wrap { overflow-x:auto; }
  .sc-table { width:100%; border-collapse:collapse; }
  .sc-table th { padding:10px 14px; text-align:left; font-size:.65rem; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:var(--text3); background:var(--bg); border-bottom:1px solid var(--border2); white-space:nowrap; }
  .sc-table td { padding:12px 14px; border-bottom:1px solid var(--border2); vertical-align:middle; }
  .sc-table tr:last-child td { border-bottom:none; }
  .sc-table tr:hover td { background:#fafbff; }
  .sc-table tr { transition:background .1s; cursor:pointer; }
  .sc-biz-cell { display:flex; align-items:center; gap:10px; }
  .sc-biz-avatar { width:30px; height:30px; border-radius:8px; background:linear-gradient(135deg,#6366f1,#8b5cf6); display:flex; align-items:center; justify-content:center; color:white; font-size:.78rem; font-weight:700; flex-shrink:0; }
  .sc-biz-avatar-ai { background:linear-gradient(135deg,#7c3aed,#6366f1); }
  .sc-biz-name { font-size:.8rem; font-weight:600; color:var(--text1); max-width:130px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .sc-biz-id { font-size:.67rem; color:var(--text3); }
  .sc-content-title { font-size:.79rem; font-weight:600; color:var(--text1); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:180px; }
  .sc-content-body { font-size:.73rem; color:var(--text2); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:180px; margin-top:1px; }
  .sc-has-image { font-size:.63rem; color:var(--purple); margin-top:2px; font-weight:500; }
  .sc-ai-badge { display:inline-flex; align-items:center; gap:3px; padding:1px 6px; border-radius:20px; font-size:.6rem; font-weight:700; background:var(--aiL); color:var(--ai); border:1px solid #ddd6fe; margin-top:2px; }
  .sc-badge { display:inline-flex; align-items:center; gap:4px; padding:2px 9px; border-radius:20px; font-size:.7rem; font-weight:700; border:1.5px solid transparent; white-space:nowrap; }
  .sc-badge-published { background:#f0fdf4; color:#15803d; border-color:#bbf7d0; }
  .sc-badge-scheduled { background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe; }
  .sc-badge-failed { background:#fef2f2; color:#be123c; border-color:#fecdd3; }
  .sc-badge-draft { background:var(--bg); color:var(--text2); border-color:var(--border); }
  .sc-badge-pending { background:#fdf4ff; color:#86198f; border-color:#f0abfc; }
  .sc-badge-update { background:var(--accentL); color:var(--accent); border-color:#c7d2fe; }
  .sc-badge-offer { background:#fff7ed; color:#c2410c; border-color:#fed7aa; }
  .sc-badge-event { background:#f0fdfa; color:#0f766e; border-color:#99f6e4; }
  .sc-status-dot { width:5px; height:5px; border-radius:50%; flex-shrink:0; }
  .sc-dot-published { background:#22c55e; }
  .sc-dot-scheduled { background:#3b82f6; animation:sc-pulse 2s ease-in-out infinite; }
  .sc-dot-failed { background:#ef4444; }
  .sc-dot-draft { background:#94a3b8; }
  .sc-dot-pending { background:#d946ef; animation:sc-pulse 2s ease-in-out infinite; }
  @keyframes sc-pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  .sc-date-val { font-size:.74rem; color:var(--text2); font-variant-numeric:tabular-nums; }
  .sc-date-ago { font-size:.66rem; color:var(--text3); margin-top:1px; }
  .sc-actions { display:flex; align-items:center; gap:5px; }
  .sc-icon-btn { width:28px; height:28px; display:flex; align-items:center; justify-content:center; border-radius:7px; border:1.5px solid var(--border); background:transparent; cursor:pointer; color:var(--text3); transition:all .12s; }
  .sc-icon-btn:hover { color:var(--red); border-color:#fecdd3; background:#fef2f2; }
  .sc-icon-btn-publish:hover { color:var(--accent); border-color:#c7d2fe; background:var(--accentL); }
  .sc-drawer { border-top:1.5px solid var(--border2); background:linear-gradient(135deg,#f8f9ff,#f0f4ff); padding:16px 20px; animation:sc-drawer-in .2s ease; }
  @keyframes sc-drawer-in { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
  .sc-drawer-head { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:10px; }
  .sc-drawer-title { font-size:.85rem; font-weight:700; color:var(--text1); }
  .sc-drawer-meta { font-size:.72rem; color:var(--text3); margin-top:2px; }
  .sc-drawer-content { font-size:.82rem; color:var(--text2); line-height:1.65; padding:10px 13px; background:white; border-radius:9px; border:1px solid var(--border2); margin-bottom:10px; }
  .sc-drawer-chips { display:flex; flex-wrap:wrap; gap:6px; }
  .sc-drawer-chip { display:inline-flex; align-items:center; gap:4px; padding:3px 10px; border-radius:20px; font-size:.7rem; font-weight:600; background:white; border:1.5px solid var(--border); color:var(--text2); }
  .sc-drawer-chip-err { background:#fef2f2; border-color:#fecdd3; color:#be123c; }
  .sc-drawer-chip-ai { background:var(--aiL); border-color:#ddd6fe; color:var(--ai); }
  .sc-drawer-close { width:22px; height:22px; display:flex; align-items:center; justify-content:center; border-radius:6px; border:1px solid var(--border); background:white; cursor:pointer; color:var(--text3); transition:all .12s; font-size:13px; }
  .sc-drawer-close:hover { color:var(--text1); }
  .sc-drawer-img { width:100%; max-height:120px; object-fit:cover; border-radius:8px; margin-bottom:10px; border:1px solid var(--border2); }
  .sc-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; padding:48px 24px; gap:10px; }
  .sc-empty-icon { width:48px; height:48px; border-radius:14px; background:var(--bg); border:1.5px solid var(--border); display:flex; align-items:center; justify-content:center; margin-bottom:4px; }
  .sc-empty-title { font-size:.88rem; font-weight:700; color:var(--text2); }
  .sc-empty-sub { font-size:.76rem; color:var(--text3); text-align:center; max-width:220px; line-height:1.5; }
  .sc-table-footer { display:flex; align-items:center; justify-content:space-between; padding:10px 16px; border-top:1px solid var(--border2); background:var(--bg); }
  .sc-table-footer-txt { font-size:.72rem; color:var(--text3); }
  .sc-refresh-link { background:none; border:none; font-size:.72rem; color:var(--accent); cursor:pointer; font-family:inherit; font-weight:600; }
  .sc-refresh-link:hover { opacity:.7; }
  .sc-load-row { display:flex; align-items:center; justify-content:center; gap:10px; padding:40px; color:var(--text3); }
  .sc-load-spin { width:22px; height:22px; border:2.5px solid var(--border); border-top-color:var(--accent); border-radius:50%; animation:sc-spin .7s linear infinite; }
  @media (max-width:1100px) { .sc-grid { grid-template-columns:1fr; } }
  @media (max-width:900px) {
    .sc-main { padding:14px 14px 40px; }
    .sc-stats-row { grid-template-columns:repeat(2,1fr); }
  }
  /* ── Multi-Select ── */
  .ms-wrap { position:relative; width:100%; }
  .ms-trigger { width:100%; height:38px; padding:0 12px; background:var(--bg); border:1.5px solid var(--border); border-radius:9px; font-size:.82rem; color:var(--text2); outline:none; font-family:inherit; cursor:pointer; display:flex; align-items:center; justify-content:space-between; gap:8px; transition:border-color .14s,box-shadow .14s; text-align:left; }
  .ms-trigger:focus, .ms-trigger.open { border-color:var(--accent); box-shadow:0 0 0 3px rgba(99,102,241,.1); background:var(--surface); color:var(--text1); }
  .ms-trigger.disabled { opacity:.5; cursor:not-allowed; }
  .ms-trigger-label { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
  .ms-tags { display:flex; flex-wrap:wrap; gap:4px; margin-top:6px; }
  .ms-tag { display:inline-flex; align-items:center; gap:4px; padding:2px 6px 2px 8px; background:var(--accentL); border:1px solid #c7d2fe; border-radius:20px; font-size:.7rem; font-weight:600; color:var(--accent); max-width:160px; }
  .ms-tag-x { background:none; border:none; cursor:pointer; color:#a5b4fc; font-size:14px; line-height:1; padding:0; display:flex; align-items:center; transition:color .12s; }
  .ms-tag-x:hover { color:var(--red); }
  .ms-dropdown { position:absolute; top:calc(100% + 4px); left:0; right:0; background:var(--surface); border:1.5px solid var(--border); border-radius:11px; box-shadow:0 8px 30px rgba(0,0,0,.12); z-index:200; overflow:hidden; }
  .ms-search-wrap { display:flex; align-items:center; gap:8px; padding:10px 12px; border-bottom:1px solid var(--border2); }
  .ms-search { flex:1; border:none; outline:none; font-size:.8rem; color:var(--text1); font-family:inherit; background:transparent; }
  .ms-search::placeholder { color:var(--text3); }
  .ms-select-all { width:100%; text-align:left; padding:6px 14px; font-size:.72rem; font-weight:700; color:var(--accent); background:var(--accentL); border:none; border-bottom:1px solid var(--border2); cursor:pointer; font-family:inherit; transition:background .12s; }
  .ms-select-all:hover { background:#e0e7ff; }
  .ms-list { max-height:220px; overflow-y:auto; }
  .ms-item { display:flex; align-items:center; gap:10px; padding:8px 14px; cursor:pointer; transition:background .1s; }
  .ms-item:hover { background:var(--bg); }
  .ms-item.checked { background:var(--accentL); }
  .ms-checkbox { width:14px; height:14px; accent-color:var(--accent); flex-shrink:0; cursor:pointer; }
  .ms-item-name { font-size:.8rem; color:var(--text1); flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .ms-item-city { font-size:.7rem; color:var(--text3); white-space:nowrap; }
  .ms-empty-msg { padding:16px; font-size:.78rem; color:var(--text3); text-align:center; }
  .ms-footer { display:flex; align-items:center; justify-content:space-between; padding:8px 14px; border-top:1px solid var(--border2); background:var(--bg); font-size:.72rem; color:var(--text3); font-weight:600; }
  .ms-clear { background:none; border:none; cursor:pointer; font-size:.72rem; color:var(--red); font-family:inherit; font-weight:600; padding:0; }
  .ms-clear:hover { opacity:.7; }
`;

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmt(d?: string) {
  if (!d) return '—';
  return new Date(d).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function timeAgo(d: string) {
  const diff = Date.now() - new Date(d).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function fmtBytes(b: number) {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
}

function extractErrorMsg(err: any): string {
  const detail = err?.response?.data?.detail;
  if (!detail) return err?.message || 'Failed';
  if (Array.isArray(detail)) return detail.map((e: any) => { const f = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : 'field'; return `${f}: ${e.msg}`; }).join(' | ');
  if (typeof detail === 'string') return detail;
  return JSON.stringify(detail);
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function Toast({ msg, type, onClose }: { msg: string; type: 'success' | 'error' | 'info'; onClose: () => void }) {
  useEffect(() => { const t = setTimeout(onClose, 3800); return () => clearTimeout(t); }, [onClose]);
  return (
    <div className={`sc-toast sc-toast-${type}`}>
      <span>{ type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ' }</span>
      <span style={{ flex: 1 }}>{msg}</span>
      <button className="sc-toast-close" onClick={onClose}>×</button>
    </div>
  );
}

// ── StatCard ──────────────────────────────────────────────────────────────────
function StatCard({ label, value, color, iconPath, sub }: { label: string; value: number; color: string; iconPath: string; sub?: string }) {
  return (
    <div className="sc-stat-card">
      <div className="sc-stat-bar" style={{ background: color }} />
      <div className="sc-stat-icon" style={{ background: `${color}18` }}>
        <Icon d={iconPath} size={16} color={color} />
      </div>
      <div className="sc-stat-val">{value.toLocaleString()}</div>
      <div className="sc-stat-label">{label}</div>
      {sub && <div className="sc-stat-sub">{sub}</div>}
    </div>
  );
}

// ── ImageUploader ─────────────────────────────────────────────────────────────
function ImageUploader({ mediaUrl, onMediaUrlChange, onError }: { mediaUrl: string; onMediaUrlChange: (url: string) => void; onError?: (msg: string) => void }) {
  const [tab, setTab] = useState<'upload' | 'url'>('upload');
  const [preview, setPreview] = useState('');
  const [fileInfo, setFileInfo] = useState<{ name: string; size: number } | null>(null);
  const [dragging, setDragging] = useState(false);
  const [urlInput, setUrlInput] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!mediaUrl) { setPreview(''); setFileInfo(null); setUrlInput(''); setUploadError(''); return; }
    setPreview(mediaUrl);
    if (mediaUrl.startsWith('http')) setUrlInput(mediaUrl);
  }, [mediaUrl]);

  const uploadFile = async (file: File) => {
    if (!file.type.startsWith('image/')) { const msg = 'Please select a valid image file.'; setUploadError(msg); onError?.(msg); return; }
    if (file.size > 10 * 1024 * 1024) { const msg = 'Image must be 10 MB or smaller.'; setUploadError(msg); onError?.(msg); return; }
    setUploading(true); setUploadError(''); setFileInfo({ name: file.name, size: file.size });
    try {
      const fd = new FormData(); fd.append('file', file);
      const res = await axios.post(`${API_BASE}/api/media/upload`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      const uploadedUrl = res.data?.url || res.data?.media_url || res.data?.mediaUrl || res.data?.file_url || res.data?.data?.url;
      if (!uploadedUrl || typeof uploadedUrl !== 'string') throw new Error('Upload succeeded but no file URL was returned.');
      setPreview(uploadedUrl); onMediaUrlChange(uploadedUrl);
    } catch (err: any) {
      const msg = extractErrorMsg(err) || 'Image upload failed';
      setUploadError(msg); setPreview(''); onMediaUrlChange(''); onError?.(msg);
    } finally { setUploading(false); }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => { const f = e.target.files?.[0]; if (f) uploadFile(f); };
  const handleDrop = (e: React.DragEvent) => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files?.[0]; if (f) uploadFile(f); };
  const handleUrlApply = () => { const v = urlInput.trim(); if (!v) return; setUploadError(''); setFileInfo(null); setPreview(v); onMediaUrlChange(v); };
  const handleClear = () => { setPreview(''); setFileInfo(null); setUrlInput(''); setUploadError(''); onMediaUrlChange(''); if (fileRef.current) fileRef.current.value = ''; };

  return (
    <div>
      <div className="sc-img-tabs">
        {(['upload', 'url'] as const).map((t) => (
          <button key={t} type="button" className={`sc-img-tab${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
            <Icon d={t === 'upload' ? IC.upload : IC.link} size={12} />
            {t === 'upload' ? 'Browse / Upload' : 'Paste URL'}
          </button>
        ))}
      </div>
      <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleFileChange} />
      {tab === 'upload' && (
        <>
          {uploading ? (
            <div className="sc-uploading-box">
              <div className="sc-load-spin" style={{ width: 18, height: 18 }} />
              <div><div className="sc-uploading-text">Uploading image…</div><div className="sc-uploading-sub">Sending file to media storage</div></div>
            </div>
          ) : !preview ? (
            <div className={`sc-dropzone${dragging ? ' drag' : ''}`} onClick={() => fileRef.current?.click()} onDragOver={(e) => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={handleDrop}>
              <div className="sc-dropzone-icon"><Icon d={IC.image} size={18} color="var(--accent)" /></div>
              <div className="sc-dropzone-title">{dragging ? 'Drop image here' : 'Drag & drop or click to browse'}</div>
              <div className="sc-dropzone-sub">JPG, PNG, WEBP, GIF — max 10 MB</div>
              <button type="button" className="sc-dropzone-btn" onClick={(e) => { e.stopPropagation(); fileRef.current?.click(); }}><Icon d={IC.upload} size={12} color="white" /> Choose File</button>
            </div>
          ) : (
            <div className="sc-img-preview-wrap">
              <img src={preview} alt="Preview" onError={() => { setPreview(''); setFileInfo(null); onMediaUrlChange(''); }} />
              <div className="sc-img-overlay">
                <button type="button" className="sc-img-overlay-btn sc-img-overlay-change" onClick={() => fileRef.current?.click()}><Icon d={IC.upload} size={12} /> Change</button>
                <button type="button" className="sc-img-overlay-btn sc-img-overlay-remove" onClick={handleClear}><Icon d={IC.x} size={12} /> Remove</button>
              </div>
              <div className="sc-img-info">
                <span className="sc-img-name">{fileInfo?.name ?? 'Uploaded image'}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  {fileInfo && <span className="sc-img-size">{fmtBytes(fileInfo.size)}</span>}
                  <span className="sc-img-source-badge sc-img-source-file">✓ uploaded</span>
                </div>
              </div>
            </div>
          )}
          {uploadError && <div className="sc-inline-error">{uploadError}</div>}
        </>
      )}
      {tab === 'url' && (
        <div className="sc-url-input-wrap">
          <div style={{ display: 'flex', gap: 6 }}>
            <input className="sc-input" type="url" value={urlInput} onChange={(e) => setUrlInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleUrlApply())} placeholder="https://cdn.example.com/photo.jpg" />
            <button type="button" onClick={handleUrlApply} style={{ flexShrink: 0, height: 38, padding: '0 14px', borderRadius: 9, background: 'var(--accent)', color: 'white', border: 'none', fontFamily: 'inherit', fontSize: '.78rem', fontWeight: 700, cursor: 'pointer' }}>Preview</button>
          </div>
          {preview && (
            <div className="sc-url-preview">
              <img src={preview} alt="URL Preview" onError={() => { setPreview(''); onMediaUrlChange(''); setUploadError('Could not load the image from that URL.'); }} />
              <div className="sc-img-info" style={{ borderTop: '1px solid var(--border2)' }}>
                <span className="sc-img-name" style={{ maxWidth: 220, fontSize: '.67rem', color: 'var(--text3)' }}>{urlInput.slice(0, 60)}{urlInput.length > 60 ? '…' : ''}</span>
                <span className="sc-img-source-badge sc-img-source-url">🔗 url</span>
              </div>
              <button type="button" className="sc-url-clear" onClick={handleClear}><Icon d={IC.x} size={11} /> Remove image</button>
            </div>
          )}
          {uploadError && <div className="sc-inline-error">{uploadError}</div>}
        </div>
      )}
    </div>
  );
}

// ── MultiBusinessSelect ───────────────────────────────────────────────────────
function MultiBusinessSelect({
  businesses, selectedIds, onChange, disabled, placeholder,
}: {
  businesses: Business[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const filtered = businesses.filter((b) => {
    if (!search) return true;
    const name = (b.business_name || b.name || '').toLowerCase();
    const city = (b.city || '').toLowerCase();
    return name.includes(search.toLowerCase()) || city.includes(search.toLowerCase());
  });

  const toggle = (id: number) =>
    onChange(selectedIds.includes(id) ? selectedIds.filter((x) => x !== id) : [...selectedIds, id]);

  const toggleAll = () =>
    onChange(selectedIds.length === businesses.length ? [] : businesses.map((b) => b.id));

  const triggerLabel =
    selectedIds.length === 0
      ? placeholder || 'Select businesses…'
      : selectedIds.length === 1
      ? (() => { const b = businesses.find((x) => x.id === selectedIds[0]); return b?.business_name || b?.name || `Business #${selectedIds[0]}`; })()
      : `${selectedIds.length} businesses selected`;

  return (
    <div className="ms-wrap" ref={ref}>
      <button
        type="button"
        className={`ms-trigger${open ? ' open' : ''}${disabled ? ' disabled' : ''}`}
        onClick={() => !disabled && setOpen((o) => !o)}
        disabled={disabled}
      >
        <span className="ms-trigger-label">{triggerLabel}</span>
        <Icon d={IC.chevron} size={12} />
      </button>

      {selectedIds.length > 0 && (
        <div className="ms-tags">
          {selectedIds.map((id) => {
            const biz = businesses.find((b) => b.id === id);
            return (
              <span key={id} className="ms-tag">
                {(biz?.business_name || biz?.name || `#${id}`).slice(0, 24)}
                <button type="button" className="ms-tag-x" onClick={() => toggle(id)} disabled={disabled}>×</button>
              </span>
            );
          })}
        </div>
      )}

      {open && (
        <div className="ms-dropdown">
          <div className="ms-search-wrap">
            <Icon d={IC.search} size={12} color="var(--text3)" />
            <input className="ms-search" type="text" placeholder="Search businesses…" value={search} onChange={(e) => setSearch(e.target.value)} autoFocus />
          </div>
          {businesses.length > 1 && (
            <button type="button" className="ms-select-all" onClick={toggleAll}>
              {selectedIds.length === businesses.length ? 'Deselect All' : `Select All (${businesses.length})`}
            </button>
          )}
          <div className="ms-list">
            {filtered.length === 0 ? (
              <div className="ms-empty-msg">No businesses match your search</div>
            ) : (
              filtered.map((b) => {
                const checked = selectedIds.includes(b.id);
                return (
                  <label key={b.id} className={`ms-item${checked ? ' checked' : ''}`}>
                    <input type="checkbox" checked={checked} onChange={() => toggle(b.id)} className="ms-checkbox" />
                    <span className="ms-item-name">{b.business_name || b.name}</span>
                    {b.city && <span className="ms-item-city">{b.city}</span>}
                  </label>
                );
              })
            )}
          </div>
          {selectedIds.length > 0 && (
            <div className="ms-footer">
              {selectedIds.length} selected
              <button type="button" className="ms-clear" onClick={() => onChange([])}>Clear all</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── AutoPostPanel ─────────────────────────────────────────────────────────────
function AutoPostPanel({ businesses, onSuccess, showToast }: { businesses: Business[]; onSuccess: () => void; showToast: (msg: string, type: 'success' | 'error' | 'info') => void }) {
  const [businessIds, setBusinessIds] = useState<number[]>([]);
  const [scheduledAt, setScheduledAt] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0); // 0=idle, 1=topic, 2=desc, 3=image, 4=done
  const [previews, setPreviews] = useState<AutoPostPreview[]>([]);

  const STEPS = ['Selecting topic & content angle…', 'Writing post description…', 'Generating AI image…', 'Saving to scheduler…'];

  const handleGenerate = async () => {
    if (businessIds.length === 0) { showToast('Please select at least one business', 'error'); return; }
    if (!scheduledAt) { showToast('Please pick a schedule date & time', 'error'); return; }

    setLoading(true);
    setPreviews([]);
    setStep(1);

    const stepTimer = (s: number, delay: number) => setTimeout(() => setStep(s), delay);
    stepTimer(2, 3000);
    stepTimer(3, 7000);

    try {
      const isoDate = new Date(scheduledAt).toISOString();
      const res = await axios.post(`${API_BASE}/api/gmb-posts/auto-generate`, {
        business_ids: businessIds,
        scheduled_at: isoDate,
      });
      setStep(4);
      const bulk = res.data;
      setPreviews(bulk.posts || []);
      const n = (bulk.posts || []).length;
      if (bulk.errors?.length) {
        showToast(`Generated ${n} post(s). ${bulk.errors.length} business(es) failed.`, 'info');
      } else {
        showToast(`${n} AI post(s) generated! Review below.`, 'info');
      }
    } catch (err: any) {
      showToast(extractErrorMsg(err), 'error');
      setStep(0);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAll = async () => {
    const postIds = previews.map((p) => p.post_id);
    try {
      await axios.post(`${API_BASE}/api/gmb-posts/bulk-confirm`, { post_ids: postIds });
      setPreviews([]);
      setStep(0);
      setBusinessIds([]);
      setScheduledAt('');
      onSuccess();
      showToast(`${postIds.length} post(s) scheduled successfully! ⚡`, 'success');
    } catch (err: any) {
      showToast(extractErrorMsg(err), 'error');
    }
  };

  const handleDiscardOne = async (postId: number) => {
    try { await axios.delete(`${API_BASE}/api/gmb-posts/${postId}`); } catch {}
    const remaining = previews.filter((p) => p.post_id !== postId);
    setPreviews(remaining);
    if (remaining.length === 0) setStep(0);
    showToast('Post discarded', 'info');
  };

  const handleDiscardAll = async () => {
    for (const p of previews) {
      try { await axios.delete(`${API_BASE}/api/gmb-posts/${p.post_id}`); } catch {}
    }
    setPreviews([]);
    setStep(0);
    showToast('All posts discarded', 'info');
  };

  const firstPreview = previews[0] ?? null;

  return (
    <div className="sc-auto-panel">
      {/* Hero Info */}
      <div className="sc-auto-hero">
        <div className="sc-auto-hero-icon">
          <Icon d={IC.sparkles} size={20} color="white" />
        </div>
        <div>
          <div className="sc-auto-hero-title">AI Auto-Post</div>
          <div className="sc-auto-hero-sub">Select one or more businesses + schedule time. AI writes a unique topic, description & image for each — zero input needed.</div>
        </div>
      </div>

      {/* How It Works */}
      <div style={{ padding: '2px 0 6px' }}>
        <div style={{ fontSize: '.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.6px', color: 'var(--text3)', marginBottom: 8 }}>How it works</div>
        <div className="sc-auto-steps">
          {['Picks best content angle per business (rotates 6 types)','Writes SEO-optimized post for each city & category','Generates professional AI image per post via FLUX.1','Saves all posts to scheduler — auto-publishes at set time'].map((s, i) => (
            <div key={i} className="sc-auto-step">
              <div className="sc-auto-step-num">{i + 1}</div>
              <span>{s}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Form */}
      <div className="sc-auto-field">
        <div className="sc-label">
          Businesses
          {businessIds.length > 0 && <span className="sc-label-note">{businessIds.length} selected</span>}
        </div>
        <MultiBusinessSelect
          businesses={businesses}
          selectedIds={businessIds}
          onChange={setBusinessIds}
          disabled={loading}
          placeholder="Select businesses…"
        />
      </div>

      <div className="sc-auto-field">
        <div className="sc-label">Schedule Date & Time</div>
        <input
          className="sc-input"
          type="datetime-local"
          value={scheduledAt}
          min={new Date(Date.now() + 60000).toISOString().slice(0, 16)}
          onChange={(e) => setScheduledAt(e.target.value)}
          disabled={loading}
          style={{ background: 'white' }}
        />
        {scheduledAt && (
          <div style={{ fontSize: '.7rem', color: '#6d28d9', marginTop: 5, fontWeight: 600 }}>
            Will publish {new Date(scheduledAt).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>

      {/* Progress Steps (during generation) */}
      {loading && step > 0 && (
        <div className="sc-auto-progress">
          <div className="sc-auto-progress-title">
            <div className="sc-spinner" style={{ borderColor: 'rgba(124,58,237,.3)', borderTopColor: '#7c3aed' }} />
            Generating {businessIds.length > 1 ? `${businessIds.length} posts` : 'your post'}…
          </div>
          <div className="sc-auto-progress-steps">
            {STEPS.map((s, i) => {
              const idx = i + 1;
              const state = idx < step ? 'done' : idx === step ? 'active' : 'pending';
              return (
                <div key={i} className={`sc-auto-progress-step ${state}`}>
                  <div className={`sc-step-icon ${state}`}>{state === 'done' ? '✓' : idx}</div>
                  {s}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Generate Button */}
      {previews.length === 0 && (
        <button className="sc-auto-submit" onClick={handleGenerate} disabled={loading}>
          {loading ? (
            <><div className="sc-spinner" /> Generating AI Post{businessIds.length > 1 ? 's' : ''}…</>
          ) : (
            <><Icon d={IC.sparkles} size={16} color="white" /> ⚡ Generate & Schedule{businessIds.length > 1 ? ` (${businessIds.length})` : ''}</>
          )}
        </button>
      )}

      {/* Preview — Single Business */}
      {previews.length === 1 && !loading && firstPreview && (
        <div className="sc-preview-card">
          <div className="sc-preview-head">
            <div className="sc-preview-head-title">
              <Icon d={IC.eye} size={13} color="#7c3aed" />
              AI Preview — Review before confirming
            </div>
          </div>
          {firstPreview.image_url ? (
            <img className="sc-preview-img" src={firstPreview.image_url} alt="AI Generated" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
          ) : (
            <div className="sc-preview-img-fallback"><Icon d={IC.image} size={28} color="#a78bfa" /></div>
          )}
          <div className="sc-preview-body">
            <div className="sc-preview-topic">{firstPreview.topic}</div>
            <div className="sc-preview-desc">{firstPreview.description}</div>
            <div className="sc-preview-meta">
              {firstPreview.content_angle && <span className="sc-preview-chip">✦ {ANGLE_LABELS[firstPreview.content_angle] || firstPreview.content_angle}</span>}
              <span className="sc-preview-chip">📅 {fmt(firstPreview.scheduled_at)}</span>
              <span className="sc-preview-chip">🤖 AI Generated</span>
            </div>
          </div>
          <div className="sc-preview-actions">
            <button className="sc-preview-confirm" onClick={handleConfirmAll}>
              <Icon d={IC.check} size={13} color="white" /> Confirm & Schedule
            </button>
            <button className="sc-preview-discard" onClick={() => handleDiscardOne(firstPreview.post_id)}>Discard</button>
          </div>
        </div>
      )}

      {/* Preview — Multiple Businesses */}
      {previews.length > 1 && !loading && (
        <div className="sc-preview-card">
          <div className="sc-preview-head">
            <div className="sc-preview-head-title">
              <Icon d={IC.eye} size={13} color="#7c3aed" />
              {previews.length} Posts Generated — Review & Confirm
            </div>
          </div>
          <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {previews.map((p) => {
              const biz = businesses.find((b) => b.id === p.business_id);
              return (
                <div key={p.post_id} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '10px 12px', background: 'var(--bg)', borderRadius: 9, border: '1px solid var(--border2)' }}>
                  <div style={{ width: 34, height: 34, borderRadius: 9, background: 'linear-gradient(135deg,#7c3aed,#6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '.8rem', fontWeight: 700, flexShrink: 0 }}>
                    {(biz?.business_name || biz?.name || '?').charAt(0).toUpperCase()}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '.78rem', fontWeight: 700, color: 'var(--text1)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {biz?.business_name || biz?.name || `Business #${p.business_id}`}
                    </div>
                    <div style={{ fontSize: '.72rem', color: 'var(--text2)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.topic}</div>
                    {p.content_angle && (
                      <span className="sc-preview-chip" style={{ marginTop: 4, display: 'inline-flex' }}>✦ {ANGLE_LABELS[p.content_angle] || p.content_angle}</span>
                    )}
                  </div>
                  <button type="button" className="sc-icon-btn" title="Discard this post" onClick={() => handleDiscardOne(p.post_id)} style={{ marginTop: 2 }}>
                    <Icon d={IC.trash} size={12} />
                  </button>
                </div>
              );
            })}
          </div>
          <div className="sc-preview-actions">
            <button className="sc-preview-confirm" onClick={handleConfirmAll}>
              <Icon d={IC.check} size={13} color="white" /> Confirm All {previews.length} Posts
            </button>
            <button className="sc-preview-discard" onClick={handleDiscardAll}>Discard All</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── PostRow ───────────────────────────────────────────────────────────────────
function PostRow({ post, isSelected, bizName, onSelect, onPublish, onDelete }: { post: GMBPost; isSelected: boolean; bizName: (id: number) => string; onSelect: () => void; onPublish: (id: number) => void; onDelete: (id: number) => void }) {
  return (
    <>
      <tr onClick={onSelect} style={{ background: isSelected ? '#f5f6ff' : undefined }}>
        <td>
          <div className="sc-biz-cell">
            <div className={`sc-biz-avatar${post.ai_generated ? ' sc-biz-avatar-ai' : ''}`}>{bizName(post.business_id).charAt(0).toUpperCase()}</div>
            <div>
              <div className="sc-biz-name">{bizName(post.business_id)}</div>
              <div className="sc-biz-id">#{post.id}{post.ai_generated && ' · 🤖'}</div>
            </div>
          </div>
        </td>
        <td>
          {post.title && <div className="sc-content-title">{post.title}</div>}
          <div className="sc-content-body">{post.description}</div>
          {post.media_url && <div className="sc-has-image">📷 Has image</div>}
          {post.ai_generated && <div className="sc-ai-badge">✦ AI Generated</div>}
        </td>
        <td>
          <span className={`sc-badge sc-badge-${post.post_type?.toLowerCase()}`} style={{ textTransform: 'capitalize' }}>{post.post_type?.toLowerCase()}</span>
        </td>
        <td>
          <span className={`sc-badge sc-badge-${post.status}`}>
            <span className={`sc-status-dot sc-dot-${post.status}`} />
            {post.status}
          </span>
        </td>
        <td>
          <div className="sc-date-val">{post.status === 'scheduled' || post.status === 'pending' ? fmt(post.scheduled_date) : post.status === 'published' ? fmt(post.published_date) : '—'}</div>
          <div className="sc-date-ago">{timeAgo(post.created_at)}</div>
        </td>
        <td onClick={(e) => e.stopPropagation()}>
          <div className="sc-actions">
            {['draft', 'failed', 'scheduled', 'pending'].includes(post.status) && (
              <button className="sc-btn sc-btn-ghost sc-btn-sm sc-icon-btn-publish" onClick={() => onPublish(post.id)} title="Publish now" style={{ width: 'auto', paddingInline: 10, gap: 4, color: 'var(--accent)', borderColor: '#c7d2fe', background: 'var(--accentL)' }}>
                <Icon d={IC.zap} size={11} color="var(--accent)" />
                <span style={{ fontSize: '.72rem', fontWeight: 700 }}>Publish</span>
              </button>
            )}
            <button className="sc-icon-btn" onClick={() => onDelete(post.id)} title="Delete"><Icon d={IC.trash} size={13} /></button>
          </div>
        </td>
      </tr>
      {isSelected && (
        <tr>
          <td colSpan={6} style={{ padding: 0 }}>
            <div className="sc-drawer">
              <div className="sc-drawer-head">
                <div>
                  <div className="sc-drawer-title">{post.title || `Post #${post.id}`}</div>
                  <div className="sc-drawer-meta">{bizName(post.business_id)} · Created {timeAgo(post.created_at)}{post.status === 'scheduled' && post.scheduled_date && ` · Scheduled for ${fmt(post.scheduled_date)}`}</div>
                </div>
                <button className="sc-drawer-close" onClick={(e) => { e.stopPropagation(); onSelect(); }}>×</button>
              </div>
              {post.media_url && <img className="sc-drawer-img" src={post.media_url} alt="Post image" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />}
              <div className="sc-drawer-content">{post.description}</div>
              <div className="sc-drawer-chips">
                {post.ai_generated && <span className="sc-drawer-chip sc-drawer-chip-ai"><Icon d={IC.sparkles} size={11} color="var(--ai)" /> AI Generated{post.content_angle ? ` · ${ANGLE_LABELS[post.content_angle] || post.content_angle}` : ''}</span>}
                {post.cta_type && <span className="sc-drawer-chip"><Icon d={IC.zap} size={11} color="var(--accent)" /> CTA: {post.cta_type}{post.cta_value ? ` → ${post.cta_value}` : ''}</span>}
                {post.media_url && <span className="sc-drawer-chip">📷 Has image</span>}
                {post.profile_id && <span className="sc-drawer-chip" style={{ fontFamily: 'monospace', fontSize: '.67rem', maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{post.profile_id}</span>}
                {post.error_log && <span className="sc-drawer-chip sc-drawer-chip-err"><Icon d={IC.alert} size={11} color="#be123c" />{post.error_log.slice(0, 100)}</span>}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function SchedulerPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [posts, setPosts] = useState<GMBPost[]>([]);
  const [stats, setStats] = useState<PostStats>({ total: 0, published: 0, scheduled: 0, failed: 0, draft: 0, pending: 0, ai_generated: 0 });
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchQ, setSearchQ] = useState('');
  const [loading, setLoading] = useState(false);
  const [postsLoading, setPostsLoading] = useState(true);
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [selectedPostId, setSelectedPostId] = useState<number | null>(null);
  const [charCount, setCharCount] = useState(0);
  const [formMode, setFormMode] = useState<FormMode>('auto');

  const showToast = (msg: string, type: 'success' | 'error' | 'info') => setToast({ msg, type });

  const emptyForm = { business_ids: [] as number[], profile_id: '', title: '', description: '', media_url: '', post_type: 'update' as PostType, cta_type: '', cta_value: '', schedule: false, scheduled_date: '' };
  const [form, setForm] = useState(emptyForm);
  const [formKey, setFormKey] = useState(0);

  useEffect(() => {
    axios.get(`${API_BASE}/api/businesses?limit=200`).then((r) => {
      const d = r.data;
      setBusinesses(Array.isArray(d) ? d : d.businesses || d.items || []);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    // Auto-fill profile_id only when exactly one business is selected
    if (form.business_ids.length === 1) {
      const biz = businesses.find((b) => b.id === form.business_ids[0]);
      if (biz?.gmb_url) setForm((f) => ({ ...f, profile_id: biz.gmb_url! }));
    } else {
      setForm((f) => ({ ...f, profile_id: '' }));
    }
  }, [form.business_ids, businesses]);

  const fetchPosts = () => {
    setPostsLoading(true);
    axios.get(`${API_BASE}/api/gmb-posts?limit=100`).then((r) => {
      const arr: GMBPost[] = Array.isArray(r.data) ? r.data : r.data?.items || [];
      setPosts(arr);
      setStats({
        total: arr.length,
        published: arr.filter((p) => p.status === 'published').length,
        scheduled: arr.filter((p) => p.status === 'scheduled').length,
        failed: arr.filter((p) => p.status === 'failed').length,
        draft: arr.filter((p) => p.status === 'draft').length,
        pending: arr.filter((p) => p.status === 'pending').length,
        ai_generated: arr.filter((p) => p.ai_generated).length,
      });
    }).catch(() => {}).finally(() => setPostsLoading(false));
  };

  useEffect(() => { fetchPosts(); }, []);

  const filteredPosts = posts.filter((p) => {
    const biz = businesses.find((b) => b.id === p.business_id);
    const name = biz?.business_name || biz?.name || '';
    const matchSearch = !searchQ || name.toLowerCase().includes(searchQ.toLowerCase()) || (p.title || '').toLowerCase().includes(searchQ.toLowerCase()) || p.description.toLowerCase().includes(searchQ.toLowerCase());
    return matchSearch && (statusFilter === 'all' || p.status === statusFilter) && (typeFilter === 'all' || p.post_type === typeFilter);
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.business_ids.length === 0) { showToast('Please select at least one business', 'error'); return; }
    if (!form.description.trim()) { showToast('Description is required', 'error'); return; }
    if (form.schedule && !form.scheduled_date) { showToast('Please pick a date & time to schedule', 'error'); return; }
    if (form.cta_type && form.cta_type !== 'call' && !form.cta_value.trim()) { showToast(`A URL is required for ${form.cta_type} CTA`, 'error'); return; }
    setLoading(true);
    try {
      const scheduledAt = form.schedule && form.scheduled_date ? new Date(form.scheduled_date).toISOString() : null;
      const res = await axios.post(`${API_BASE}/api/gmb-posts`, {
        businessIds: form.business_ids,
        profileId: form.business_ids.length === 1 ? (form.profile_id?.trim() || null) : null,
        title: form.title?.trim() || null,
        description: form.description,
        mediaUrl: form.media_url?.trim() || null,
        postType: form.post_type || 'update',
        ctaType: form.cta_type || null,
        ctaValue: form.cta_type && form.cta_type !== 'call' ? form.cta_value?.trim() || null : null,
        schedule: form.schedule,
        scheduledAt,
      });
      const created = res.data?.created ?? 1;
      const n = form.business_ids.length;
      showToast(
        form.schedule
          ? `Scheduled ${created} post(s) for ${n} business(es)!`
          : `Published to ${created} Google Business profile(s)!`,
        'success'
      );
      setForm(emptyForm); setCharCount(0); setFormKey((k) => k + 1); fetchPosts();
    } catch (err: any) {
      showToast(extractErrorMsg(err), 'error');
    } finally { setLoading(false); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this post? This cannot be undone.')) return;
    try { await axios.delete(`${API_BASE}/api/gmb-posts/${id}`); showToast('Post deleted', 'info'); if (selectedPostId === id) setSelectedPostId(null); fetchPosts(); }
    catch { showToast('Delete failed', 'error'); }
  };

  const handlePublishNow = async (id: number) => {
    try { await axios.post(`${API_BASE}/api/gmb-posts/${id}/trigger`); showToast('Post sent to Google Business!', 'success'); fetchPosts(); }
    catch (err: any) { showToast(extractErrorMsg(err), 'error'); }
  };

  const bizName = (id: number) => { const b = businesses.find((x) => x.id === id); return b?.business_name || b?.name || `Business #${id}`; };
  const charPct = Math.min((charCount / 1500) * 100, 100);
  const charCls = charCount > 1400 ? 'over' : charCount > 1000 ? 'warn' : '';

  const STATUS_TABS: { key: StatusFilter; label: string; count: number }[] = [
    { key: 'all', label: 'All', count: stats.total },
    { key: 'published', label: 'Published', count: stats.published },
    { key: 'scheduled', label: 'Scheduled', count: stats.scheduled },
    { key: 'pending', label: 'Pending', count: stats.pending },
    { key: 'failed', label: 'Failed', count: stats.failed },
    { key: 'draft', label: 'Draft', count: stats.draft },
  ];

  return (
    <div className="sc-page">
      <style>{CSS}</style>

      <header className="sc-topbar">
        <div className="sc-topbar-left">
          <Link href="/" className="sc-brand">
            <div className="sc-brand-dot"><Icon d={IC.trend} size={13} color="white" /></div>
            <span className="sc-brand-name">LeadMatrix</span>
          </Link>
          <div className="sc-divider" />
          <span className="sc-pg-label">GMB Scheduler</span>
        </div>
        <div className="sc-topbar-right">
          <button className="sc-btn sc-btn-ghost" onClick={fetchPosts}><Icon d={IC.refresh} size={13} /> Refresh</button>
          <Link href="/businesses-list" className="sc-btn sc-btn-ghost"><Icon d={IC.back} size={13} /> Back</Link>
        </div>
      </header>

      <main className="sc-main">
        {/* Stats */}
        <div className="sc-stats-row">
          <StatCard label="Total Posts" value={stats.total} color="#6366f1" iconPath={IC.post} />
          <StatCard label="Published" value={stats.published} color="#10b981" iconPath={IC.check} sub="Live on GMB" />
          <StatCard label="Scheduled" value={stats.scheduled} color="#3b82f6" iconPath={IC.clock} sub="Pending" />
          <StatCard label="AI Posts" value={stats.ai_generated} color="#7c3aed" iconPath={IC.sparkles} sub="Auto-generated" />
          <StatCard label="Failed" value={stats.failed} color="#ef4444" iconPath={IC.alert} sub="Needs retry" />
          <StatCard label="Drafts" value={stats.draft} color="#94a3b8" iconPath={IC.post} />
        </div>

        <div className="sc-grid">
          {/* Left Panel */}
          <div className="sc-card">
            <div className="sc-card-head" style={{ background: formMode === 'auto' ? 'linear-gradient(135deg,#f5f3ff,#eef2ff)' : 'linear-gradient(135deg,#eef2ff,#f0fdf4)' }}>
              <div className="sc-card-head-left">
                <div className="sc-card-icon" style={{ background: formMode === 'auto' ? '#7c3aed18' : '#6366f118' }}>
                  <Icon d={formMode === 'auto' ? IC.sparkles : IC.post} size={15} color={formMode === 'auto' ? '#7c3aed' : '#6366f1'} />
                </div>
                <div>
                  <div className="sc-card-title">{formMode === 'auto' ? 'AI Auto-Post' : 'Create Manual Post'}</div>
                  <div className="sc-card-sub">{formMode === 'auto' ? 'Zero input — AI writes topic, text & image' : 'Full control — write your own post'}</div>
                </div>
              </div>
            </div>

            <div className="sc-card-body">
              {/* Mode Switcher */}
              <div className="sc-mode-switch">
                <button className={`sc-mode-btn auto${formMode === 'auto' ? ' active' : ''}`} onClick={() => setFormMode('auto')}>
                  <Icon d={IC.sparkles} size={14} color={formMode === 'auto' ? '#7c3aed' : 'var(--text3)'} />
                  ⚡ AI Auto-Post
                </button>
                <button className={`sc-mode-btn manual${formMode === 'manual' ? ' active' : ''}`} onClick={() => setFormMode('manual')}>
                  <Icon d={IC.edit} size={14} color={formMode === 'manual' ? 'var(--accent)' : 'var(--text3)'} />
                  Manual Post
                </button>
              </div>

              {/* AUTO MODE */}
              {formMode === 'auto' && (
                <AutoPostPanel businesses={businesses} onSuccess={fetchPosts} showToast={showToast} />
              )}

              {/* MANUAL MODE */}
              {formMode === 'manual' && (
                <form onSubmit={handleSubmit}>
                  <div className="sc-field">
                    <div className="sc-label">
                      Businesses
                      {form.business_ids.length > 0 && <span className="sc-label-note">{form.business_ids.length} selected</span>}
                    </div>
                    <MultiBusinessSelect
                      businesses={businesses}
                      selectedIds={form.business_ids}
                      onChange={(ids) => setForm((f) => ({ ...f, business_ids: ids }))}
                    />
                  </div>

                  <div className="sc-field">
                    <div className="sc-label">Post Type</div>
                    <div className="sc-type-pills">
                      {([['update', '📝', 'Update'], ['offer', '🏷️', 'Offer'], ['event', '📅', 'Event']] as [PostType, string, string][]).map(([key, emoji, label]) => (
                        <button key={key} type="button" className={`sc-type-pill${form.post_type === key ? ' active' : ''}`} onClick={() => setForm((f) => ({ ...f, post_type: key }))}>
                          <span>{emoji}</span>{label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="sc-field">
                    <div className="sc-label">Title <span className="sc-label-note">optional</span></div>
                    <input className="sc-input" type="text" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} placeholder="e.g. Summer Sale — 20% Off All Services" />
                  </div>

                  <div className="sc-field">
                    <div className="sc-label">Description</div>
                    <textarea className="sc-textarea" rows={4} value={form.description} maxLength={1500} onChange={(e) => { setForm((f) => ({ ...f, description: e.target.value })); setCharCount(e.target.value.length); }} placeholder="Write your Google Business post here." required />
                    <div className="sc-char-row">
                      <div className="sc-char-bar-wrap"><div className={`sc-char-bar ${charCls}`} style={{ width: `${charPct}%` }} /></div>
                      <span className={`sc-char-count ${charCls}`}>{charCount}/1500</span>
                    </div>
                  </div>

                  <div className="sc-field">
                    <div className="sc-label">Image <span className="sc-label-note">optional</span></div>
                    <ImageUploader key={formKey} mediaUrl={form.media_url} onMediaUrlChange={(url) => setForm((f) => ({ ...f, media_url: url }))} onError={(msg) => showToast(msg, 'error')} />
                  </div>

                  <div className="sc-field">
                    <div className="sc-label">Call to Action</div>
                    <div className="sc-input-grid">
                      <select className="sc-select" value={form.cta_type} onChange={(e) => setForm((f) => ({ ...f, cta_type: e.target.value, cta_value: '' }))}>
                        {CTA_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
                      </select>
                      <input className="sc-input" type="text" value={form.cta_value} onChange={(e) => setForm((f) => ({ ...f, cta_value: e.target.value }))} disabled={!form.cta_type || form.cta_type === 'call'} placeholder={form.cta_type === 'call' ? 'Auto — uses GMB phone' : 'https://...'} style={!form.cta_type || form.cta_type === 'call' ? { opacity: 0.5 } : {}} />
                    </div>
                  </div>

                  <div className="sc-toggle-row">
                    <div className="sc-toggle-info">
                      <span className="sc-toggle-title">Schedule for later</span>
                      <span className="sc-toggle-sub">Auto-publish at a specific date &amp; time</span>
                    </div>
                    <button type="button" className={`sc-toggle-btn ${form.schedule ? 'on' : 'off'}`} onClick={() => setForm((f) => ({ ...f, schedule: !f.schedule, scheduled_date: '' }))}>
                      <div className="sc-toggle-thumb" />
                    </button>
                  </div>

                  {form.schedule && (
                    <div className="sc-schedule-panel">
                      <div className="sc-schedule-panel-title"><Icon d={IC.calendar} size={13} color="#92400e" /> Pick date &amp; time</div>
                      <div className="sc-field" style={{ marginBottom: 0 }}>
                        <div className="sc-label">Schedule Date &amp; Time</div>
                        <input className="sc-input" type="datetime-local" value={form.scheduled_date} min={new Date(Date.now() + 60000).toISOString().slice(0, 16)} onChange={(e) => setForm((f) => ({ ...f, scheduled_date: e.target.value }))} required={form.schedule} style={{ background: 'white' }} />
                        {form.scheduled_date && <div style={{ fontSize: '.7rem', color: '#92400e', marginTop: 5, fontWeight: 600 }}>Will publish {new Date(form.scheduled_date).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</div>}
                      </div>
                    </div>
                  )}

                  <button type="submit" className={`sc-submit${form.schedule ? ' sc-submit-schedule' : ''}`} disabled={loading}>
                    {loading ? (<><div className="sc-spinner" />{form.schedule ? 'Scheduling…' : 'Publishing…'}</>) : form.schedule ? (<><Icon d={IC.calendar} size={15} color="white" /> Schedule Post</>) : (<><Icon d={IC.zap} size={15} color="white" /> Publish Now to GMB</>)}
                  </button>
                </form>
              )}
            </div>
          </div>

          {/* Right Panel — Posts Table */}
          <div className="sc-card" style={{ minHeight: 500 }}>
            <div className="sc-status-tabs">
              {STATUS_TABS.map((tab) => (
                <button key={tab.key} className={`sc-status-tab${statusFilter === tab.key ? ' active' : ''}`} onClick={() => setStatusFilter(tab.key)}>
                  {tab.label}
                  {tab.count > 0 && <span className={`sc-tab-badge ${statusFilter === tab.key ? 'sc-tab-badge-active' : 'sc-tab-badge-default'}`}>{tab.count}</span>}
                </button>
              ))}
            </div>

            <div className="sc-toolbar">
              <div className="sc-toolbar-left">
                <span style={{ fontSize: '.82rem', fontWeight: 700, color: 'var(--text1)' }}>Posts</span>
                <span className="sc-count-badge">{filteredPosts.length}</span>
                {stats.ai_generated > 0 && <span style={{ fontSize: '.72rem', color: 'var(--ai)', fontWeight: 600, background: 'var(--aiL)', padding: '2px 8px', borderRadius: 99, border: '1px solid #ddd6fe' }}>✦ {stats.ai_generated} AI</span>}
              </div>
              <div className="sc-toolbar-right">
                <div className="sc-search-wrap">
                  <span className="sc-search-ico"><Icon d={IC.search} size={12} color="var(--text3)" /></span>
                  <input className="sc-search-input" type="text" value={searchQ} onChange={(e) => setSearchQ(e.target.value)} placeholder="Search posts…" />
                </div>
                <select className="sc-filter-select" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                  <option value="all">All Types</option>
                  <option value="update">Update</option>
                  <option value="offer">Offer</option>
                  <option value="event">Event</option>
                </select>
              </div>
            </div>

            {postsLoading ? (
              <div className="sc-load-row"><div className="sc-load-spin" /><span style={{ fontSize: '.82rem', color: 'var(--text3)' }}>Loading posts…</span></div>
            ) : filteredPosts.length === 0 ? (
              <div className="sc-empty">
                <div className="sc-empty-icon"><Icon d={IC.post} size={20} color="var(--text3)" /></div>
                <div className="sc-empty-title">No posts found</div>
                <div className="sc-empty-sub">{searchQ ? 'Try a different search term' : 'Create your first post using the form on the left'}</div>
              </div>
            ) : (
              <div className="sc-table-wrap">
                <table className="sc-table">
                  <thead>
                    <tr><th>Business</th><th>Content</th><th>Type</th><th>Status</th><th>Date</th><th>Actions</th></tr>
                  </thead>
                  <tbody>
                    {filteredPosts.map((post) => (
                      <PostRow key={post.id} post={post} isSelected={selectedPostId === post.id} bizName={bizName} onSelect={() => setSelectedPostId(selectedPostId === post.id ? null : post.id)} onPublish={handlePublishNow} onDelete={handleDelete} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="sc-table-footer">
              <span className="sc-table-footer-txt">{filteredPosts.length} of {posts.length} posts{statusFilter !== 'all' ? ` · ${statusFilter}` : ''}</span>
              <button className="sc-refresh-link" onClick={fetchPosts}>Refresh</button>
            </div>
          </div>
        </div>
      </main>

      {toast && <Toast msg={toast.msg} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}
