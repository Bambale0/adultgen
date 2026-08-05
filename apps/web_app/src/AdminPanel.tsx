import { useEffect, useMemo, useState } from 'react';

import {
  applyAdminPublicationAction,
  createAdminWalletAdjustment,
  fetchAdminAuditEvents,
  fetchAdminGenerations,
  fetchAdminPaymentOrders,
  fetchAdminPublications,
  fetchAdminUsers,
  updateAdminUserCapabilities,
  type AdminAuditEvent,
  type AdminGeneration,
  type AdminPaymentOrder,
  type AdminPublication,
  type AdminUser,
  type AdminWalletAdjustment,
} from './adminApi';

const ADMIN_TOKEN_STORAGE_KEY = 'adultgen_admin_token';
const DEFAULT_LIMIT = 50;

type AdminTab = 'overview' | 'users' | 'generations' | 'publications' | 'payments' | 'wallet' | 'audit';
type LoadState = 'idle' | 'loading' | 'ready' | 'error';

type CapabilityDraft = {
  is_blocked: boolean;
  can_generate: boolean;
  can_publish_profile: boolean;
  can_publish_feed: boolean;
  can_use_payments: boolean;
  reason: string;
};

type PublicationActionDraft = {
  publication_id: string;
  action: 'hide' | 'restore' | 'delete';
  reason: string;
};

type WalletAdjustmentDraft = {
  user_id: string;
  amount: number;
  bucket: 'purchased' | 'subscription' | 'bonus';
  reason: string;
};

const emptyCapabilityDraft: CapabilityDraft = {
  is_blocked: false,
  can_generate: true,
  can_publish_profile: true,
  can_publish_feed: true,
  can_use_payments: true,
  reason: 'Operational safety review',
};

const defaultPublicationActionDraft: PublicationActionDraft = {
  publication_id: '',
  action: 'hide',
  reason: 'Moderation decision',
};

const defaultWalletAdjustmentDraft: WalletAdjustmentDraft = {
  user_id: '',
  amount: 100,
  bucket: 'bonus',
  reason: 'Support compensation',
};

