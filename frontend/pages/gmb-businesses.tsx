'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Types ─────────────────────────────────────────────────────────────────────

interface FormData {
  name: string;
  address: string;
  phone: string;
  website: string;
  category: string;
  city: string;
  state: string;
  gmb_url: string;
}

type FieldErrors = Partial<Record<keyof FormData, string>>;
type Touched     = Partial<Record<keyof FormData, boolean>>;

const CATEGORIES = [
  { value: 'Hospital',    label: 'Hospital',          icon: '🏥' },
  { value: 'Clinic',      label: 'Clinic',            icon: '🩺' },
  { value: 'Dental',      label: 'Dental Clinic',     icon: '🦷' },
  { value: 'Pharmacy',    label: 'Pharmacy',          icon: '💊' },
  { value: 'Diagnostic',  label: 'Diagnostic Center', icon: '🔬' },
  { value: 'Gym',         label: 'Gym / Fitness',     icon: '💪' },
  { value: 'Salon',       label: 'Salon / Spa',       icon: '💇' },
  { value: 'Restaurant',  label: 'Restaurant',        icon: '🍽️' },
  { value: 'Retail',      label: 'Retail Store',      icon: '🛍️' },
  { value: 'Other',       label: 'Other',             icon: '📦' },
];

// ── CSS ───────────────────────────────────────────────────────────────────────

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #f8fafc;
    --surface:   #ffffff;
    --surface2:  #f1f5f9;
    --border:    #e2e8f0;
    --border2:   #f1f5f9;
    --text1:     #0f172a;
    --text2:     #475569;
    --text3:     #94a3b8;
    --accent:    #6366f1;
    --accentL:   #eef2ff;
    --accentD:   #4f46e5;
    --green:     #10b981;
    --greenL:    #f0fdf4;
    --greenB:    #bbf7d0;
    --red:       #ef4444;
    --redL:      #fef2f2;
    --amber:     #f59e0b;
    --r-sm:      6px;
    --r-md:      10px;
    --r-lg:      14px;
    --r-xl:      18px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
    --shadow-md: 0 4px 16px rgba(0,0,0,.06), 0 2px 6px rgba(0,0,0,.04);
    --shadow-lg: 0 12px 40px rgba(0,0,0,.08), 0 4px 12px rgba(0,0,0,.05);
  }

  html, body { font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: var(--text1); -webkit-font-smoothing: antialiased; }

  /* ── Page layout ── */
  .ab-page { min-height: 100vh; background: var(--bg); }

  /* ── Topbar ── */
  .ab-topbar {
    position: sticky; top: 0; z-index: 100;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 24px; height: 58px; gap: 12px;
  }
  .ab-topbar-left  { display: flex; align-items: center; gap: 10px; }
  .ab-topbar-right { display: flex; align-items: center; gap: 8px; }
  .ab-brand { display: flex; align-items: center; gap: 8px; text-decoration: none; }
  .ab-brand-dot {
    width: 28px; height: 28px; border-radius: 8px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    display: flex; align-items: center; justify-content: center;
  }
  .ab-brand-name { font-size: .88rem; font-weight: 700; color: var(--text1); }
  .ab-divider     { width: 1px; height: 20px; background: var(--border); }
  .ab-crumb       { font-size: .82rem; color: var(--text2); font-weight: 500; }
  .ab-crumb-cur   { font-size: .82rem; color: var(--text1); font-weight: 600; }

  /* ── Buttons ── */
  .ab-btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 0 14px; height: 34px; border-radius: var(--r-md);
    font-size: .79rem; font-weight: 600; cursor: pointer;
    border: 1.5px solid transparent; transition: all .15s;
    font-family: inherit; white-space: nowrap; text-decoration: none;
  }
  .ab-btn-ghost   { background: transparent; border-color: var(--border); color: var(--text2); }
  .ab-btn-ghost:hover { background: var(--bg); color: var(--text1); }
  .ab-btn-primary {
    background: var(--accent); color: white; border-color: var(--accent);
    box-shadow: 0 2px 8px rgba(99,102,241,.25);
  }
  .ab-btn-primary:hover { background: var(--accentD); border-color: var(--accentD); }
  .ab-btn-primary:disabled { background: #c7d2fe; border-color: #c7d2fe; cursor: not-allowed; box-shadow: none; }

  /* ── Main grid ── */
  .ab-main {
    max-width: 1140px; margin: 0 auto;
    padding: 32px 24px 64px;
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 24px;
    align-items: start;
  }
  @media (max-width: 900px) {
    .ab-main { grid-template-columns: 1fr; padding: 16px 14px 48px; }
    .ab-sidebar { order: -1; }
  }

  /* ── Page title area ── */
  .ab-page-title-row { margin-bottom: 24px; }
  .ab-page-title { font-size: 1.35rem; font-weight: 800; color: var(--text1); letter-spacing: -.3px; }
  .ab-page-sub   { font-size: .82rem; color: var(--text2); margin-top: 4px; }

  /* ── Card ── */
  .ab-card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--r-xl);
    box-shadow: var(--shadow-sm);
  }
  .ab-card-header {
    padding: 20px 24px 0;
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 20px;
  }
  .ab-card-header-icon {
    width: 36px; height: 36px; border-radius: var(--r-md);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .ab-card-header-title { font-size: .9rem; font-weight: 700; color: var(--text1); }
  .ab-card-header-sub   { font-size: .75rem; color: var(--text2); margin-top: 1px; }
  .ab-card-body { padding: 0 24px 24px; }

  /* ── Section divider inside card ── */
  .ab-section-label {
    font-size: .67rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .7px; color: var(--text3);
    margin-bottom: 14px; margin-top: 20px;
    display: flex; align-items: center; gap: 8px;
  }
  .ab-section-label::before {
    content: ''; flex: none; width: 16px; height: 1.5px;
    background: var(--border);
  }
  .ab-section-label:first-child { margin-top: 0; }

  /* ── Form fields ── */
  .ab-field { margin-bottom: 16px; }
  .ab-field:last-child { margin-bottom: 0; }
  .ab-field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  @media (max-width: 560px) { .ab-field-row { grid-template-columns: 1fr; } }

  .ab-label {
    display: block; font-size: .78rem; font-weight: 600;
    color: var(--text2); margin-bottom: 6px;
  }
  .ab-req { color: var(--red); margin-left: 2px; }

  .ab-input, .ab-select {
    width: 100%; height: 40px; padding: 0 12px;
    border: 1.5px solid var(--border); border-radius: var(--r-md);
    font-size: .84rem; color: var(--text1); background: var(--surface);
    font-family: inherit; outline: none;
    transition: border-color .15s, box-shadow .15s;
  }
  .ab-input::placeholder { color: var(--text3); }
  .ab-input:focus, .ab-select:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(99,102,241,.12);
  }
  .ab-input.error { border-color: var(--red); }
  .ab-input.error:focus { box-shadow: 0 0 0 3px rgba(239,68,68,.12); }
  .ab-input-wrap { position: relative; }
  .ab-input-icon {
    position: absolute; left: 11px; top: 50%; transform: translateY(-50%);
    color: var(--text3); pointer-events: none;
    display: flex; align-items: center;
  }
  .ab-input-wrap .ab-input { padding-left: 34px; }

  .ab-error-msg {
    font-size: .72rem; color: var(--red); font-weight: 500;
    margin-top: 5px; display: flex; align-items: center; gap: 4px;
  }

  /* ── Category grid ── */
  .ab-cat-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 8px;
  }
  .ab-cat-btn {
    display: flex; flex-direction: column; align-items: center; gap: 4px;
    padding: 12px 8px; border-radius: var(--r-lg);
    border: 1.5px solid var(--border); background: var(--surface);
    cursor: pointer; transition: all .15s; font-family: inherit;
    font-size: .73rem; font-weight: 500; color: var(--text2);
    text-align: center; line-height: 1.3;
  }
  .ab-cat-btn:hover { border-color: var(--accent); color: var(--accent); background: var(--accentL); }
  .ab-cat-btn.active {
    border-color: var(--accent); color: var(--accent);
    background: var(--accentL); font-weight: 700;
    box-shadow: 0 0 0 3px rgba(99,102,241,.1);
  }
  .ab-cat-btn-icon { font-size: 1.3rem; line-height: 1; }

  /* ── Progress bar ── */
  .ab-progress-wrap { margin-top: 18px; }
  .ab-progress-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
  .ab-progress-label { font-size: .72rem; font-weight: 600; color: var(--text3); }
  .ab-progress-pct   { font-size: .72rem; font-weight: 700; color: var(--text1); }
  .ab-progress-track {
    width: 100%; height: 6px; border-radius: 99px;
    background: var(--border2); overflow: hidden;
  }
  .ab-progress-fill {
    height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, var(--accent), #8b5cf6);
    transition: width .35s cubic-bezier(.4,0,.2,1);
  }

  /* ── Sidebar ── */
  .ab-sidebar { display: flex; flex-direction: column; gap: 16px; }

  .ab-checklist-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 0; border-bottom: 1px solid var(--border2);
    font-size: .8rem; color: var(--text2);
  }
  .ab-checklist-item:last-child { border-bottom: none; padding-bottom: 0; }
  .ab-check-icon {
    width: 22px; height: 22px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: .7rem; font-weight: 700; transition: all .2s;
  }
  .ab-check-icon.done { background: var(--greenL); color: var(--green); border: 1.5px solid var(--greenB); }
  .ab-check-icon.todo { background: var(--bg); color: var(--text3); border: 1.5px solid var(--border); }
  .ab-checklist-text { font-weight: 500; }
  .ab-checklist-text.done { color: var(--text1); }

  /* ── Info tile in sidebar ── */
  .ab-info-tile {
    padding: 14px 16px; background: var(--accentL);
    border: 1.5px solid #c7d2fe; border-radius: var(--r-lg);
  }
  .ab-info-tile-title { font-size: .78rem; font-weight: 700; color: var(--accentD); margin-bottom: 6px; }
  .ab-info-tile-text  { font-size: .74rem; color: #4338ca; line-height: 1.55; }

  /* ── Submit section ── */
  .ab-submit-wrap {
    padding: 20px 24px; border-top: 1px solid var(--border2);
    display: flex; flex-direction: column; gap: 10px;
  }
  .ab-submit-btn {
    width: 100%; height: 44px;
    background: linear-gradient(135deg, var(--accent), #8b5cf6);
    color: white; border: none; border-radius: var(--r-lg);
    font-size: .9rem; font-weight: 700; cursor: pointer;
    font-family: inherit; transition: all .2s;
    display: flex; align-items: center; justify-content: center; gap: 8px;
    box-shadow: 0 4px 14px rgba(99,102,241,.3);
  }
  .ab-submit-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(99,102,241,.35);
  }
  .ab-submit-btn:active:not(:disabled) { transform: translateY(0); }
  .ab-submit-btn:disabled {
    background: #c7d2fe; cursor: not-allowed;
    box-shadow: none; transform: none;
  }
  .ab-submit-hint { font-size: .72rem; color: var(--text3); text-align: center; }

  /* ── Spinner ── */
  @keyframes spin { to { transform: rotate(360deg); } }
  .ab-spinner {
    width: 16px; height: 16px;
    border: 2px solid rgba(255,255,255,.35);
    border-top-color: white; border-radius: 50%;
    animation: spin .7s linear infinite; flex-shrink: 0;
  }

  /* ── Success overlay ── */
  .ab-success-overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 9999; padding: 24px; backdrop-filter: blur(4px);
  }
  @keyframes popIn {
    0%   { transform: scale(.85); opacity: 0; }
    70%  { transform: scale(1.03); }
    100% { transform: scale(1); opacity: 1; }
  }
  .ab-success-card {
    background: var(--surface); border-radius: 20px;
    padding: 48px 40px; max-width: 420px; width: 100%;
    text-align: center; box-shadow: var(--shadow-lg);
    border: 1.5px solid var(--border);
    animation: popIn .4s cubic-bezier(.34,1.56,.64,1);
  }
  .ab-success-icon {
    width: 80px; height: 80px; border-radius: 50%;
    background: linear-gradient(135deg, var(--green), #059669);
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 24px; font-size: 2rem;
    box-shadow: 0 8px 24px rgba(16,185,129,.35);
  }
  .ab-success-title { font-size: 1.3rem; font-weight: 800; color: var(--text1); margin-bottom: 10px; }
  .ab-success-sub   { font-size: .85rem; color: var(--text2); line-height: 1.6; }
  .ab-success-biz   { display: inline-block; margin-top: 14px; padding: 6px 14px; background: var(--accentL); border-radius: 99px; font-size: .8rem; font-weight: 700; color: var(--accent); }
  .ab-success-redirect { margin-top: 24px; font-size: .75rem; color: var(--text3); }

  /* ── Banner alert ── */
  .ab-alert {
    padding: 12px 16px; border-radius: var(--r-md);
    font-size: .8rem; font-weight: 500; display: flex; align-items: center; gap: 8px;
    margin-bottom: 16px;
  }
  .ab-alert-error { background: var(--redL); border: 1.5px solid #fecdd3; color: #be123c; }
`;

// ── SVG Icons ─────────────────────────────────────────────────────────────────

const Icon = ({ d, size = 15, color = 'currentColor' }: { d: string; size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

const IC = {
  back:   'M19 12H5M12 5l-7 7 7 7',
  biz:    'M3 21h18M3 7v1a3 3 0 0 0 6 0V7m0 1a3 3 0 0 0 6 0V7m0 1a3 3 0 0 0 6 0V7H3l2-4h14l2 4zM5 21V10.85M19 21V10.85',
  loc:    'M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z',
  phone:  'M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z',
  globe:  'M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 0c-2.5 2.5-4 5.5-4 10s1.5 7.5 4 10m0-20c2.5 2.5 4 5.5 4 10s-1.5 7.5-4 10M2 12h20',
  gmb:    'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z',
  link:   'M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71',
  tag:    'M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82zM7 7h.01',
  trend:  'M22 7l-9.2 9.2-4.8-4.8L2 18',
  check:  'M20 6L9 17l-5-5',
  warn:   'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01',
  city:   'M3 21h18M9 8h1m-1 4h1m4-4h1m-1 4h1M9 21v-5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v5M5 21V7l7-4 7 4v14',
  info:   'M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 4v4m0 4h.01',
};

// ── Validation ────────────────────────────────────────────────────────────────

function validateField(name: keyof FormData, value: string): string {
  switch (name) {
    case 'name':
      if (!value.trim()) return 'Business name is required';
      if (value.trim().length < 3) return 'Name must be at least 3 characters';
      break;
    case 'phone':
      if (value && !/^[+]?[\d\s\-()+]+$/.test(value)) return 'Invalid phone number format';
      break;
    case 'website':
    case 'gmb_url':
      if (value && !/^https?:\/\/.+/.test(value)) return 'Must start with https:// or http://';
      break;
    case 'city':
      if (value && value.trim().length < 2) return 'Enter a valid city name';
      break;
  }
  return '';
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function AddGMBBusiness() {
  const router = useRouter();

  const [formData, setFormData] = useState<FormData>({
    name: '', address: '', phone: '', website: '',
    category: '', city: '', state: '', gmb_url: '',
  });
  const [errors,   setErrors]   = useState<FieldErrors>({});
  const [touched,  setTouched]  = useState<Touched>({});
  const [loading,  setLoading]  = useState(false);
  const [apiError, setApiError] = useState('');
  const [success,  setSuccess]  = useState<{ name: string } | null>(null);
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => { nameRef.current?.focus(); }, []);

  const progress = Math.round(
    (Object.values(formData).filter(v => v.trim() !== '').length / Object.keys(formData).length) * 100
  );

  const checks = [
    { label: 'Business name',       done: formData.name.trim().length >= 3 },
    { label: 'Category selected',   done: !!formData.category },
    { label: 'Location added',      done: !!(formData.city || formData.address) },
    { label: 'Contact info',        done: !!(formData.phone || formData.website) },
    { label: 'GMB URL (optional)',  done: !!formData.gmb_url },
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setApiError('');
    if (touched[name as keyof FormData]) {
      setErrors(prev => ({ ...prev, [name]: validateField(name as keyof FormData, value) }));
    }
  };

  const handleBlur = (name: keyof FormData) => {
    setTouched(prev => ({ ...prev, [name]: true }));
    setErrors(prev => ({ ...prev, [name]: validateField(name, formData[name]) }));
  };

  const handleCategorySelect = (val: string) => {
    setFormData(prev => ({ ...prev, category: val }));
    setTouched(prev => ({ ...prev, category: true }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const allTouched: Touched = {};
    const allErrors: FieldErrors = {};
    (Object.keys(formData) as (keyof FormData)[]).forEach(k => {
      allTouched[k] = true;
      allErrors[k] = validateField(k, formData[k]);
    });
    if (!formData.category) allErrors.category = 'Please select a category';
    setTouched(allTouched);
    setErrors(allErrors);
    if (Object.values(allErrors).some(e => e !== '')) return;

    setLoading(true);
    setApiError('');
    try {
      const res = await fetch(`${API_BASE}/api/businesses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      if (data.success) {
        setSuccess({ name: formData.name });
        setTimeout(() => router.push('/businesses-list'), 2500);
      } else {
        setApiError(data.detail || data.message || 'Failed to add business. Please try again.');
      }
    } catch (err) {
      console.error(err);
      setApiError('Cannot reach backend. Make sure the server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const isSubmitDisabled = loading || !formData.name.trim() || !formData.category || Object.values(errors).some(e => !!e);

  const Field = ({
    name, label, required, type = 'text', placeholder, iconD, hint,
  }: {
    name: keyof FormData; label: string; required?: boolean;
    type?: string; placeholder?: string; iconD?: string; hint?: string;
  }) => (
    <div className="ab-field">
      <label className="ab-label" htmlFor={name}>
        {label}{required && <span className="ab-req">*</span>}
      </label>
      <div className={iconD ? 'ab-input-wrap' : undefined}>
        {iconD && <span className="ab-input-icon"><Icon d={iconD} size={14} /></span>}
        <input
          ref={name === 'name' ? nameRef : undefined}
          id={name}
          type={type}
          name={name}
          value={formData[name]}
          onChange={handleChange}
          onBlur={() => handleBlur(name)}
          placeholder={placeholder}
          className={`ab-input${errors[name] && touched[name] ? ' error' : ''}`}
          autoComplete="off"
        />
      </div>
      {errors[name] && touched[name] && (
        <p className="ab-error-msg">
          <Icon d={IC.warn} size={12} color="#ef4444" /> {errors[name]}
        </p>
      )}
      {hint && !errors[name] && (
        <p style={{ fontSize: '.71rem', color: 'var(--text3)', marginTop: 4 }}>{hint}</p>
      )}
    </div>
  );

  return (
    <div className="ab-page">
      <style>{CSS}</style>

      {success && (
        <div className="ab-success-overlay">
          <div className="ab-success-card">
            <div className="ab-success-icon">✓</div>
            <h2 className="ab-success-title">Business Added!</h2>
            <p className="ab-success-sub">Your listing has been created and is ready to track.</p>
            <span className="ab-success-biz">{success.name}</span>
            <p className="ab-success-redirect">Redirecting to business list…</p>
          </div>
        </div>
      )}

      <header className="ab-topbar">
        <div className="ab-topbar-left">
          <Link href="/" className="ab-brand">
            <div className="ab-brand-dot">
              <Icon d={IC.trend} size={13} color="white" />
            </div>
            <span className="ab-brand-name">LeadMatrix</span>
          </Link>
          <div className="ab-divider" />
          <Link href="/businesses-list" className="ab-crumb" style={{ textDecoration: 'none' }}>Businesses</Link>
          <Icon d="M9 18l6-6-6-6" size={13} color="var(--text3)" />
          <span className="ab-crumb-cur">Add Business</span>
        </div>
        <div className="ab-topbar-right">
          <Link href="/businesses-list" className="ab-btn ab-btn-ghost">
            <Icon d={IC.back} size={13} /> Back
          </Link>
        </div>
      </header>

      <div className="ab-main">
        <div>
          <div className="ab-page-title-row">
            <h1 className="ab-page-title">Add New Business</h1>
            <p className="ab-page-sub">Fill in your Google Business Profile details to start tracking analytics.</p>
          </div>

          {apiError && (
            <div className="ab-alert ab-alert-error">
              <Icon d={IC.warn} size={14} color="#be123c" />
              {apiError}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <div className="ab-card" style={{ marginBottom: 16 }}>
              <div className="ab-card-header">
                <div className="ab-card-header-icon" style={{ background: '#eef2ff' }}>
                  <Icon d={IC.biz} size={16} color="#6366f1" />
                </div>
                <div>
                  <div className="ab-card-header-title">Business Identity</div>
                  <div className="ab-card-header-sub">Name and category</div>
                </div>
              </div>
              <div className="ab-card-body">
                <Field
                  name="name" label="Business Name" required
                  placeholder="Dr. Prashansa Raut Clinic"
                  iconD={IC.biz}
                />

                <div className="ab-section-label">Category</div>
                <div className="ab-cat-grid">
                  {CATEGORIES.map(c => (
                    <button
                      key={c.value}
                      type="button"
                      className={`ab-cat-btn${formData.category === c.value ? ' active' : ''}`}
                      onClick={() => handleCategorySelect(c.value)}
                    >
                      <span className="ab-cat-btn-icon">{c.icon}</span>
                      {c.label}
                    </button>
                  ))}
                </div>
                {errors.category && touched.category && (
                  <p className="ab-error-msg" style={{ marginTop: 8 }}>
                    <Icon d={IC.warn} size={12} color="#ef4444" /> {errors.category}
                  </p>
                )}
              </div>
            </div>

            <div className="ab-card" style={{ marginBottom: 16 }}>
              <div className="ab-card-header">
                <div className="ab-card-header-icon" style={{ background: '#fef3c7' }}>
                  <Icon d={IC.loc} size={16} color="#f59e0b" />
                </div>
                <div>
                  <div className="ab-card-header-title">Location</div>
                  <div className="ab-card-header-sub">Address and city details</div>
                </div>
              </div>
              <div className="ab-card-body">
                <Field
                  name="address" label="Full Address"
                  placeholder="123 Main Street, Andheri West"
                  iconD={IC.loc}
                />
                <div className="ab-field-row">
                  <Field name="city"  label="City"  placeholder="Mumbai" iconD={IC.city} />
                  <Field name="state" label="State" placeholder="Maharashtra" />
                </div>
              </div>
            </div>

            <div className="ab-card" style={{ marginBottom: 16 }}>
              <div className="ab-card-header">
                <div className="ab-card-header-icon" style={{ background: '#f0fdf4' }}>
                  <Icon d={IC.phone} size={16} color="#10b981" />
                </div>
                <div>
                  <div className="ab-card-header-title">Contact &amp; Online Presence</div>
                  <div className="ab-card-header-sub">Phone, website, and GMB link</div>
                </div>
              </div>
              <div className="ab-card-body">
                <div className="ab-field-row">
                  <Field name="phone"   label="Phone Number" type="tel" placeholder="+91 98765 43210" iconD={IC.phone} />
                  <Field name="website" label="Website URL"  type="url" placeholder="https://example.com" iconD={IC.globe} />
                </div>
                <Field
                  name="gmb_url" label="Google Business Profile URL" type="url"
                  placeholder="https://g.page/your-business-name"
                  iconD={IC.link}
                  hint="Paste the URL from your Google Business Profile dashboard"
                />
              </div>
            </div>

            <div className="ab-card">
              <div style={{ padding: '20px 24px 0' }}>
                <div className="ab-progress-wrap">
                  <div className="ab-progress-row">
                    <span className="ab-progress-label">Profile Completeness</span>
                    <span className="ab-progress-pct">{progress}%</span>
                  </div>
                  <div className="ab-progress-track">
                    <div className="ab-progress-fill" style={{ width: `${progress}%` }} />
                  </div>
                </div>
              </div>
              <div className="ab-submit-wrap">
                <button type="submit" className="ab-submit-btn" disabled={isSubmitDisabled}>
                  {loading ? (
                    <><div className="ab-spinner" /> Adding Business…</>
                  ) : (
                    <><Icon d={IC.check} size={16} color="white" /> Add Business</>
                  )}
                </button>
                <p className="ab-submit-hint">
                  You can edit all details after adding the business.
                </p>
              </div>
            </div>
          </form>
        </div>

        <aside className="ab-sidebar">
          <div className="ab-card">
            <div className="ab-card-header">
              <div className="ab-card-header-icon" style={{ background: '#f0fdf4' }}>
                <Icon d={IC.check} size={15} color="#10b981" />
              </div>
              <div>
                <div className="ab-card-header-title">Completion Checklist</div>
                <div className="ab-card-header-sub">Fill in key details</div>
              </div>
            </div>
            <div className="ab-card-body">
              {checks.map((c, i) => (
                <div key={i} className="ab-checklist-item">
                  <div className={`ab-check-icon ${c.done ? 'done' : 'todo'}`}>
                    {c.done ? '✓' : i + 1}
                  </div>
                  <span className={`ab-checklist-text${c.done ? ' done' : ''}`}>{c.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="ab-info-tile">
            <div className="ab-info-tile-title">💡 Pro Tip</div>
            <p className="ab-info-tile-text">
              Adding your GMB URL lets LeadMatrix sync live data automatically — including views, calls, directions, and keyword searches.
            </p>
          </div>

          <div className="ab-card">
            <div className="ab-card-header">
              <div className="ab-card-header-icon" style={{ background: '#f8fafc' }}>
                <Icon d={IC.link} size={15} color="#6366f1" />
              </div>
              <div>
                <div className="ab-card-header-title">Quick Links</div>
              </div>
            </div>
            <div className="ab-card-body" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <a
                href="https://business.google.com"
                target="_blank" rel="noopener noreferrer"
                className="ab-btn ab-btn-ghost"
                style={{ justifyContent: 'center', height: 36 }}
              >
                <Icon d={IC.globe} size={13} /> Google Business
              </a>
              <Link href="/businesses-list" className="ab-btn ab-btn-ghost" style={{ justifyContent: 'center', height: 36 }}>
                <Icon d={IC.biz} size={13} /> View All Businesses
              </Link>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
