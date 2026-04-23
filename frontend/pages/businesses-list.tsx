'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import Link from 'next/link';
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ─── Types ────────────────────────────────────────────────────
interface Business {
  id: number;
  name: string;
  business_name: string;
  category: string;
  city: string;
  phone: string;
  phone_number: string;
  address: string;
  website: string;
  status: string;
}

type SortField = 'id' | 'name' | 'category' | 'city' | 'status';
type SortOrder = 'asc' | 'desc';
type ViewMode  = 'table' | 'grid';

// ─── Minimal SVG Icons ────────────────────────────────────────
const Icon = ({ d, size = 16, color = 'currentColor', strokeWidth = 1.8 }: {
  d: string; size?: number; color?: string; strokeWidth?: number;
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

const IC = {
  search:   'M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0z',
  refresh:  'M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15',
  download: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3',
  plus:     'M12 5v14M5 12h14',
  sun:      'M12 3v1m0 16v1m9-9h-1M4 12H3m15.36-6.36-.7.7M6.34 17.66l-.7.7m12.72 0-.7-.7M6.34 6.34l-.7-.7M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
  moon:     'M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z',
  table:    'M3 3h18v18H3zM3 9h18M3 15h18M9 3v18M15 3v18',
  grid:     'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z',
  building: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM9 22V12h6v10',
  check:    'M20 6L9 17l-5-5',
  pin:      'M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0zM12 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  tag:      'M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82zM7 7h.01',
  chart:    'M18 20V10M12 20V4M6 20v-6',
  edit:     'M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z',
  trash:    'M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2',
  filter:   'M22 3H2l8 9.46V19l4 2V12.46L22 3z',
  x:        'M18 6 6 18M6 6l12 12',
  sortUp:   'M12 5l-7 7h14zM5 17h14',
  chevD:    'M6 9l6 6 6-6',
  phone:    'M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z',
  globe:    'M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 0c-2.5 2.5-4 5.5-4 10s1.5 7.5 4 10m0-20c2.5 2.5 4 5.5 4 10s-1.5 7.5-4 10M2 12h20',
  warn:     'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01',
  arrowL:   'M19 12H5M12 5l-7 7 7 7',
};

// ─── Helpers ──────────────────────────────────────────────────
const getBizName = (b: Business) => b.name || b.business_name || 'Unnamed';
const getPhone   = (b: Business) => b.phone || b.phone_number || '—';
const getInitial = (b: Business) => getBizName(b)[0]?.toUpperCase() || '?';
const AVATAR_COLORS = [
  '#6366f1','#8b5cf6','#06b6d4','#10b981','#f59e0b','#ef4444','#ec4899','#0ea5e9'
];
const getAvatarColor = (id: number) => AVATAR_COLORS[id % AVATAR_COLORS.length];

// ─── Global CSS ───────────────────────────────────────────────
const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:       #f8fafc;
    --surface:  #ffffff;
    --border:   #e2e8f0;
    --border2:  #f1f5f9;
    --text1:    #0f172a;
    --text2:    #475569;
    --text3:    #94a3b8;
    --accent:   #6366f1;
    --accentBg: #eef2ff;
    --green:    #10b981;
    --red:      #ef4444;
    --amber:    #f59e0b;
  }
  .dark {
    --bg:       #0f172a;
    --surface:  #1e293b;
    --border:   #334155;
    --border2:  #1e293b;
    --text1:    #f1f5f9;
    --text2:    #94a3b8;
    --text3:    #64748b;
    --accentBg: #1e1b4b;
  }
  body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
  
  .bl-page { min-height: 100vh; background: var(--bg); color: var(--text1); transition: background .2s, color .2s; }
  
  /* Topbar */
  .bl-topbar { position: sticky; top: 0; z-index: 100; background: var(--surface); border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; padding: 0 28px; height: 60px; gap: 14px; }
  .bl-topbar-left { display: flex; align-items: center; gap: 12px; }
  .bl-topbar-right { display: flex; align-items: center; gap: 8px; }
  .bl-brand { display: flex; align-items: center; gap: 8px; text-decoration: none; }
  .bl-brand-dot { width: 28px; height: 28px; border-radius: 8px; background: linear-gradient(135deg, #6366f1, #8b5cf6); display: flex; align-items: center; justify-content: center; }
  .bl-brand-name { font-size: 0.9rem; font-weight: 700; color: var(--text1); letter-spacing: -0.3px; }
  .bl-divider { width: 1px; height: 22px; background: var(--border); }
  .bl-page-title { font-size: 0.85rem; font-weight: 600; color: var(--text2); }
  
  /* Search bar */
  .bl-search { display: flex; align-items: center; gap: 8px; background: var(--bg); border: 1.5px solid var(--border); border-radius: 10px; padding: 0 12px; height: 36px; width: 260px; transition: border-color .15s, box-shadow .15s; }
  .bl-search:focus-within { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(99,102,241,.1); }
  .bl-search input { background: none; border: none; outline: none; font-size: 0.83rem; color: var(--text1); width: 100%; font-family: inherit; }
  .bl-search input::placeholder { color: var(--text3); }

  /* Buttons */
  .bl-btn { display: inline-flex; align-items: center; gap: 6px; padding: 0 14px; height: 36px; border-radius: 9px; font-size: 0.82rem; font-weight: 600; cursor: pointer; border: 1.5px solid transparent; transition: all .15s; font-family: inherit; white-space: nowrap; }
  .bl-btn-ghost { background: transparent; border-color: var(--border); color: var(--text2); }
  .bl-btn-ghost:hover { background: var(--bg); color: var(--text1); }
  .bl-btn-primary { background: var(--accent); color: white; border-color: var(--accent); box-shadow: 0 2px 8px rgba(99,102,241,.25); }
  .bl-btn-primary:hover { opacity: .92; box-shadow: 0 4px 14px rgba(99,102,241,.35); }
  .bl-btn-danger { background: #fef2f2; color: var(--red); border-color: #fecaca; }
  .bl-btn-danger:hover { background: #fee2e2; }
  .bl-btn-icon { width: 36px; height: 36px; padding: 0; justify-content: center; }

  /* Main content */
  .bl-main { max-width: 1480px; margin: 0 auto; padding: 28px 28px 48px; }

  /* Page heading */
  .bl-heading { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 16px; margin-bottom: 28px; }
  .bl-heading h1 { font-size: 1.5rem; font-weight: 800; color: var(--text1); letter-spacing: -0.5px; line-height: 1.2; }
  .bl-heading p { font-size: 0.83rem; color: var(--text2); margin-top: 4px; }
  .bl-heading-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

  /* Stats */
  .bl-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 24px; }
  .bl-stat { background: var(--surface); border: 1.5px solid var(--border); border-radius: 14px; padding: 18px 20px; display: flex; align-items: center; gap: 14px; transition: border-color .15s, box-shadow .15s; }
  .bl-stat:hover { border-color: var(--accent); box-shadow: 0 4px 16px rgba(99,102,241,.08); }
  .bl-stat-icon { width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .bl-stat-label { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .6px; color: var(--text3); margin-bottom: 4px; }
  .bl-stat-val { font-size: 1.6rem; font-weight: 800; color: var(--text1); line-height: 1; }

  /* Filter bar */
  .bl-filterbar { background: var(--surface); border: 1.5px solid var(--border); border-radius: 14px; padding: 16px 20px; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .bl-filterbar select, .bl-filterbar-input { height: 36px; padding: 0 12px; background: var(--bg); border: 1.5px solid var(--border); border-radius: 9px; font-size: 0.82rem; color: var(--text1); outline: none; font-family: inherit; transition: border-color .15s, box-shadow .15s; cursor: pointer; }
  .bl-filterbar select:focus, .bl-filterbar-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(99,102,241,.1); }
  .bl-filter-divider { width: 1px; height: 22px; background: var(--border); margin: 0 4px; }
  .bl-filter-info { font-size: 0.78rem; color: var(--text3); margin-left: auto; white-space: nowrap; }
  
  /* View toggle */
  .bl-view-toggle { display: flex; gap: 2px; background: var(--bg); border: 1.5px solid var(--border); border-radius: 9px; padding: 3px; }
  .bl-view-btn { width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border: none; border-radius: 6px; cursor: pointer; background: transparent; color: var(--text3); transition: all .15s; }
  .bl-view-btn.active { background: var(--surface); color: var(--accent); box-shadow: 0 1px 4px rgba(0,0,0,.08); }

  /* Bulk action bar */
  .bl-bulk-bar { background: var(--accentBg); border: 1.5px solid rgba(99,102,241,.2); border-radius: 12px; padding: 10px 16px; margin-bottom: 12px; display: flex; align-items: center; gap: 12px; animation: fadeSlideIn .2s ease; }
  .bl-bulk-count { font-size: 0.82rem; font-weight: 600; color: var(--accent); }
  @keyframes fadeSlideIn { from { opacity:0; transform: translateY(-6px); } to { opacity:1; transform: translateY(0); } }

  /* Table */
  .bl-table-wrap { background: var(--surface); border: 1.5px solid var(--border); border-radius: 14px; overflow: hidden; margin-bottom: 16px; }
  .bl-table { width: 100%; border-collapse: collapse; min-width: 820px; }
  .bl-table thead { background: var(--bg); }
  .bl-table th { padding: 11px 16px; text-align: left; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .6px; color: var(--text3); border-bottom: 1.5px solid var(--border); white-space: nowrap; }
  .bl-table th.sortable { cursor: pointer; user-select: none; }
  .bl-table th.sortable:hover { color: var(--accent); }
  .bl-table td { padding: 13px 16px; font-size: 0.83rem; color: var(--text1); border-bottom: 1px solid var(--border2); vertical-align: middle; }
  .bl-table tbody tr { transition: background .1s; }
  .bl-table tbody tr:hover td { background: var(--bg); }
  .bl-table tbody tr:last-child td { border-bottom: none; }
  .bl-table tbody tr.selected td { background: var(--accentBg); }

  /* Business cell */
  .bl-biz-cell { display: flex; align-items: center; gap: 10px; }
  .bl-avatar { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 800; color: white; flex-shrink: 0; }
  .bl-biz-name { font-weight: 600; color: var(--text1); font-size: 0.85rem; }
  .bl-biz-addr { font-size: 0.73rem; color: var(--text3); max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-top: 2px; }

  /* Badges */
  .bl-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 9px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; white-space: nowrap; }
  .bl-badge-id { background: #eef2ff; color: #4338ca; }
  .bl-badge-cat { background: #fef3c7; color: #92400e; }
  .bl-badge-active { background: #d1fae5; color: #065f46; }
  .bl-badge-inactive { background: #f1f5f9; color: #475569; }

  /* Action buttons */
  .bl-action-wrap { display: flex; align-items: center; gap: 4px; justify-content: flex-end; }
  .bl-action-btn { width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; border-radius: 7px; border: 1.5px solid transparent; cursor: pointer; transition: all .15s; text-decoration: none; font-family: inherit; }
  .bl-action-btn.view  { background: #eef2ff; color: #4338ca; border-color: #c7d2fe; }
  .bl-action-btn.view:hover  { background: #e0e7ff; }
  .bl-action-btn.edit  { background: #f0fdf4; color: #15803d; border-color: #bbf7d0; }
  .bl-action-btn.edit:hover  { background: #dcfce7; }
  .bl-action-btn.del   { background: #fff1f2; color: #be123c; border-color: #fecdd3; }
  .bl-action-btn.del:hover   { background: #ffe4e6; }

  /* Grid cards */
  .bl-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; margin-bottom: 16px; }
  .bl-card { background: var(--surface); border: 1.5px solid var(--border); border-radius: 14px; padding: 20px; transition: all .2s; }
  .bl-card:hover { border-color: var(--accent); box-shadow: 0 8px 24px rgba(99,102,241,.1); transform: translateY(-2px); }
  .bl-card.selected { border-color: var(--accent); background: var(--accentBg); }
  .bl-card-head { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
  .bl-card-avatar { width: 40px; height: 40px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.88rem; color: white; flex-shrink: 0; }
  .bl-card-title { font-size: 0.93rem; font-weight: 700; color: var(--text1); line-height: 1.3; flex: 1; }
  .bl-card-body { display: flex; flex-direction: column; gap: 7px; margin-bottom: 16px; }
  .bl-card-row { display: flex; align-items: center; gap: 7px; font-size: 0.78rem; color: var(--text2); }
  .bl-card-row span.label { color: var(--text3); font-weight: 500; }
  .bl-card-footer { display: flex; gap: 7px; align-items: center; padding-top: 14px; border-top: 1px solid var(--border); }
  .bl-card-link { display: inline-flex; align-items: center; gap: 5px; padding: 0 12px; height: 30px; border-radius: 7px; font-size: 0.75rem; font-weight: 600; text-decoration: none; transition: all .15s; }

  /* Empty state */
  .bl-empty { padding: 64px 24px; text-align: center; }
  .bl-empty-icon { width: 56px; height: 56px; border-radius: 16px; background: var(--bg); border: 1.5px solid var(--border); display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; }
  .bl-empty-title { font-size: 1rem; font-weight: 700; color: var(--text1); margin-bottom: 6px; }
  .bl-empty-sub { font-size: 0.82rem; color: var(--text3); }

  /* Pagination */
  .bl-pagination { background: var(--surface); border: 1.5px solid var(--border); border-radius: 12px; padding: 12px 18px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
  .bl-pagination-info { display: flex; align-items: center; gap: 12px; }
  .bl-pagination-info label { display: flex; align-items: center; gap: 7px; font-size: 0.78rem; color: var(--text2); }
  .bl-pagination-info select { height: 30px; padding: 0 8px; background: var(--bg); border: 1.5px solid var(--border); border-radius: 7px; font-size: 0.78rem; color: var(--text1); outline: none; font-family: inherit; cursor: pointer; }
  .bl-pagination-text { font-size: 0.78rem; color: var(--text3); }
  .bl-pagination-btns { display: flex; gap: 4px; }
  .bl-pg-btn { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: 1.5px solid var(--border); border-radius: 7px; background: var(--surface); color: var(--text2); font-size: 0.78rem; font-weight: 600; cursor: pointer; transition: all .15s; font-family: inherit; }
  .bl-pg-btn:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
  .bl-pg-btn.active { background: var(--accent); color: white; border-color: var(--accent); }
  .bl-pg-btn:disabled { opacity: .35; cursor: not-allowed; }

  /* Toast */
  .bl-toast { position: fixed; bottom: 24px; right: 24px; z-index: 9999; display: flex; align-items: center; gap: 10px; padding: 13px 18px; background: var(--surface); border: 1.5px solid var(--border); border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,.15); font-size: 0.84rem; font-weight: 600; color: var(--text1); animation: toastIn .25s ease; max-width: 340px; }
  .bl-toast-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); flex-shrink: 0; }
  @keyframes toastIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

  /* Loading skeleton */
  .bl-skeleton { background: linear-gradient(90deg, var(--border) 25%, var(--border2) 50%, var(--border) 75%); background-size: 200%; border-radius: 6px; animation: shimmer 1.4s infinite; }
  @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

  /* Loading page */
  .bl-loading-page { min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; background: var(--bg); }
  .bl-spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin .8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .bl-loading-text { font-size: 0.88rem; font-weight: 500; color: var(--text3); }

  /* Error page */
  .bl-error-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg); padding: 24px; }
  .bl-error-box { background: var(--surface); border: 1.5px solid var(--border); border-radius: 18px; padding: 40px; max-width: 480px; width: 100%; text-align: center; }
  .bl-error-icon { width: 56px; height: 56px; background: #fef2f2; border-radius: 16px; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; }
  .bl-error-title { font-size: 1.1rem; font-weight: 700; color: var(--text1); margin-bottom: 10px; }
  .bl-error-msg { font-size: 0.84rem; color: var(--text2); line-height: 1.6; margin-bottom: 24px; }
  
  /* Checkbox */
  .bl-checkbox { width: 16px; height: 16px; cursor: pointer; accent-color: var(--accent); }

  /* Responsive */
  @media (max-width: 768px) {
    .bl-topbar { padding: 0 16px; }
    .bl-main { padding: 16px 16px 40px; }
    .bl-search { display: none; }
    .bl-stats { grid-template-columns: repeat(2, 1fr); }
  }
`;

// ─── Component ────────────────────────────────────────────────
export default function BusinessesList() {
  const [businesses, setBusinesses]     = useState<Business[]>([]);
  const [loading, setLoading]           = useState(true);
  const [error, setError]               = useState('');

  const [searchTerm, setSearchTerm]         = useState('');
  const [filterCity, setFilterCity]         = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterStatus, setFilterStatus]     = useState('');

  const [sortField, setSortField] = useState<SortField>('id');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  const [currentPage, setCurrentPage]   = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const [viewMode, setViewMode]         = useState<ViewMode>('table');

  const [selectedIds, setSelectedIds]           = useState<number[]>([]);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);

  const [darkMode, setDarkMode]                 = useState(false);

  const [showToastState, setShowToastState]     = useState(false);
  const [toastMessage, setToastMessage]         = useState('');
  const [toastType, setToastType]               = useState<'success'|'error'>('success');

  useEffect(() => {
    const saved = localStorage.getItem('darkMode');
    if (saved === 'true') setDarkMode(true);
  }, []);

  useEffect(() => {
    localStorage.setItem('darkMode', darkMode.toString());
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  const showToast = (msg: string, type: 'success'|'error' = 'success') => {
    setToastMessage(msg);
    setToastType(type);
    setShowToastState(true);
    setTimeout(() => setShowToastState(false), 3200);
  };

  const fetchBusinesses = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const r = await axios.get(`${API_BASE}/api/businesses`, { timeout: 5000 });
      setBusinesses(r.data.businesses || []);
      setLoading(false);
      showToast('Businesses loaded successfully');
    } catch {
      setError('Failed to connect to backend. Make sure your FastAPI server is running.');
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchBusinesses(); }, [fetchBusinesses]);

  const filteredAndSorted = useMemo(() => {
    let f = businesses;
    if (searchTerm) {
      const t = searchTerm.toLowerCase();
      f = f.filter(b =>
        getBizName(b).toLowerCase().includes(t) ||
        b.city?.toLowerCase().includes(t) ||
        b.category?.toLowerCase().includes(t) ||
        b.phone?.toLowerCase().includes(t)
      );
    }
    if (filterCity)     f = f.filter(b => b.city     === filterCity);
    if (filterCategory) f = f.filter(b => b.category === filterCategory);
    if (filterStatus)   f = f.filter(b => b.status   === filterStatus);

    return [...f].sort((a, b) => {
      let av: any = sortField === 'name' ? getBizName(a) : (a[sortField] || '');
      let bv: any = sortField === 'name' ? getBizName(b) : (b[sortField] || '');
      if (typeof av === 'string') return sortOrder === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortOrder === 'asc' ? av - bv : bv - av;
    });
  }, [businesses, searchTerm, filterCity, filterCategory, filterStatus, sortField, sortOrder]);

  const paginated = useMemo(() => {
    const s = (currentPage - 1) * itemsPerPage;
    return filteredAndSorted.slice(s, s + itemsPerPage);
  }, [filteredAndSorted, currentPage, itemsPerPage]);

  const totalPages  = Math.ceil(filteredAndSorted.length / itemsPerPage);
  const cities      = useMemo(() => Array.from(new Set(businesses.map(b => b.city).filter(Boolean))), [businesses]);
  const categories  = useMemo(() => Array.from(new Set(businesses.map(b => b.category).filter(Boolean))), [businesses]);
  const statuses    = useMemo(() => Array.from(new Set(businesses.map(b => b.status).filter(Boolean))), [businesses]);

  const handleSort = (field: SortField) => {
    if (sortField === field) setSortOrder(o => o === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortOrder('asc'); }
    setCurrentPage(1);
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    try {
      await axios.delete(`${API_BASE}/api/businesses/${id}`);
      showToast('Business deleted');
      fetchBusinesses();
      setSelectedIds(p => p.filter(x => x !== id));
    } catch { showToast('Failed to delete business', 'error'); }
  };

  const handleBulkDelete = async () => {
    if (!selectedIds.length) return;
    if (!confirm(`Delete ${selectedIds.length} selected businesses?`)) return;
    setBulkActionLoading(true);
    try {
      await Promise.all(selectedIds.map(id => axios.delete(`${API_BASE}/api/businesses/${id}`)));
      showToast(`${selectedIds.length} businesses deleted`);
      fetchBusinesses();
      setSelectedIds([]);
    } catch { showToast('Some deletions failed', 'error'); }
    finally { setBulkActionLoading(false); }
  };

  const handleExportCSV = () => {
    const rows = [
      ['ID','Business Name','Category','City','Phone','Address','Website','Status'],
      ...filteredAndSorted.map(b => [
        b.id, getBizName(b), b.category||'', b.city||'',
        getPhone(b), b.address||'', b.website||'', b.status||''
      ])
    ].map(r => r.join(',')).join('\n');

    const blob = new Blob([rows], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `businesses-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('CSV exported');
  };

  const toggleSelect = (id: number) =>
    setSelectedIds(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id]);

  const handleSelectAll = () =>
    setSelectedIds(selectedIds.length === paginated.length ? [] : paginated.map(b => b.id));

  const clearFilters = () => {
    setSearchTerm(''); setFilterCity(''); setFilterCategory(''); setFilterStatus('');
    setCurrentPage(1);
  };

  const hasFilters = searchTerm || filterCity || filterCategory || filterStatus;

  // ── Sorting indicator ────────────────────────────────────────
  const SortIcon = ({ field }: { field: SortField }) =>
    sortField === field
      ? <Icon d={sortOrder === 'asc' ? 'M12 5l7 7H5z' : 'M12 19l-7-7h14z'} size={10} color="#6366f1" />
      : <Icon d="M7 9l5-5 5 5M7 15l5 5 5-5" size={10} color="currentColor" />;

  // ─── Page renders ─────────────────────────────────────────────
  if (loading) return (
    <div className={`bl-loading-page${darkMode ? ' dark' : ''}`}>
      <style>{GLOBAL_CSS}</style>
      <div className="bl-spinner" />
      <p className="bl-loading-text">Loading businesses…</p>
    </div>
  );

  if (error) return (
    <div className={`bl-error-page${darkMode ? ' dark' : ''}`}>
      <style>{GLOBAL_CSS}</style>
      <div className="bl-error-box">
        <div className="bl-error-icon">
          <Icon d={IC.warn} size={22} color="#ef4444" />
        </div>
        <h2 className="bl-error-title">Connection Failed</h2>
        <p className="bl-error-msg">{error}</p>
        <button className="bl-btn bl-btn-primary" onClick={fetchBusinesses} style={{ width: '100%', justifyContent: 'center' }}>
          <Icon d={IC.refresh} size={14} color="white" /> Retry Connection
        </button>
      </div>
    </div>
  );

  return (
    <div className={`bl-page${darkMode ? ' dark' : ''}`}>
      <style>{GLOBAL_CSS}</style>

      {/* ── Toast ── */}
      {showToastState && (
        <div className="bl-toast">
          <span className="bl-toast-dot" style={{ background: toastType === 'error' ? '#ef4444' : '#10b981' }} />
          {toastMessage}
        </div>
      )}

      {/* ── Topbar ── */}
      <header className="bl-topbar">
        <div className="bl-topbar-left">
          <Link href="/" className="bl-brand">
            <div className="bl-brand-dot">
              <Icon d={IC.building} size={13} color="white" />
            </div>
            <span className="bl-brand-name">LeadMatrix</span>
          </Link>
          <div className="bl-divider" />
          <span className="bl-page-title">Businesses</span>
        </div>

        <div className="bl-search">
          <Icon d={IC.search} size={14} color="var(--text3)" />
          <input
            placeholder="Search name, city, category…"
            value={searchTerm}
            onChange={e => { setSearchTerm(e.target.value); setCurrentPage(1); }}
          />
          {searchTerm && (
            <button onClick={() => setSearchTerm('')} style={{ background:'none', border:'none', cursor:'pointer', display:'flex', padding:0 }}>
              <Icon d={IC.x} size={13} color="var(--text3)" />
            </button>
          )}
        </div>

        <div className="bl-topbar-right">
          <button className="bl-btn bl-btn-ghost bl-btn-icon" onClick={() => setDarkMode(d => !d)} title="Toggle theme">
            <Icon d={darkMode ? IC.sun : IC.moon} size={15} />
          </button>
          <button className="bl-btn bl-btn-ghost bl-btn-icon" onClick={fetchBusinesses} title="Refresh">
            <Icon d={IC.refresh} size={15} />
          </button>
          <button className="bl-btn bl-btn-ghost" onClick={handleExportCSV}>
            <Icon d={IC.download} size={14} /> Export
          </button>
          <Link href="/gmb-businesses" className="bl-btn bl-btn-primary">
            <Icon d={IC.plus} size={14} color="white" /> Add Business
          </Link>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="bl-main">

        {/* Heading */}
        <div className="bl-heading">
          <div>
            <h1>All Businesses</h1>
            <p>
              {businesses.length} total · {filteredAndSorted.length} shown
              {hasFilters && <> · <span style={{ color: 'var(--accent)', fontWeight: 600 }}>Filtered</span></>}
            </p>
          </div>
        </div>

        {/* Stat Cards */}
        <div className="bl-stats">
          {[
            { label: 'Total',      value: businesses.length,                                        color: '#6366f1', bg: '#eef2ff', icon: IC.building },
            { label: 'Active',     value: businesses.filter(b => b.status === 'active').length,     color: '#10b981', bg: '#d1fae5', icon: IC.check    },
            { label: 'Cities',     value: cities.length,                                            color: '#06b6d4', bg: '#cffafe', icon: IC.pin      },
            { label: 'Categories', value: categories.length,                                        color: '#f59e0b', bg: '#fef3c7', icon: IC.tag      },
          ].map((s, i) => (
            <div className="bl-stat" key={i}>
              <div className="bl-stat-icon" style={{ background: s.bg }}>
                <Icon d={s.icon} size={18} color={s.color} />
              </div>
              <div>
                <div className="bl-stat-label">{s.label}</div>
                <div className="bl-stat-val">{s.value}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Filter Bar */}
        <div className="bl-filterbar">
          <Icon d={IC.filter} size={14} color="var(--text3)" />

          <select value={filterCity} onChange={e => { setFilterCity(e.target.value); setCurrentPage(1); }}>
            <option value="">All Cities</option>
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          <select value={filterCategory} onChange={e => { setFilterCategory(e.target.value); setCurrentPage(1); }}>
            <option value="">All Categories</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          <select value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setCurrentPage(1); }}>
            <option value="">All Statuses</option>
            {statuses.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

          {hasFilters && (
            <button className="bl-btn bl-btn-ghost" onClick={clearFilters} style={{ height: 36 }}>
              <Icon d={IC.x} size={13} /> Clear filters
            </button>
          )}

          <div className="bl-filter-divider" />

          <div className="bl-view-toggle" style={{ marginLeft: 'auto' }}>
            <button className={`bl-view-btn${viewMode === 'table' ? ' active' : ''}`} onClick={() => setViewMode('table')} title="Table view">
              <Icon d={IC.table} size={14} />
            </button>
            <button className={`bl-view-btn${viewMode === 'grid' ? ' active' : ''}`} onClick={() => setViewMode('grid')} title="Grid view">
              <Icon d={IC.grid} size={14} />
            </button>
          </div>
        </div>

        {/* Bulk Action Bar */}
        {selectedIds.length > 0 && (
          <div className="bl-bulk-bar">
            <Icon d={IC.check} size={15} color="var(--accent)" />
            <span className="bl-bulk-count">{selectedIds.length} selected</span>
            <button className="bl-btn bl-btn-danger" onClick={handleBulkDelete} disabled={bulkActionLoading} style={{ height: 32, fontSize: '0.79rem' }}>
              <Icon d={IC.trash} size={13} />
              {bulkActionLoading ? 'Deleting…' : `Delete ${selectedIds.length}`}
            </button>
            <button className="bl-btn bl-btn-ghost" onClick={() => setSelectedIds([])} style={{ height: 32, fontSize: '0.79rem', marginLeft: 'auto' }}>
              <Icon d={IC.x} size={13} /> Deselect all
            </button>
          </div>
        )}

        {/* ── TABLE VIEW ── */}
        {viewMode === 'table' && (
          <div className="bl-table-wrap">
            <div style={{ overflowX: 'auto' }}>
              <table className="bl-table">
                <thead>
                  <tr>
                    <th style={{ width: 40 }}>
                      <input type="checkbox" className="bl-checkbox"
                        checked={selectedIds.length === paginated.length && paginated.length > 0}
                        onChange={handleSelectAll} />
                    </th>
                    <th>ID</th>
                    {(['name', 'category', 'city'] as SortField[]).map(f => (
                      <th key={f} className="sortable" onClick={() => handleSort(f)}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                          {f.charAt(0).toUpperCase() + f.slice(1)} <SortIcon field={f} />
                        </span>
                      </th>
                    ))}
                    <th>Phone</th>
                    <th className="sortable" onClick={() => handleSort('status')}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                        Status <SortIcon field="status" />
                      </span>
                    </th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {paginated.length === 0 ? (
                    <tr>
                      <td colSpan={8}>
                        <div className="bl-empty">
                          <div className="bl-empty-icon">
                            <Icon d={IC.building} size={22} color="var(--text3)" />
                          </div>
                          <div className="bl-empty-title">No businesses found</div>
                          <div className="bl-empty-sub">Try adjusting your search or filters</div>
                        </div>
                      </td>
                    </tr>
                  ) : paginated.map(b => (
                    <tr key={b.id} className={selectedIds.includes(b.id) ? 'selected' : ''}>
                      <td>
                        <input type="checkbox" className="bl-checkbox"
                          checked={selectedIds.includes(b.id)}
                          onChange={() => toggleSelect(b.id)} />
                      </td>
                      <td>
                        <span className="bl-badge bl-badge-id">#{b.id}</span>
                      </td>
                      <td>
                        <div className="bl-biz-cell">
                          <div className="bl-avatar" style={{ background: getAvatarColor(b.id) }}>
                            {getInitial(b)}
                          </div>
                          <div>
                            <div className="bl-biz-name">{getBizName(b)}</div>
                            {b.address && <div className="bl-biz-addr">{b.address}</div>}
                          </div>
                        </div>
                      </td>
                      <td>
                        {b.category
                          ? <span className="bl-badge bl-badge-cat">{b.category}</span>
                          : <span style={{ color: 'var(--text3)', fontSize: '0.8rem' }}>—</span>}
                      </td>
                      <td style={{ color: 'var(--text2)', fontSize: '0.82rem' }}>
                        {b.city || <span style={{ color: 'var(--text3)' }}>—</span>}
                      </td>
                      <td>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.81rem', color: 'var(--text2)' }}>
                          <Icon d={IC.phone} size={12} color="var(--text3)" />
                          {getPhone(b)}
                        </span>
                      </td>
                      <td>
                        <span className={`bl-badge ${b.status === 'active' ? 'bl-badge-active' : 'bl-badge-inactive'}`}>
                          {b.status || 'active'}
                        </span>
                      </td>
                      <td>
                        <div className="bl-action-wrap">
                          <Link href={`/analytics/${b.id}`} className="bl-action-btn view" title="Analytics">
                            <Icon d={IC.chart} size={14} />
                          </Link>
                          <Link href={`/edit-business/${b.id}`} className="bl-action-btn edit" title="Edit">
                            <Icon d={IC.edit} size={14} />
                          </Link>
                          <button className="bl-action-btn del" title="Delete"
                            onClick={() => handleDelete(b.id, getBizName(b))}>
                            <Icon d={IC.trash} size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── GRID VIEW ── */}
        {viewMode === 'grid' && (
          <div className="bl-grid">
            {paginated.length === 0 ? (
              <div style={{ gridColumn: '1/-1' }}>
                <div className="bl-empty" style={{ background: 'var(--surface)', border: '1.5px solid var(--border)', borderRadius: 14 }}>
                  <div className="bl-empty-icon"><Icon d={IC.building} size={22} color="var(--text3)" /></div>
                  <div className="bl-empty-title">No businesses found</div>
                  <div className="bl-empty-sub">Try adjusting your search or filters</div>
                </div>
              </div>
            ) : paginated.map(b => (
              <div key={b.id} className={`bl-card${selectedIds.includes(b.id) ? ' selected' : ''}`}>
                <div className="bl-card-head">
                  <div className="bl-card-avatar" style={{ background: getAvatarColor(b.id) }}>
                    {getInitial(b)}
                  </div>
                  <div className="bl-card-title">{getBizName(b)}</div>
                  <input type="checkbox" className="bl-checkbox"
                    checked={selectedIds.includes(b.id)}
                    onChange={() => toggleSelect(b.id)} />
                </div>

                <div className="bl-card-body">
                  {b.city && (
                    <div className="bl-card-row">
                      <Icon d={IC.pin} size={12} color="var(--text3)" />
                      <span>{b.city}</span>
                    </div>
                  )}
                  {b.category && (
                    <div className="bl-card-row">
                      <Icon d={IC.tag} size={12} color="var(--text3)" />
                      <span>{b.category}</span>
                    </div>
                  )}
                  <div className="bl-card-row">
                    <Icon d={IC.phone} size={12} color="var(--text3)" />
                    <span>{getPhone(b)}</span>
                  </div>
                  {b.website && (
                    <div className="bl-card-row">
                      <Icon d={IC.globe} size={12} color="var(--text3)" />
                      <a href={b.website} target="_blank" rel="noreferrer"
                        style={{ color: 'var(--accent)', textDecoration: 'none', fontSize: '0.78rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 180 }}>
                        {b.website.replace(/^https?:\/\//, '')}
                      </a>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 12 }}>
                  <span className="bl-badge bl-badge-id">#{b.id}</span>
                  <span className={`bl-badge ${b.status === 'active' ? 'bl-badge-active' : 'bl-badge-inactive'}`}>
                    {b.status || 'active'}
                  </span>
                </div>

                <div className="bl-card-footer">
                  <Link href={`/analytics/${b.id}`} className="bl-card-link"
                    style={{ background: '#eef2ff', color: '#4338ca', border: '1.5px solid #c7d2fe' }}>
                    <Icon d={IC.chart} size={12} /> Analytics
                  </Link>
                  <Link href={`/edit-business/${b.id}`} className="bl-card-link"
                    style={{ background: '#f0fdf4', color: '#15803d', border: '1.5px solid #bbf7d0' }}>
                    <Icon d={IC.edit} size={12} /> Edit
                  </Link>
                  <button className="bl-action-btn del" onClick={() => handleDelete(b.id, getBizName(b))} style={{ marginLeft: 'auto' }}>
                    <Icon d={IC.trash} size={13} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── Pagination ── */}
        {totalPages > 1 && (
          <div className="bl-pagination">
            <div className="bl-pagination-info">
              <label>
                Rows per page
                <select value={itemsPerPage} onChange={e => { setItemsPerPage(Number(e.target.value)); setCurrentPage(1); }}>
                  {[10, 25, 50, 100].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </label>
              <span className="bl-pagination-text">
                {(currentPage - 1) * itemsPerPage + 1}–{Math.min(currentPage * itemsPerPage, filteredAndSorted.length)} of {filteredAndSorted.length}
              </span>
            </div>

            <div className="bl-pagination-btns">
              <button className="bl-pg-btn" onClick={() => setCurrentPage(1)} disabled={currentPage === 1}>«</button>
              <button className="bl-pg-btn" onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}>‹</button>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let p: number;
                if (totalPages <= 5) p = i + 1;
                else if (currentPage <= 3) p = i + 1;
                else if (currentPage >= totalPages - 2) p = totalPages - 4 + i;
                else p = currentPage - 2 + i;
                return (
                  <button key={p} className={`bl-pg-btn${currentPage === p ? ' active' : ''}`} onClick={() => setCurrentPage(p)}>
                    {p}
                  </button>
                );
              })}
              <button className="bl-pg-btn" onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>›</button>
              <button className="bl-pg-btn" onClick={() => setCurrentPage(totalPages)} disabled={currentPage === totalPages}>»</button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