export function AdminPanel() {
  const [adminToken, setAdminToken] = useState(() => localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) ?? '');
  const [tokenDraft, setTokenDraft] = useState(adminToken);
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  const [loadState, setLoadState] = useState<LoadState>('idle');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [generations, setGenerations] = useState<AdminGeneration[]>([]);
  const [publications, setPublications] = useState<AdminPublication[]>([]);
  const [payments, setPayments] = useState<AdminPaymentOrder[]>([]);
  const [auditEvents, setAuditEvents] = useState<AdminAuditEvent[]>([]);
  const [latestWalletAdjustment, setLatestWalletAdjustment] = useState<AdminWalletAdjustment | null>(null);

  const [selectedUserId, setSelectedUserId] = useState('');
  const [capabilityDraft, setCapabilityDraft] = useState<CapabilityDraft>(emptyCapabilityDraft);
  const [publicationActionDraft, setPublicationActionDraft] = useState<PublicationActionDraft>(
    defaultPublicationActionDraft,
  );
  const [walletAdjustmentDraft, setWalletAdjustmentDraft] = useState<WalletAdjustmentDraft>(
    defaultWalletAdjustmentDraft,
  );

  const selectedUser = useMemo(
    () => users.find((user) => user.id === selectedUserId) ?? null,
    [selectedUserId, users],
  );

  const metrics = useMemo(() => buildAdminMetrics(users, generations, publications, payments, auditEvents), [
    auditEvents,
    generations,
    payments,
    publications,
    users,
  ]);

  useEffect(() => {
    if (!adminToken) return;

    let ignore = false;
    setLoadState('loading');
    loadAdminData(adminToken)
      .then((snapshot) => {
        if (ignore) return;
        setUsers(snapshot.users);
        setGenerations(snapshot.generations);
        setPublications(snapshot.publications);
        setPayments(snapshot.payments);
        setAuditEvents(snapshot.auditEvents);
        setLoadState('ready');
      })
      .catch((error) => {
        if (ignore) return;
        setErrorMessage(error instanceof Error ? error.message : 'Admin data loading failed.');
        setLoadState('error');
      });

    return () => {
      ignore = true;
    };
  }, [adminToken]);

  useEffect(() => {
    if (!selectedUser) return;
    setCapabilityDraft({
      is_blocked: selectedUser.is_blocked,
      can_generate: selectedUser.can_generate,
      can_publish_profile: selectedUser.can_publish_profile,
      can_publish_feed: selectedUser.can_publish_feed,
      can_use_payments: selectedUser.can_use_payments,
      reason: capabilityDraft.reason || 'Operational safety review',
    });
    setWalletAdjustmentDraft((current) => ({ ...current, user_id: selectedUser.id }));
  }, [selectedUser?.id]);

  async function runAdminAction<T>(message: string, action: () => Promise<T>): Promise<T | null> {
    if (!adminToken) {
      setErrorMessage('Вставь ADMIN_API_TOKEN и подключи админку.');
      return null;
    }
    setStatusMessage(message);
    setErrorMessage(null);
    try {
      const result = await action();
      setStatusMessage('Готово.');
      return result;
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Admin action failed.');
      setStatusMessage(null);
      return null;
    }
  }

  function handleConnectAdmin() {
    const normalized = tokenDraft.trim();
    if (!normalized) {
      setErrorMessage('ADMIN_API_TOKEN пустой.');
      return;
    }
    localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, normalized);
    setAdminToken(normalized);
    setStatusMessage('Admin token сохранён локально.');
    setErrorMessage(null);
  }

  function handleDisconnectAdmin() {
    localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
    setAdminToken('');
    setTokenDraft('');
    setUsers([]);
    setGenerations([]);
    setPublications([]);
    setPayments([]);
    setAuditEvents([]);
    setLatestWalletAdjustment(null);
    setLoadState('idle');
  }

  async function refreshAll() {
    const snapshot = await runAdminAction('Обновляем admin snapshot…', () => loadAdminData(adminToken));
    if (!snapshot) return;
    setUsers(snapshot.users);
    setGenerations(snapshot.generations);
    setPublications(snapshot.publications);
    setPayments(snapshot.payments);
    setAuditEvents(snapshot.auditEvents);
  }

  async function refreshUsers() {
    const result = await runAdminAction('Обновляем users…', () => fetchAdminUsers(adminToken, DEFAULT_LIMIT));
    if (result) setUsers(result.items);
  }

  async function refreshGenerations() {
    const result = await runAdminAction('Обновляем generations…', () => fetchAdminGenerations(adminToken, DEFAULT_LIMIT));
    if (result) setGenerations(result.items);
  }

  async function refreshPublications() {
    const result = await runAdminAction('Обновляем publications…', () => fetchAdminPublications(adminToken, DEFAULT_LIMIT));
    if (result) setPublications(result.items);
  }

  async function refreshPayments() {
    const result = await runAdminAction('Обновляем payment orders…', () => fetchAdminPaymentOrders(adminToken, DEFAULT_LIMIT));
    if (result) setPayments(result.items);
  }

  async function refreshAudit() {
    const result = await runAdminAction('Обновляем audit events…', () => fetchAdminAuditEvents(adminToken, DEFAULT_LIMIT));
    if (result) setAuditEvents(result.items);
  }

  async function handleUpdateCapabilities() {
    if (!selectedUser) {
      setErrorMessage('Выбери пользователя.');
      return;
    }
    const result = await runAdminAction('Обновляем user capabilities…', () =>
      updateAdminUserCapabilities(adminToken, selectedUser.id, capabilityDraft),
    );
    if (!result) return;
    setUsers((items) => items.map((user) => (user.id === result.id ? result : user)));
    await refreshAudit();
  }

  async function handlePublicationAction() {
    if (!publicationActionDraft.publication_id) {
      setErrorMessage('Выбери publication.');
      return;
    }
    const result = await runAdminAction('Применяем publication action…', () =>
      applyAdminPublicationAction(
        adminToken,
        publicationActionDraft.publication_id,
        publicationActionDraft.action,
        publicationActionDraft.reason,
      ),
    );
    if (!result) return;
    setPublications((items) => items.map((publication) => (publication.id === result.id ? result : publication)));
    await refreshAudit();
  }

  async function handleWalletAdjustment() {
    if (!walletAdjustmentDraft.user_id) {
      setErrorMessage('Выбери пользователя для wallet adjustment.');
      return;
    }
    const result = await runAdminAction('Начисляем admin wallet adjustment…', () =>
      createAdminWalletAdjustment(adminToken, walletAdjustmentDraft),
    );
    if (!result) return;
    setLatestWalletAdjustment(result);
    await refreshUsers();
    await refreshAudit();
  }

  return (
    <main className="admin-shell">
      <aside className="admin-sidebar">
        <div>
          <p className="eyebrow">AdultGen Admin</p>
          <h1>Control Room</h1>
          <p className="sidebar-copy">
            Операционный контур: пользователи, генерации, публикации, платежи, ручные кредиты и audit trail.
          </p>
        </div>
        <AdminTokenCard
          adminToken={adminToken}
          tokenDraft={tokenDraft}
          setTokenDraft={setTokenDraft}
          onConnect={handleConnectAdmin}
          onDisconnect={handleDisconnectAdmin}
        />
        <nav className="route-nav" aria-label="Админская навигация">
          {ADMIN_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={tab.id === activeTab ? 'route-button active' : 'route-button'}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.title}
            </button>
          ))}
        </nav>
      </aside>
      <section className="admin-main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">/admin</p>
            <h2>{ADMIN_TABS.find((tab) => tab.id === activeTab)?.title ?? 'Admin'}</h2>
          </div>
          <div className="topbar-actions">
            <button className="ghost-button" type="button" onClick={() => void refreshAll()} disabled={!adminToken}>
              Refresh all
            </button>
            <span className={`status-pill ${loadState === 'error' ? 'error' : ''}`}>{loadState}</span>
            {statusMessage && <span className="status-pill">{statusMessage}</span>}
            {errorMessage && <span className="status-pill error">{errorMessage}</span>}
          </div>
        </header>

        {!adminToken ? (
          <section className="card stack-card danger-card">
            <p className="eyebrow">Locked</p>
            <h3>Нужен ADMIN_API_TOKEN</h3>
            <p>
              Админка не использует пользовательскую web-session и 18+ flow. Это отдельная поверхность управления,
              закрытая backend-token guard’ом.
            </p>
          </section>
        ) : activeTab === 'overview' ? (
          <AdminOverview metrics={metrics} onRefresh={() => void refreshAll()} />
        ) : activeTab === 'users' ? (
          <AdminUsersSection
            users={users}
            selectedUserId={selectedUserId}
            setSelectedUserId={setSelectedUserId}
            selectedUser={selectedUser}
            capabilityDraft={capabilityDraft}
            setCapabilityDraft={setCapabilityDraft}
            onRefresh={() => void refreshUsers()}
            onUpdateCapabilities={() => void handleUpdateCapabilities()}
          />
        ) : activeTab === 'generations' ? (
          <AdminGenerationsSection generations={generations} onRefresh={() => void refreshGenerations()} />
        ) : activeTab === 'publications' ? (
          <AdminPublicationsSection
            publications={publications}
            actionDraft={publicationActionDraft}
            setActionDraft={setPublicationActionDraft}
            onRefresh={() => void refreshPublications()}
            onApplyAction={() => void handlePublicationAction()}
          />
        ) : activeTab === 'payments' ? (
          <AdminPaymentsSection payments={payments} onRefresh={() => void refreshPayments()} />
        ) : activeTab === 'wallet' ? (
          <AdminWalletSection
            users={users}
            draft={walletAdjustmentDraft}
            setDraft={setWalletAdjustmentDraft}
            latestAdjustment={latestWalletAdjustment}
            onApply={() => void handleWalletAdjustment()}
          />
        ) : (
          <AdminAuditSection events={auditEvents} onRefresh={() => void refreshAudit()} />
        )}
      </section>
    </main>
  );
}

