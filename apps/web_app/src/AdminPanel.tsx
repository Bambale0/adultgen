import { Activity, KeyRound, RadioTower, ShieldAlert } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import {
  applyAdminPublicationAction, createAdminWalletAdjustment, fetchAdminAuditEvents,
  fetchAdminGenerations, fetchAdminPaymentOrders, fetchAdminPublications, fetchAdminUsers,
  updateAdminUserCapabilities, type AdminAuditEvent, type AdminGeneration,
  type AdminPaymentOrder, type AdminPublication, type AdminUser,
} from './adminApi';

const ADMIN_TOKEN_STORAGE_KEY = 'adultgen_admin_token';
type AdminTab = 'overview' | 'users' | 'generations' | 'publications' | 'payments' | 'wallet' | 'audit';
const tabs: AdminTab[] = ['overview', 'users', 'generations', 'publications', 'payments', 'wallet', 'audit'];

export function AdminPanel() {
  const [token, setToken] = useState(() => window.localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) || '');
  const [draft, setDraft] = useState('');
  const [tab, setTab] = useState<AdminTab>('overview');
  const [message, setMessage] = useState('');
  const saveToken = () => { window.localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, draft); setToken(draft); };
  const clearToken = () => { window.localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY); setToken(''); };

  if (!token) return <main className="admin-shell admin-lock"><section className="admin-main-panel"><div className="gate-icon"><KeyRound /></div><p className="eyebrow">ADULTGEN ADMIN</p><h1>Control Room</h1><p>Нужен ADMIN_API_TOKEN</p><label>Admin token<input type="password" value={draft} onChange={(event) => setDraft(event.target.value)} autoComplete="off" /></label><button className="primary-action" disabled={!draft} onClick={saveToken}>Unlock console</button></section></main>;

  return <main className="admin-shell"><aside className="admin-sidebar"><p className="eyebrow">ADULTGEN / OPS</p><h1>Control Room</h1><nav>{tabs.map((item) => <button key={item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)}>{item}</button>)}</nav><button className="secondary-action" onClick={clearToken}>Lock console</button></aside><section className="admin-main-panel"><header><div><p className="eyebrow">PROTECTED WORKSPACE</p><h2>AdultGen Admin</h2></div><span>{message || 'Explicit reasons are audit logged.'}</span></header>{tab === 'overview' && <AdminOverview />}{tab === 'users' && <AdminUsersSection token={token} onMessage={setMessage} />}{tab === 'generations' && <AdminGenerationsSection token={token} />}{tab === 'publications' && <AdminPublicationsSection token={token} onMessage={setMessage} />}{tab === 'payments' && <AdminPaymentsSection token={token} />}{tab === 'wallet' && <AdminWalletSection token={token} onMessage={setMessage} />}{tab === 'audit' && <AdminAuditSection token={token} />}</section></main>;
}

function AdminOverview() {
  return <><section className="admin-metrics"><article><Activity /><span>API STATUS</span><strong>CONNECTED</strong></article><article><ShieldAlert /><span>MODERATION</span><strong>PROTECTED</strong></article><article><RadioTower /><span>DELIVERIES</span><strong>LIVE</strong></article></section><section className="admin-card"><h3>Operational boundary</h3><p>Dangerous mutations are separated from monitoring and require a reason.</p></section></>;
}

function AdminUsersSection({ token, onMessage }: { token: string; onMessage: (value: string) => void }) {
  const [items, setItems] = useState<AdminUser[]>([]);
  const load = useCallback(() => fetchAdminUsers(token).then((result) => setItems(result.items)), [token]);
  useEffect(() => { void load(); }, [load]);
  const toggle = async (user: AdminUser) => {
    const reason = window.prompt('Reason for capability change?'); if (!reason) return;
    await updateAdminUserCapabilities(token, user.id, { is_blocked: !user.is_blocked }, reason);
    onMessage('User capability updated'); await load();
  };
  return <section className="admin-card"><h3>Users</h3><div className="admin-table">{items.map((user) => <div className="admin-row" key={user.id}><span>{user.username || user.telegram_user_id}</span><span>{user.cached_available_balance ?? 0} credits</span><button onClick={() => void toggle(user)}>{user.is_blocked ? 'Unblock' : 'Block'}</button></div>)}</div></section>;
}

function AdminGenerationsSection({ token }: { token: string }) {
  const [items, setItems] = useState<AdminGeneration[]>([]);
  useEffect(() => { void fetchAdminGenerations(token).then((result) => setItems(result.items)); }, [token]);
  return <section className="admin-card"><h3>Generations</h3><div className="admin-table">{items.map((item) => <div className="admin-row" key={item.id}><span>{item.model_code}</span><span>{item.operation}</span><strong>{item.status}</strong></div>)}</div></section>;
}

function AdminPublicationsSection({ token, onMessage }: { token: string; onMessage: (value: string) => void }) {
  const [items, setItems] = useState<AdminPublication[]>([]);
  const load = useCallback(() => fetchAdminPublications(token).then((result) => setItems(result.items)), [token]);
  useEffect(() => { void load(); }, [load]);
  const hide = async (item: AdminPublication) => {
    const reason = window.prompt('Reason for moderation action?'); if (!reason) return;
    await applyAdminPublicationAction(token, item.id, 'hide', reason);
    onMessage('Publication hidden and audited'); await load();
  };
  return <section className="admin-card"><h3>Publications</h3><div className="admin-table">{items.map((item) => <div className="admin-row" key={item.id}><span>{item.title || item.id}</span><strong>{item.status}</strong><button onClick={() => void hide(item)}>Hide</button></div>)}</div></section>;
}

function AdminPaymentsSection({ token }: { token: string }) {
  const [items, setItems] = useState<AdminPaymentOrder[]>([]);
  useEffect(() => { void fetchAdminPaymentOrders(token).then((result) => setItems(result.items)); }, [token]);
  return <section className="admin-card"><h3>Payments</h3><div className="admin-table">{items.map((item) => <div className="admin-row" key={item.id}><span>{item.provider} / {item.package_code}</span><span>{item.amount_minor} {item.currency}</span><strong>{item.status}</strong></div>)}</div></section>;
}

function AdminWalletSection({ token, onMessage }: { token: string; onMessage: (value: string) => void }) {
  const [userId, setUserId] = useState(''); const [amount, setAmount] = useState(100); const [reason, setReason] = useState('');
  const submit = async () => { await createAdminWalletAdjustment(token, userId, amount, reason); onMessage('Wallet adjustment appended to ledger'); };
  return <section className="admin-card admin-two-column"><div><h3>Wallet adjustment</h3><p>This action appends a ledger entry; it never overwrites a balance.</p></div><form onSubmit={(event) => { event.preventDefault(); void submit(); }}><label>User ID<input value={userId} onChange={(event) => setUserId(event.target.value)} required /></label><label>Credits<input type="number" min="1" value={amount} onChange={(event) => setAmount(Number(event.target.value))} required /></label><label>Reason<input value={reason} onChange={(event) => setReason(event.target.value)} required minLength={3} /></label><button className="primary-action">Credit wallet</button></form></section>;
}

function AdminAuditSection({ token }: { token: string }) {
  const [items, setItems] = useState<AdminAuditEvent[]>([]);
  useEffect(() => { void fetchAdminAuditEvents(token).then((result) => setItems(result.items)); }, [token]);
  return <section className="admin-card"><h3>Audit events</h3><div className="admin-table">{items.map((item) => <div className="admin-row" key={item.id}><span>{item.target_type}</span><strong>{item.action}</strong><span>{item.reason || '—'}</span></div>)}</div></section>;
}
