import { Activity, KeyRound, RadioTower, ShieldAlert } from 'lucide-react';
import { useState } from 'react';

const ADMIN_KEY = 'adultgen.admin-token.v1';

export function AdminPanel() {
  const [token, setToken] = useState(() => window.localStorage.getItem(ADMIN_KEY) || '');
  const [draft, setDraft] = useState('');
  if (!token) {
    return <main className="admin-lock"><section><div className="gate-icon"><KeyRound /></div><p className="eyebrow">ADMIN AUTHORITY</p><h1>Control Room</h1><p>Нужен ADMIN_API_TOKEN</p><label>Admin token<input type="password" value={draft} onChange={(event) => setDraft(event.target.value)} autoComplete="off" /></label><button className="primary-action" disabled={!draft} onClick={() => { window.localStorage.setItem(ADMIN_KEY, draft); setToken(draft); }}>Unlock console</button></section></main>;
  }
  return <main className="admin-console"><header><div><p className="eyebrow">ADULTGEN / OPERATIONS</p><h1>Control Room</h1></div><button className="secondary-action" onClick={() => { window.localStorage.removeItem(ADMIN_KEY); setToken(''); }}>Lock console</button></header><section className="admin-metrics"><article><Activity /><span>API STATUS</span><strong>CONNECTED</strong></article><article><ShieldAlert /><span>MODERATION</span><strong>QUEUE —</strong></article><article><RadioTower /><span>DELIVERIES</span><strong>LIVE</strong></article></section><section className="panel admin-note"><h2>Operational boundary</h2><p>Admin mutations require explicit reasons and are written to the audit log. Full moderation tables activate when the protected admin API is connected.</p></section></main>;
}