const ADMIN_TABS: { id: AdminTab; title: string }[] = [
  { id: 'overview', title: 'Overview' },
  { id: 'users', title: 'Users' },
  { id: 'generations', title: 'Generations' },
  { id: 'publications', title: 'Publications' },
  { id: 'payments', title: 'Payments' },
  { id: 'wallet', title: 'Wallet' },
  { id: 'audit', title: 'Audit' },
];

async function loadAdminData(adminToken: string) {
  const [users, generations, publications, payments, auditEvents] = await Promise.all([
    fetchAdminUsers(adminToken, DEFAULT_LIMIT),
    fetchAdminGenerations(adminToken, DEFAULT_LIMIT),
    fetchAdminPublications(adminToken, DEFAULT_LIMIT),
    fetchAdminPaymentOrders(adminToken, DEFAULT_LIMIT),
    fetchAdminAuditEvents(adminToken, DEFAULT_LIMIT),
  ]);
  return {
    users: users.items,
    generations: generations.items,
    publications: publications.items,
    payments: payments.items,
    auditEvents: auditEvents.items,
  };
}

function AdminTokenCard({
  adminToken,
  tokenDraft,
  setTokenDraft,
  onConnect,
  onDisconnect,
}: {
  adminToken: string;
  tokenDraft: string;
  setTokenDraft: (value: string) => void;
  onConnect: () => void;
  onDisconnect: () => void;
}) {
  return (
    <section className="admin-token-card">
      <p className="eyebrow">Access</p>
      <label>
        ADMIN_API_TOKEN
        <input
          type="password"
          value={tokenDraft}
          onChange={(event) => setTokenDraft(event.target.value)}
          placeholder="Paste token"
        />
      </label>
      <div className="button-row">
        <button className="primary-button" type="button" onClick={onConnect}>
          Connect
        </button>
        <button className="ghost-button" type="button" onClick={onDisconnect} disabled={!adminToken}>
          Disconnect
        </button>
      </div>
      <small>{adminToken ? 'Token stored locally in this browser.' : 'No admin token connected.'}</small>
    </section>
  );
}

