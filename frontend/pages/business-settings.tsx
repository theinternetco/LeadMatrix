'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import axios from 'axios';
import API_BASE from '../lib/api';

interface Business {
  id: number;
  name: string;
  category?: string;
  city?: string;
  keywords: string[];
}

const Icon = ({ d, size = 16, color = 'currentColor' }: { d: string; size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

const IC = {
  back:     'M19 12H5M12 5l-7 7 7 7',
  search:   'M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0z',
  tag:      'M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82zM7 7h.01',
  check:    'M20 6L9 17l-5-5',
  settings: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z',
  trend:    'M22 7l-9.2 9.2-4.8-4.8L2 18',
};

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', -apple-system, sans-serif; }
  :root {
    --bg: #f8fafc; --surface: #ffffff; --border: #e2e8f0; --border2: #f1f5f9;
    --text1: #0f172a; --text2: #475569; --text3: #94a3b8;
    --accent: #6366f1; --accentL: #eef2ff; --green: #10b981; --red: #ef4444;
  }
  .bs-page { min-height:100vh; background:var(--bg); color:var(--text1); font-family:'Inter',-apple-system,sans-serif; }
  .bs-topbar { position:sticky; top:0; z-index:100; background:var(--surface); border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; padding:0 24px; height:58px; gap:12px; }
  .bs-topbar-left { display:flex; align-items:center; gap:10px; }
  .bs-brand { display:flex; align-items:center; gap:8px; text-decoration:none; }
  .bs-brand-dot { width:28px; height:28px; border-radius:8px; background:linear-gradient(135deg,#6366f1,#8b5cf6); display:flex; align-items:center; justify-content:center; }
  .bs-brand-name { font-size:.88rem; font-weight:700; color:var(--text1); }
  .bs-divider { width:1px; height:20px; background:var(--border); }
  .bs-pg-label { font-size:.82rem; color:var(--text2); font-weight:500; }
  .bs-btn { display:inline-flex; align-items:center; gap:6px; padding:0 14px; height:34px; border-radius:8px; font-size:.79rem; font-weight:600; cursor:pointer; border:1.5px solid transparent; transition:all .14s; font-family:inherit; white-space:nowrap; text-decoration:none; }
  .bs-btn-ghost { background:transparent; border-color:var(--border); color:var(--text2); }
  .bs-btn-ghost:hover { background:var(--bg); color:var(--text1); }
  .bs-main { max-width:960px; margin:0 auto; padding:28px 24px 56px; }
  .bs-page-title { font-size:1.35rem; font-weight:800; color:var(--text1); letter-spacing:-.5px; margin-bottom:4px; }
  .bs-page-sub { font-size:.82rem; color:var(--text3); margin-bottom:24px; }
  .bs-search-wrap { position:relative; margin-bottom:20px; }
  .bs-search-ico { position:absolute; left:12px; top:50%; transform:translateY(-50%); pointer-events:none; }
  .bs-search-input { width:100%; height:40px; padding:0 14px 0 38px; background:var(--surface); border:1.5px solid var(--border); border-radius:10px; font-size:.83rem; color:var(--text1); outline:none; font-family:inherit; transition:border-color .14s; }
  .bs-search-input:focus { border-color:var(--accent); }
  .bs-search-input::placeholder { color:var(--text3); }
  .bs-list { display:flex; flex-direction:column; gap:12px; }
  .bs-card { background:var(--surface); border:1.5px solid var(--border); border-radius:13px; padding:18px 20px; transition:box-shadow .15s; }
  .bs-card:hover { box-shadow:0 4px 16px rgba(0,0,0,.06); }
  .bs-card-top { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; margin-bottom:14px; }
  .bs-card-info { display:flex; align-items:center; gap:12px; }
  .bs-avatar { width:40px; height:40px; border-radius:11px; background:linear-gradient(135deg,#6366f1,#8b5cf6); display:flex; align-items:center; justify-content:center; color:white; font-size:.9rem; font-weight:800; flex-shrink:0; }
  .bs-biz-name { font-size:.92rem; font-weight:700; color:var(--text1); }
  .bs-biz-meta { font-size:.72rem; color:var(--text3); margin-top:2px; }
  .bs-save-btn { display:inline-flex; align-items:center; gap:5px; height:30px; padding:0 12px; border-radius:7px; font-size:.73rem; font-weight:700; font-family:inherit; cursor:pointer; border:1.5px solid transparent; transition:all .14s; white-space:nowrap; }
  .bs-save-btn-idle { background:var(--accentL); color:var(--accent); border-color:#c7d2fe; }
  .bs-save-btn-idle:hover { background:#e0e7ff; }
  .bs-save-btn-saving { background:#f0fdf4; color:#15803d; border-color:#bbf7d0; cursor:default; }
  .bs-save-btn-saved { background:#f0fdf4; color:#15803d; border-color:#bbf7d0; cursor:default; }
  .bs-kw-section { }
  .bs-kw-label { font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.7px; color:var(--text3); margin-bottom:8px; }
  .bs-kw-tags { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; min-height:28px; }
  .bs-tag { display:inline-flex; align-items:center; gap:5px; padding:4px 8px 4px 10px; background:var(--accentL); border:1.5px solid #c7d2fe; border-radius:20px; font-size:.73rem; font-weight:600; color:var(--accent); }
  .bs-tag-x { background:none; border:none; cursor:pointer; color:#a5b4fc; font-size:15px; line-height:1; padding:0; display:flex; align-items:center; transition:color .12s; }
  .bs-tag-x:hover { color:var(--red); }
  .bs-kw-input-row { display:flex; gap:8px; }
  .bs-kw-input { flex:1; height:36px; padding:0 12px; background:var(--bg); border:1.5px solid var(--border); border-radius:9px; font-size:.82rem; color:var(--text1); outline:none; font-family:inherit; transition:border-color .14s; }
  .bs-kw-input:focus { border-color:var(--accent); background:var(--surface); }
  .bs-kw-input::placeholder { color:var(--text3); }
  .bs-kw-add { height:36px; padding:0 14px; border-radius:9px; background:var(--accent); color:white; border:none; font-size:.78rem; font-weight:700; font-family:inherit; cursor:pointer; transition:opacity .14s; white-space:nowrap; }
  .bs-kw-add:hover { opacity:.88; }
  .bs-kw-hint { font-size:.67rem; color:var(--text3); margin-top:5px; }
  .bs-empty { text-align:center; padding:60px 24px; color:var(--text3); font-size:.88rem; }
  .bs-load { display:flex; align-items:center; justify-content:center; gap:10px; padding:60px; color:var(--text3); font-size:.85rem; }
  .bs-spinner { width:18px; height:18px; border:2.5px solid var(--border); border-top-color:var(--accent); border-radius:50%; animation:bs-spin .7s linear infinite; }
  @keyframes bs-spin { to { transform:rotate(360deg); } }
  .bs-toast { position:fixed; bottom:24px; right:24px; z-index:9999; display:flex; align-items:center; gap:10px; padding:12px 18px; border-radius:12px; font-size:.82rem; font-weight:600; color:white; box-shadow:0 8px 32px rgba(0,0,0,.18); animation:bs-toast-in .3s cubic-bezier(.16,1,.3,1); }
  .bs-toast-success { background:linear-gradient(135deg,#10b981,#059669); }
  .bs-toast-error   { background:linear-gradient(135deg,#ef4444,#dc2626); }
  @keyframes bs-toast-in { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
`;

function Toast({ msg, type, onClose }: { msg: string; type: 'success' | 'error'; onClose: () => void }) {
  useEffect(() => { const t = setTimeout(onClose, 3000); return () => clearTimeout(t); }, [onClose]);
  return <div className={`bs-toast bs-toast-${type}`}>{msg}</div>;
}

function BusinessCard({ biz, onSaved }: { biz: Business; onSaved: (id: number, keywords: string[]) => void }) {
  const [keywords, setKeywords] = useState<string[]>(biz.keywords || []);
  const [input, setInput]       = useState('');
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved'>('idle');
  const inputRef = useRef<HTMLInputElement>(null);

  const isDirty = JSON.stringify(keywords) !== JSON.stringify(biz.keywords || []);

  const addKeyword = () => {
    const kw = input.trim();
    if (!kw || keywords.includes(kw)) { setInput(''); return; }
    setKeywords((prev) => [...prev, kw]);
    setInput('');
  };

  const removeKeyword = (kw: string) => setKeywords((prev) => prev.filter((k) => k !== kw));

  const handleSave = async () => {
    setSaveState('saving');
    try {
      await axios.patch(`${API_BASE}/api/businesses/${biz.id}/keywords`, { keywords });
      onSaved(biz.id, keywords);
      setSaveState('saved');
      setTimeout(() => setSaveState('idle'), 2000);
    } catch {
      setSaveState('idle');
    }
  };

  const initial = (biz.name || '?').charAt(0).toUpperCase();

  return (
    <div className="bs-card">
      <div className="bs-card-top">
        <div className="bs-card-info">
          <div className="bs-avatar">{initial}</div>
          <div>
            <div className="bs-biz-name">{biz.name}</div>
            <div className="bs-biz-meta">
              {[biz.category, biz.city].filter(Boolean).join(' · ')}
            </div>
          </div>
        </div>
        {isDirty && (
          <button
            className={`bs-save-btn ${saveState === 'idle' ? 'bs-save-btn-idle' : 'bs-save-btn-saved'}`}
            onClick={handleSave}
            disabled={saveState !== 'idle'}
          >
            {saveState === 'saving' ? (
              <><div className="bs-spinner" style={{ width: 11, height: 11, borderWidth: 2 }} /> Saving…</>
            ) : saveState === 'saved' ? (
              <><Icon d={IC.check} size={11} color="#15803d" /> Saved</>
            ) : (
              'Save keywords'
            )}
          </button>
        )}
      </div>

      <div className="bs-kw-section">
        <div className="bs-kw-label">
          Keywords ({keywords.length})
        </div>
        {keywords.length > 0 && (
          <div className="bs-kw-tags">
            {keywords.map((kw) => (
              <span key={kw} className="bs-tag">
                {kw}
                <button type="button" className="bs-tag-x" onClick={() => removeKeyword(kw)}>×</button>
              </span>
            ))}
          </div>
        )}
        <div className="bs-kw-input-row">
          <input
            ref={inputRef}
            className="bs-kw-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addKeyword(); } }}
            placeholder="e.g. plumbing, emergency repair, Mumbai…"
          />
          <button type="button" className="bs-kw-add" onClick={addKeyword}>Add</button>
        </div>
        <div className="bs-kw-hint">Press Enter or click Add · Click × to remove a keyword · Click "Save keywords" to persist</div>
      </div>
    </div>
  );
}

export default function BusinessSettings() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading]       = useState(true);
  const [searchQ, setSearchQ]       = useState('');
  const [toast, setToast]           = useState<{ msg: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    axios.get(`${API_BASE}/api/businesses?limit=500`)
      .then((r) => {
        const d = r.data;
        const list = Array.isArray(d) ? d : d.businesses || [];
        setBusinesses(list.map((b: any) => ({
          id:       b.id,
          name:     b.name || b.business_name || `Business #${b.id}`,
          category: b.category,
          city:     b.city,
          keywords: b.keywords || [],
        })));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSaved = useCallback((id: number, keywords: string[]) => {
    setBusinesses((prev) => prev.map((b) => b.id === id ? { ...b, keywords } : b));
    setToast({ msg: 'Keywords saved', type: 'success' });
  }, []);

  const filtered = businesses.filter((b) => {
    if (!searchQ) return true;
    const q = searchQ.toLowerCase();
    return (b.name || '').toLowerCase().includes(q) || (b.city || '').toLowerCase().includes(q) || (b.category || '').toLowerCase().includes(q);
  });

  return (
    <div className="bs-page">
      <style>{CSS}</style>

      <header className="bs-topbar">
        <div className="bs-topbar-left">
          <Link href="/" className="bs-brand">
            <div className="bs-brand-dot"><Icon d={IC.trend} size={13} color="white" /></div>
            <span className="bs-brand-name">LeadMatrix</span>
          </Link>
          <div className="bs-divider" />
          <span className="bs-pg-label">Business Settings</span>
        </div>
        <Link href="/dashboard" className="bs-btn bs-btn-ghost">
          <Icon d={IC.back} size={13} /> Dashboard
        </Link>
      </header>

      <main className="bs-main">
        <div className="bs-page-title">Business Settings</div>
        <div className="bs-page-sub">Add keywords for each business — the AI uses them when generating posts.</div>

        <div className="bs-search-wrap">
          <span className="bs-search-ico"><Icon d={IC.search} size={14} color="var(--text3)" /></span>
          <input
            className="bs-search-input"
            type="text"
            value={searchQ}
            onChange={(e) => setSearchQ(e.target.value)}
            placeholder="Search businesses by name, city or category…"
          />
        </div>

        {loading ? (
          <div className="bs-load"><div className="bs-spinner" /> Loading businesses…</div>
        ) : filtered.length === 0 ? (
          <div className="bs-empty">{searchQ ? 'No businesses match your search.' : 'No businesses found.'}</div>
        ) : (
          <div className="bs-list">
            {filtered.map((biz) => (
              <BusinessCard key={biz.id} biz={biz} onSaved={handleSaved} />
            ))}
          </div>
        )}
      </main>

      {toast && <Toast msg={toast.msg} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}
