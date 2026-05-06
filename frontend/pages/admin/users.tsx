'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import API_BASE from '../../lib/api';

const ADMIN_EMAILS = ['abhishek@theinternetcompany.in', 'zishan@theinternetcompany.in'];

interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string | null;
  last_login: string | null;
}

export default function AdminUsers() {
  const router = useRouter();

  const [users,       setUsers]       = useState<User[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState('');
  const [myEmail,     setMyEmail]     = useState('');

  const [newEmail,    setNewEmail]    = useState('');
  const [newName,     setNewName]     = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [addError,    setAddError]    = useState('');
  const [addSuccess,  setAddSuccess]  = useState('');
  const [adding,      setAdding]      = useState(false);

  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [deleting,     setDeleting]     = useState(false);
  const [deleteError,  setDeleteError]  = useState('');

  const token = () => (typeof window !== 'undefined' ? localStorage.getItem('lm_token') : null);

  useEffect(() => {
    const t = token();
    if (!t) { router.replace('/login'); return; }

    fetch(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${t}` },
    })
      .then((r) => r.json())
      .then((data) => {
        if (!ADMIN_EMAILS.includes(data.email)) {
          router.replace('/dashboard');
          return;
        }
        setMyEmail(data.email);
        loadUsers(t);
      })
      .catch(() => router.replace('/login'));
  }, []);

  async function loadUsers(t: string) {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/admin/users`, {
        headers: { Authorization: `Bearer ${t}` },
      });
      if (!res.ok) throw new Error('Failed to load users');
      setUsers(await res.json());
    } catch {
      setError('Could not load users. Please refresh.');
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setAddError('');
    setAddSuccess('');
    setAdding(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token()}`,
        },
        body: JSON.stringify({ email: newEmail, full_name: newName || null, password: newPassword }),
      });
      const data = await res.json();
      if (!res.ok) { setAddError(data.detail || 'Failed to add user'); return; }
      setAddSuccess(`${data.email} added successfully`);
      setNewEmail(''); setNewName(''); setNewPassword('');
      loadUsers(token()!);
    } catch {
      setAddError('Cannot reach the server. Please try again.');
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    setDeleteError('');
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${deleteTarget.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token()}` },
      });
      const data = await res.json();
      if (!res.ok) { setDeleteError(data.detail || 'Failed to delete user'); return; }
      setDeleteTarget(null);
      loadUsers(token()!);
    } catch {
      setDeleteError('Cannot reach the server. Please try again.');
    } finally {
      setDeleting(false);
    }
  }

  function fmt(iso: string | null) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  return (
    <div style={s.page}>
      <div style={s.container}>

        {/* Header */}
        <div style={s.header}>
          <div>
            <div style={s.logo}>LM</div>
          </div>
          <div style={s.headerText}>
            <h1 style={s.title}>User Management</h1>
            <p style={s.sub}>Signed in as <strong>{myEmail}</strong></p>
          </div>
          <Link href="/dashboard" style={s.backLink}>← Dashboard</Link>
        </div>

        {/* Add User */}
        <div style={s.card}>
          <h2 style={s.sectionTitle}>Add User</h2>
          <form onSubmit={handleAdd} style={s.form}>
            <div style={s.row}>
              <div style={s.field}>
                <label style={s.label}>Email</label>
                <input
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="name@theinternetcompany.in"
                  required
                  style={s.input}
                />
              </div>
              <div style={s.field}>
                <label style={s.label}>Full Name</label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Optional"
                  style={s.input}
                />
              </div>
              <div style={s.field}>
                <label style={s.label}>Password</label>
                <input
                  type="text"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Min. 8 characters"
                  required
                  style={s.input}
                />
              </div>
              <button type="submit" disabled={adding} style={s.addBtn}>
                {adding ? 'Adding…' : 'Add User'}
              </button>
            </div>
            {addError   && <div style={s.errorBox}>{addError}</div>}
            {addSuccess && <div style={s.successBox}>{addSuccess}</div>}
          </form>
        </div>

        {/* Users Table */}
        <div style={s.card}>
          <h2 style={s.sectionTitle}>All Users ({users.length})</h2>
          {loading && <p style={s.muted}>Loading…</p>}
          {error   && <div style={s.errorBox}>{error}</div>}
          {!loading && !error && (
            <div style={s.tableWrap}>
              <table style={s.table}>
                <thead>
                  <tr>
                    <th style={s.th}>Email</th>
                    <th style={s.th}>Name</th>
                    <th style={s.th}>Status</th>
                    <th style={s.th}>Joined</th>
                    <th style={s.th}>Last Login</th>
                    <th style={s.th}></th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} style={s.tr}>
                      <td style={s.td}>
                        {u.email}
                        {ADMIN_EMAILS.includes(u.email) && (
                          <span style={s.adminBadge}>admin</span>
                        )}
                      </td>
                      <td style={s.td}>{u.full_name || <span style={s.muted}>—</span>}</td>
                      <td style={s.td}>
                        <span style={u.is_active ? s.badgeActive : s.badgeInactive}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td style={s.td}>{fmt(u.created_at)}</td>
                      <td style={s.td}>{fmt(u.last_login)}</td>
                      <td style={s.td}>
                        {u.email !== myEmail && (
                          <button
                            onClick={() => { setDeleteTarget(u); setDeleteError(''); }}
                            style={s.deleteBtn}
                          >
                            Remove
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div style={s.overlay}>
          <div style={s.modal}>
            <h3 style={s.modalTitle}>Remove User</h3>
            <p style={s.modalBody}>
              Are you sure you want to permanently delete <strong>{deleteTarget.email}</strong>?
              This cannot be undone.
            </p>
            {deleteError && <div style={s.errorBox}>{deleteError}</div>}
            <div style={s.modalActions}>
              <button
                onClick={() => setDeleteTarget(null)}
                disabled={deleting}
                style={s.cancelBtn}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                style={s.confirmDeleteBtn}
              >
                {deleting ? 'Removing…' : 'Yes, Remove'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    background: '#f1f5f9',
    fontFamily: "'Inter', sans-serif",
    padding: '32px 16px',
  },
  container: {
    maxWidth: 960,
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
    gap: 24,
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
  },
  logo: {
    width: 44,
    height: 44,
    borderRadius: 12,
    background: '#6366f1',
    color: '#fff',
    fontWeight: 800,
    fontSize: 16,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  headerText: {
    flex: 1,
  },
  title: {
    margin: 0,
    fontSize: 22,
    fontWeight: 700,
    color: '#0f172a',
  },
  sub: {
    margin: '2px 0 0',
    fontSize: 13,
    color: '#64748b',
  },
  backLink: {
    fontSize: 13,
    color: '#6366f1',
    textDecoration: 'none',
    whiteSpace: 'nowrap',
  },
  card: {
    background: '#fff',
    borderRadius: 14,
    padding: '24px 28px',
    boxShadow: '0 2px 12px rgba(0,0,0,0.07)',
  },
  sectionTitle: {
    margin: '0 0 16px',
    fontSize: 16,
    fontWeight: 700,
    color: '#0f172a',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  row: {
    display: 'flex',
    gap: 12,
    alignItems: 'flex-end',
    flexWrap: 'wrap',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: 5,
    flex: 1,
    minWidth: 160,
  },
  label: {
    fontSize: 12,
    fontWeight: 600,
    color: '#374151',
  },
  input: {
    padding: '9px 11px',
    borderRadius: 8,
    border: '1.5px solid #e2e8f0',
    fontSize: 14,
    color: '#0f172a',
    outline: 'none',
  },
  addBtn: {
    padding: '9px 20px',
    borderRadius: 8,
    background: '#6366f1',
    color: '#fff',
    fontWeight: 700,
    fontSize: 14,
    border: 'none',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    alignSelf: 'flex-end',
  },
  errorBox: {
    background: '#fef2f2',
    color: '#dc2626',
    border: '1px solid #fecaca',
    borderRadius: 8,
    padding: '9px 12px',
    fontSize: 13,
  },
  successBox: {
    background: '#f0fdf4',
    color: '#16a34a',
    border: '1px solid #bbf7d0',
    borderRadius: 8,
    padding: '9px 12px',
    fontSize: 13,
  },
  tableWrap: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 14,
  },
  th: {
    textAlign: 'left',
    padding: '8px 12px',
    fontSize: 12,
    fontWeight: 600,
    color: '#64748b',
    borderBottom: '1.5px solid #e2e8f0',
    whiteSpace: 'nowrap',
  },
  tr: {
    borderBottom: '1px solid #f1f5f9',
  },
  td: {
    padding: '12px 12px',
    color: '#0f172a',
    verticalAlign: 'middle',
  },
  muted: {
    color: '#94a3b8',
    fontSize: 13,
  },
  adminBadge: {
    marginLeft: 8,
    padding: '2px 7px',
    borderRadius: 99,
    background: '#eef2ff',
    color: '#6366f1',
    fontSize: 11,
    fontWeight: 700,
  },
  badgeActive: {
    padding: '3px 9px',
    borderRadius: 99,
    background: '#f0fdf4',
    color: '#16a34a',
    fontSize: 12,
    fontWeight: 600,
  },
  badgeInactive: {
    padding: '3px 9px',
    borderRadius: 99,
    background: '#fef2f2',
    color: '#dc2626',
    fontSize: 12,
    fontWeight: 600,
  },
  deleteBtn: {
    padding: '5px 12px',
    borderRadius: 6,
    background: '#fff',
    color: '#dc2626',
    border: '1.5px solid #fecaca',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
  },
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.4)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
  },
  modal: {
    background: '#fff',
    borderRadius: 14,
    padding: '28px 28px 24px',
    width: '100%',
    maxWidth: 400,
    boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
  },
  modalTitle: {
    margin: '0 0 8px',
    fontSize: 17,
    fontWeight: 700,
    color: '#0f172a',
  },
  modalBody: {
    margin: '0 0 20px',
    fontSize: 14,
    color: '#475569',
    lineHeight: 1.6,
  },
  modalActions: {
    display: 'flex',
    gap: 10,
    justifyContent: 'flex-end',
    marginTop: 16,
  },
  cancelBtn: {
    padding: '9px 18px',
    borderRadius: 8,
    background: '#f1f5f9',
    color: '#374151',
    fontWeight: 600,
    fontSize: 14,
    border: 'none',
    cursor: 'pointer',
  },
  confirmDeleteBtn: {
    padding: '9px 18px',
    borderRadius: 8,
    background: '#dc2626',
    color: '#fff',
    fontWeight: 700,
    fontSize: 14,
    border: 'none',
    cursor: 'pointer',
  },
};