function AdminOverview({ metrics, onRefresh }: { metrics: ReturnType<typeof buildAdminMetrics>; onRefresh: () => void }) {
  return (
    <section className="admin-workspace">
      <div className="card hero-card">
        <p className="eyebrow">Operational snapshot</p>
        <h3>Панель контроля платформы</h3>
        <p>
          Здесь видны основные риски: заблокированные пользователи, failed generations, скрытые публикации,
          unpaid/paid payments и последние действия админа.
        </p>
        <button className="primary-button" type="button" onClick={onRefresh}>
          Refresh snapshot
        </button>
      </div>
      <div className="admin-metrics-grid">
        {metrics.map((metric) => (
          <MetricTile key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
        ))}
      </div>
    </section>
  );
}

function AdminUsersSection({
  users,
  selectedUserId,
  setSelectedUserId,
  selectedUser,
  capabilityDraft,
  setCapabilityDraft,
  onRefresh,
  onUpdateCapabilities,
}: {
  users: AdminUser[];
  selectedUserId: string;
  setSelectedUserId: (value: string) => void;
  selectedUser: AdminUser | null;
  capabilityDraft: CapabilityDraft;
  setCapabilityDraft: (value: CapabilityDraft) => void;
  onRefresh: () => void;
  onUpdateCapabilities: () => void;
}) {
  return (
    <section className="admin-workspace">
      <AdminSectionHeader title="Users" description="Capabilities, blocks and cached wallet projection." onRefresh={onRefresh} />
      <div className="admin-two-column">
        <div className="card table-card">
          <AdminTable
            headers={['User', 'Telegram', 'Flags', 'Balance', 'Updated']}
            rows={users.map((user) => [
              <button className="link-button" type="button" onClick={() => setSelectedUserId(user.id)}>
                {user.username ?? user.first_name ?? shortId(user.id)}
              </button>,
              String(user.telegram_user_id),
              <UserFlags user={user} />,
              `${formatNumber(user.cached_available_balance ?? 0)} / ${formatNumber(user.cached_reserved_balance ?? 0)}`,
              formatDate(user.updated_at),
            ])}
            emptyText="Пользователи не загружены."
          />
        </div>
        <aside className="card stack-card danger-card">
          <p className="eyebrow">Dangerous action</p>
          <h3>User capabilities</h3>
          <label>
            User
            <select value={selectedUserId} onChange={(event) => setSelectedUserId(event.target.value)}>
              <option value="">Выбери пользователя</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.username ?? user.first_name ?? shortId(user.id)} · {user.id}
                </option>
              ))}
            </select>
          </label>
          <CapabilityCheckboxes draft={capabilityDraft} setDraft={setCapabilityDraft} />
          <label>
            Reason
            <textarea
              rows={3}
              value={capabilityDraft.reason}
              onChange={(event) => setCapabilityDraft({ ...capabilityDraft, reason: event.target.value })}
            />
          </label>
          {selectedUser && <CodeBlock value={JSON.stringify(selectedUser, null, 2)} />}
          <button className="primary-button" type="button" onClick={onUpdateCapabilities} disabled={!selectedUserId}>
            Apply capabilities
          </button>
        </aside>
      </div>
    </section>
  );
}

function AdminGenerationsSection({ generations, onRefresh }: { generations: AdminGeneration[]; onRefresh: () => void }) {
  return (
    <section className="admin-workspace">
      <AdminSectionHeader title="Generations" description="Provider task lifecycle and credit reservation state." onRefresh={onRefresh} />
      <div className="card table-card">
        <AdminTable
          headers={['Task', 'User', 'Status', 'Model', 'Credits', 'Provider task', 'Created']}
          rows={generations.map((task) => [
            shortId(task.id),
            shortId(task.user_id),
            <StatusBadge status={task.status} />,
            task.model_code,
            `${task.reserved_credits} reserved / ${task.charged_credits} charged`,
            task.provider_task_id ?? '—',
            formatDate(task.created_at),
          ])}
          emptyText="Generation tasks не загружены."
        />
      </div>
    </section>
  );
}

function AdminPublicationsSection({
  publications,
  actionDraft,
  setActionDraft,
  onRefresh,
  onApplyAction,
}: {
  publications: AdminPublication[];
  actionDraft: PublicationActionDraft;
  setActionDraft: (value: PublicationActionDraft) => void;
  onRefresh: () => void;
  onApplyAction: () => void;
}) {
  return (
    <section className="admin-workspace">
      <AdminSectionHeader title="Publications" description="Feed/profile visibility, explicit flags and moderation actions." onRefresh={onRefresh} />
      <div className="admin-two-column">
        <div className="card table-card">
          <AdminTable
            headers={['Publication', 'User', 'Visibility', 'Status', 'Explicit', 'Published']}
            rows={publications.map((publication) => [
              <button
                className="link-button"
                type="button"
                onClick={() => setActionDraft({ ...actionDraft, publication_id: publication.id })}
              >
                {publication.title ?? shortId(publication.id)}
              </button>,
              shortId(publication.user_id),
              publication.visibility,
              <StatusBadge status={publication.status} />,
              publication.is_explicit ? 'explicit' : 'safe',
              formatDate(publication.published_at),
            ])}
            emptyText="Публикации не загружены."
          />
        </div>
        <aside className="card stack-card danger-card">
          <p className="eyebrow">Dangerous action</p>
          <h3>Publication action</h3>
          <label>
            Publication
            <select
              value={actionDraft.publication_id}
              onChange={(event) => setActionDraft({ ...actionDraft, publication_id: event.target.value })}
            >
              <option value="">Выбери публикацию</option>
              {publications.map((publication) => (
                <option key={publication.id} value={publication.id}>
                  {publication.title ?? shortId(publication.id)} · {publication.status}
                </option>
              ))}
            </select>
          </label>
          <label>
            Action
            <select
              value={actionDraft.action}
              onChange={(event) =>
                setActionDraft({ ...actionDraft, action: event.target.value as PublicationActionDraft['action'] })
              }
            >
              <option value="hide">Hide</option>
              <option value="restore">Restore</option>
              <option value="delete">Delete</option>
            </select>
          </label>
          <label>
            Reason
            <textarea
              rows={3}
              value={actionDraft.reason}
              onChange={(event) => setActionDraft({ ...actionDraft, reason: event.target.value })}
            />
          </label>
          <button className="primary-button" type="button" onClick={onApplyAction} disabled={!actionDraft.publication_id}>
            Apply publication action
          </button>
        </aside>
      </div>
    </section>
  );
}

function AdminPaymentsSection({ payments, onRefresh }: { payments: AdminPaymentOrder[]; onRefresh: () => void }) {
  return (
    <section className="admin-workspace">
      <AdminSectionHeader title="Payments" description="Payment orders and checkout/provider status." onRefresh={onRefresh} />
      <div className="card table-card">
        <AdminTable
          headers={['Order', 'User', 'Provider', 'Package', 'Amount', 'Status', 'Paid']}
          rows={payments.map((order) => [
            shortId(order.id),
            shortId(order.user_id),
            order.provider,
            order.package_code,
            `${order.amount_minor / 100} ${order.currency}`,
            <StatusBadge status={order.status} />,
            formatDate(order.paid_at),
          ])}
          emptyText="Payment orders не загружены."
        />
      </div>
    </section>
  );
}

function AdminWalletSection({
  users,
  draft,
  setDraft,
  latestAdjustment,
  onApply,
}: {
  users: AdminUser[];
  draft: WalletAdjustmentDraft;
  setDraft: (value: WalletAdjustmentDraft) => void;
  latestAdjustment: AdminWalletAdjustment | null;
  onApply: () => void;
}) {
  return (
    <section className="admin-workspace">
      <AdminSectionHeader title="Wallet adjustments" description="Manual credit grants through the immutable ledger." />
      <div className="admin-two-column">
        <form className="card stack-card danger-card" onSubmit={(event) => event.preventDefault()}>
          <p className="eyebrow">Ledger-only mutation</p>
          <h3>Credit wallet</h3>
          <label>
            User
            <select value={draft.user_id} onChange={(event) => setDraft({ ...draft, user_id: event.target.value })}>
              <option value="">Выбери пользователя</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.username ?? user.first_name ?? shortId(user.id)} · available {user.cached_available_balance ?? 0}
                </option>
              ))}
            </select>
          </label>
          <label>
            Amount
            <input
              type="number"
              min="1"
              max="1000000"
              value={draft.amount}
              onChange={(event) => setDraft({ ...draft, amount: Number(event.target.value) })}
            />
          </label>
          <label>
            Bucket
            <select value={draft.bucket} onChange={(event) => setDraft({ ...draft, bucket: event.target.value as WalletAdjustmentDraft['bucket'] })}>
              <option value="bonus">bonus</option>
              <option value="purchased">purchased</option>
              <option value="subscription">subscription</option>
            </select>
          </label>
          <label>
            Reason
            <textarea rows={3} value={draft.reason} onChange={(event) => setDraft({ ...draft, reason: event.target.value })} />
          </label>
          <button className="primary-button" type="button" onClick={onApply} disabled={!draft.user_id}>
            Apply wallet adjustment
          </button>
        </form>
        <aside className="card stack-card">
          <p className="eyebrow">Latest adjustment</p>
          {latestAdjustment ? <CodeBlock value={JSON.stringify(latestAdjustment, null, 2)} /> : <p className="muted-text">Пока нет операции.</p>}
        </aside>
      </div>
    </section>
  );
}

function AdminAuditSection({ events, onRefresh }: { events: AdminAuditEvent[]; onRefresh: () => void }) {
  return (
    <section className="admin-workspace">
      <AdminSectionHeader title="Audit events" description="Append-only trail for dangerous admin actions." onRefresh={onRefresh} />
      <div className="card table-card">
        <AdminTable
          headers={['Time', 'Action', 'Target', 'Reason', 'Actor']}
          rows={events.map((event) => [
            formatDate(event.created_at),
            event.action,
            `${event.target_type}:${event.target_id ? shortId(event.target_id) : '—'}`,
            event.reason ?? '—',
            event.admin_user_id ? shortId(event.admin_user_id) : 'static-token',
          ])}
          emptyText="Audit events не загружены."
        />
      </div>
    </section>
  );
}

function AdminSectionHeader({ title, description, onRefresh }: { title: string; description: string; onRefresh?: () => void }) {
  return (
    <header className="admin-section-header">
      <div>
        <p className="eyebrow">Admin surface</p>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      {onRefresh && (
        <button className="ghost-button" type="button" onClick={onRefresh}>
          Refresh
        </button>
      )}
    </header>
  );
}

function AdminTable({
  headers,
  rows,
  emptyText,
}: {
  headers: string[];
  rows: (React.ReactNode | string | number | null)[][];
  emptyText: string;
}) {
  return (
    <div className="admin-table-wrap">
      <table className="admin-table">
        <thead>
          <tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={headers.length}>{emptyText}</td>
            </tr>
          ) : (
            rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => <td key={`${rowIndex}-${cellIndex}`}>{cell ?? '—'}</td>)}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function CapabilityCheckboxes({ draft, setDraft }: { draft: CapabilityDraft; setDraft: (value: CapabilityDraft) => void }) {
  return (
    <div className="admin-checkbox-grid">
      {(['is_blocked', 'can_generate', 'can_publish_profile', 'can_publish_feed', 'can_use_payments'] as const).map((field) => (
        <label key={field} className="checkbox-label">
          <input type="checkbox" checked={draft[field]} onChange={(event) => setDraft({ ...draft, [field]: event.target.checked })} />
          {field}
        </label>
      ))}
    </div>
  );
}

function UserFlags({ user }: { user: AdminUser }) {
  return (
    <span className="admin-flag-list">
      {user.is_blocked && <span className="guard-pill danger">blocked</span>}
      {user.can_generate && <span className="guard-pill enabled">generate</span>}
      {user.can_publish_feed && <span className="guard-pill enabled">feed</span>}
      {!user.can_use_payments && <span className="guard-pill danger">payments off</span>}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  return <span className={`status-pill ${statusTone(status)}`}>{status}</span>;
}

function MetricTile({ label, value, tone }: { label: string; value: number | string; tone?: 'good' | 'warn' | 'danger' }) {
  return (
    <section className={`metric-card admin-metric ${tone ?? ''}`}>
      <p className="eyebrow">{label}</p>
      <strong>{typeof value === 'number' ? formatNumber(value) : value}</strong>
    </section>
  );
}

function CodeBlock({ value }: { value: string }) {
  return <pre className="code-block">{value}</pre>;
}

function buildAdminMetrics(
  users: AdminUser[],
  generations: AdminGeneration[],
  publications: AdminPublication[],
  payments: AdminPaymentOrder[],
  auditEvents: AdminAuditEvent[],
) {
  return [
    { label: 'Users', value: users.length, tone: 'good' as const },
    { label: 'Blocked users', value: users.filter((user) => user.is_blocked).length, tone: 'warn' as const },
    { label: 'Generations', value: generations.length, tone: 'good' as const },
    { label: 'Failed generations', value: generations.filter((task) => task.status === 'failed').length, tone: 'danger' as const },
    { label: 'Publications', value: publications.length, tone: 'good' as const },
    { label: 'Hidden/deleted', value: publications.filter((publication) => publication.status !== 'active').length, tone: 'warn' as const },
    { label: 'Paid orders', value: payments.filter((payment) => payment.status === 'paid').length, tone: 'good' as const },
    { label: 'Audit events', value: auditEvents.length, tone: 'warn' as const },
  ];
}

function statusTone(status: string) {
  if (['paid', 'active', 'completed', 'ready'].includes(status)) return 'success';
  if (['failed', 'deleted', 'hidden', 'blocked'].includes(status)) return 'error';
  return '';
}

function formatDate(value: string | null | undefined) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value));
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('ru-RU').format(value);
}

function shortId(value: string) {
  return value.slice(0, 8);
}
