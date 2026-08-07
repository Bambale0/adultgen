import { useEffect, useState, type ChangeEvent, type FormEvent, type ReactNode } from 'react';
import {
  api,
  type AdultConsentStatus,
  type CreditPackage,
  type GenerationMode,
  type GenerationTask,
  type Profile,
  type Publication,
  type WalletBalance,
  type WebSession,
} from './api';
import { sessionStore } from './session';

type RouteId = 'feed' | 'studio' | 'missions' | 'profile' | 'billing';
type Workspace = { avatar_id: string; project_id: string; scene_id: string };
type Toast = { tone: 'cyan' | 'pink' | 'error'; message: string } | null;

const routes: { id: RouteId; path: string; label: string; icon: string; protected?: boolean }[] = [
  { id: 'feed', path: '/', label: 'ORBITAL FEED', icon: '◫' },
  { id: 'studio', path: '/studio', label: 'DEPLOY', icon: '✦', protected: true },
  { id: 'missions', path: '/missions', label: 'TELEMETRY', icon: '⌁', protected: true },
  { id: 'profile', path: '/profile', label: 'OPERATOR', icon: '◎', protected: true },
  { id: 'billing', path: '/billing', label: 'CREDITS', icon: '◇', protected: true },
];

const safeSignals = [
  { title: 'NEON CONTACT', copy: 'Cinematic synthwave portrait // safe preview', accent: 'pink', metric: '12.8K' },
  { title: 'ORBITAL DRIFT', copy: 'Zero-g editorial motion // cyan atmosphere', accent: 'cyan', metric: '9.4K' },
  { title: 'NIGHT PROTOCOL', copy: 'Rainy megacity scene // volumetric light', accent: 'violet', metric: '18.2K' },
  { title: 'SIGNAL BLOOM', copy: 'Abstract bio-digital pattern // macro detail', accent: 'lime', metric: '7.1K' },
  { title: 'CHROME PILOT', copy: 'Mecha operator concept // studio lighting', accent: 'silver', metric: '5.6K' },
  { title: 'VOID GARDEN', copy: 'Surreal flora // black glass landscape', accent: 'blue', metric: '14.0K' },
];

function routeFromPath(): RouteId {
  const found = routes.find((item) => item.path === window.location.pathname);
  return found?.id ?? 'feed';
}

export function App() {
  const [route, setRoute] = useState<RouteId>(() => routeFromPath());
  const [session, setSession] = useState<WebSession | null>(() => sessionStore.session());
  const [consent, setConsent] = useState<AdultConsentStatus | null>(() => sessionStore.consent());
  const [authOpen, setAuthOpen] = useState(false);
  const [ageOpen, setAgeOpen] = useState(false);
  const [toast, setToast] = useState<Toast>(null);
  const [feed, setFeed] = useState<Publication[]>([]);
  const [tasks, setTasks] = useState<GenerationTask[]>([]);
  const [wallet, setWallet] = useState<WalletBalance | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);

  const active = routes.find((item) => item.id === route) ?? routes[0];
  const unlocked = Boolean(session && consent?.accepted);

  useEffect(() => {
    const onPop = () => setRoute(routeFromPath());
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 3600);
    return () => window.clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    if (!session) return;
    void api.getConsent(session.access_token).then((status) => {
      setConsent(status);
      sessionStore.saveConsent(status);
    }).catch(() => undefined);
  }, [session]);

  useEffect(() => {
    if (!unlocked || !session) return;
    void Promise.allSettled([
      api.feed().then((result) => setFeed(result.items)),
      api.generations(session.access_token).then((result) => setTasks(result.items)),
      api.wallet(session.access_token).then(setWallet),
      api.profile(session.access_token).then(setProfile),
    ]);
  }, [unlocked, session]);

  function navigate(id: RouteId) {
    const next = routes.find((item) => item.id === id) ?? routes[0];
    if (next.protected && !session) {
      setAuthOpen(true);
      return;
    }
    if (next.protected && !consent?.accepted && id !== 'billing') {
      setAgeOpen(true);
      return;
    }
    window.history.pushState({ route: id }, '', next.path);
    setRoute(id);
  }

  function logout() {
    sessionStore.clear();
    setSession(null);
    setConsent(null);
    setFeed([]);
    setTasks([]);
    setWallet(null);
    setProfile(null);
    setWorkspace(null);
    window.history.pushState({ route: 'feed' }, '', '/');
    setRoute('feed');
  }

  async function onAuthenticated(nextSession: WebSession) {
    sessionStore.saveSession(nextSession);
    setSession(nextSession);
    setAuthOpen(false);
    try {
      const status = await api.getConsent(nextSession.access_token);
      setConsent(status);
      sessionStore.saveConsent(status);
      if (!status.accepted) setAgeOpen(true);
    } catch (error) {
      setToast({ tone: 'error', message: errorMessage(error) });
    }
  }

  async function acceptAge() {
    if (!session) return;
    try {
      const result = await api.acceptConsent(session.access_token);
      sessionStore.saveConsent(result);
      setConsent(result);
      setAgeOpen(false);
      setToast({ tone: 'cyan', message: 'AGE GATE // VERIFIED' });
    } catch (error) {
      setToast({ tone: 'error', message: errorMessage(error) });
    }
  }

  return (
    <div className="orbital-app">
      <div className="scanline-layer" aria-hidden="true" />
      <Sidebar
        route={route}
        session={session}
        wallet={wallet}
        onNavigate={navigate}
        onAuth={() => setAuthOpen(true)}
        onLogout={logout}
      />
      <main className="orbital-main">
        <Topbar
          active={active}
          unlocked={unlocked}
          session={session}
          onAuth={() => setAuthOpen(true)}
          onNavigate={navigate}
        />
        {route === 'feed' && (
          <FeedScreen
            unlocked={unlocked}
            publications={feed}
            session={session}
            onSave={async (id) => {
              if (!session) return setAuthOpen(true);
              try {
                await api.savePublication(session.access_token, id);
                setToast({ tone: 'pink', message: 'SIGNAL // SAVED TO COLLECTION' });
              } catch (error) {
                setToast({ tone: 'error', message: errorMessage(error) });
              }
            }}
            onReport={async (id) => {
              if (!session) return setAuthOpen(true);
              try {
                await api.reportPublication(session.access_token, id);
                setToast({ tone: 'cyan', message: 'REPORT // TRANSMITTED' });
              } catch (error) {
                setToast({ tone: 'error', message: errorMessage(error) });
              }
            }}
            onDeploy={() => navigate('studio')}
          />
        )}
        {route === 'studio' && session && consent?.accepted && (
          <StudioScreen
            session={session}
            workspace={workspace}
            setWorkspace={setWorkspace}
            tasks={tasks}
            setTasks={setTasks}
            setWallet={setWallet}
            notify={setToast}
          />
        )}
        {route === 'missions' && session && consent?.accepted && (
          <TelemetryScreen session={session} tasks={tasks} setTasks={setTasks} notify={setToast} />
        )}
        {route === 'profile' && session && consent?.accepted && (
          <ProfileScreen session={session} profile={profile} setProfile={setProfile} notify={setToast} />
        )}
        {route === 'billing' && session && (
          <BillingScreen session={session} wallet={wallet} setWallet={setWallet} notify={setToast} />
        )}
      </main>
      {authOpen && <AuthModal onClose={() => setAuthOpen(false)} onAuthenticated={onAuthenticated} notify={setToast} />}
      {ageOpen && <AgeGate onClose={() => setAgeOpen(false)} onAccept={() => void acceptAge()} />}
      {toast && <div className={`toast ${toast.tone}`}>{toast.message}</div>}
    </div>
  );
}

function Sidebar({
  route,
  session,
  wallet,
  onNavigate,
  onAuth,
  onLogout,
}: {
  route: RouteId;
  session: WebSession | null;
  wallet: WalletBalance | null;
  onNavigate: (id: RouteId) => void;
  onAuth: () => void;
  onLogout: () => void;
}) {
  return (
    <aside className="sidebar">
      <button className="brand" onClick={() => onNavigate('feed')}>
        <span className="brand-glyph">A/G</span>
        <span><strong>ADULTGEN</strong><small>ORBITAL CONTROL</small></span>
      </button>
      <div className="sidebar-status"><i /> SYSTEM ONLINE <span>V2.0</span></div>
      <nav>
        <p className="nav-kicker">// SECTORS</p>
        {routes.map((item) => (
          <button key={item.id} className={route === item.id ? 'nav-link active' : 'nav-link'} onClick={() => onNavigate(item.id)}>
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
            {route === item.id && <b>●</b>}
          </button>
        ))}
      </nav>
      <section className="credit-terminal">
        <p>AVAILABLE CREDITS</p>
        <strong>{wallet?.total_available?.toLocaleString('ru-RU') ?? '---'}</strong>
        <span>{wallet ? `${wallet.total_reserved} RESERVED` : 'NO WALLET SYNC'}</span>
      </section>
      <div className="sidebar-spacer" />
      {session ? (
        <section className="operator-chip">
          <div className="operator-avatar">{session.display_name.slice(0, 2).toUpperCase()}</div>
          <div><strong>{session.display_name}</strong><small>{session.email}</small></div>
          <button onClick={onLogout} title="Выйти">↯</button>
        </section>
      ) : (
        <button className="terminal-button full" onClick={onAuth}>INITIALIZE SESSION</button>
      )}
    </aside>
  );
}

function Topbar({
  active,
  unlocked,
  session,
  onAuth,
  onNavigate,
}: {
  active: (typeof routes)[number];
  unlocked: boolean;
  session: WebSession | null;
  onAuth: () => void;
  onNavigate: (id: RouteId) => void;
}) {
  return (
    <header className="topbar">
      <div className="sector-title"><span>SECTOR //</span><strong>{active.label}</strong></div>
      <label className="search-terminal">
        <span>⌕</span><input placeholder="SEARCH SIGNALS / PROMPTS / OPERATORS" />
        <kbd>⌘K</kbd>
      </label>
      <div className="top-actions">
        <span className={unlocked ? 'sync-badge active' : 'sync-badge'}>{unlocked ? '● SYNCED' : '○ SAFE MODE'}</span>
        <button className="deploy-button" onClick={() => session ? onNavigate('studio') : onAuth()}>✦ DEPLOY</button>
      </div>
    </header>
  );
}

function FeedScreen({
  unlocked,
  publications,
  session,
  onSave,
  onReport,
  onDeploy,
}: {
  unlocked: boolean;
  publications: Publication[];
  session: WebSession | null;
  onSave: (id: string) => void;
  onReport: (id: string) => void;
  onDeploy: () => void;
}) {
  const real = unlocked && publications.length > 0;
  return (
    <section className="screen feed-screen">
      <div className="screen-heading">
        <div><p className="eyebrow">LIVE NETWORK // ORBITAL V2</p><h1>ORBITAL FEED</h1></div>
        <div className="feed-tabs"><button className="active">LIVE</button><button>TRENDING</button><button>FOLLOWING</button></div>
      </div>
      {!unlocked && (
        <div className="safe-banner"><span>18+ LOCKED</span><p>Public surface shows non-explicit preview signals only. Sign in and confirm age to sync the live creator feed.</p><button onClick={onDeploy}>OPEN DEPLOY</button></div>
      )}
      <div className="masonry-feed">
        {real ? publications.map((item, index) => (
          <article className={`signal-card h-${(index % 3) + 1}`} key={item.id}>
            <MediaPreview publication={item} />
            <div className="signal-overlay">
              <div className="signal-meta"><span>#{String(index + 1).padStart(3, '0')}</span><b>{item.visibility.toUpperCase()}</b></div>
              <h2>{item.title || 'UNTITLED SIGNAL'}</h2>
              <p>{item.description || 'No public transmission note.'}</p>
              <div className="signal-footer"><span>@{short(item.user_id)}</span><div><button onClick={() => onSave(item.id)}>◇ SAVE</button><button onClick={() => onReport(item.id)}>⚑</button></div></div>
            </div>
          </article>
        )) : safeSignals.map((item, index) => (
          <article className={`signal-card mock ${item.accent} h-${(index % 3) + 1}`} key={item.title}>
            <div className="mock-visual"><span className="reticle">＋</span><span className="coordinates">X:{31 + index * 7}.2 / Y:{77 - index * 4}.8</span></div>
            <div className="signal-overlay">
              <div className="signal-meta"><span>SAFE // {String(index + 1).padStart(2, '0')}</span><b>{item.metric}</b></div>
              <h2>{item.title}</h2><p>{item.copy}</p>
              <div className="signal-footer"><span>@ORBITAL.SEED</span><button onClick={onDeploy}>✦ REMIX</button></div>
            </div>
          </article>
        ))}
      </div>
      {session && <div className="floating-scan">SESSION {short(session.user_id)} // NETWORK {unlocked ? 'UNLOCKED' : 'LOCKED'}</div>}
    </section>
  );
}

function MediaPreview({ publication }: { publication: Publication }) {
  const src = publication.blur_required && publication.blur_preview_url
    ? api.mediaUrl(publication.blur_preview_url)
    : api.mediaUrl(publication.preview_url || publication.media_url);
  return <div className="signal-media"><img src={src} alt={publication.title || 'Generated publication'} loading="lazy" /></div>;
}

function StudioScreen({
  session,
  workspace,
  setWorkspace,
  tasks,
  setTasks,
  setWallet,
  notify,
}: {
  session: WebSession;
  workspace: Workspace | null;
  setWorkspace: (workspace: Workspace) => void;
  tasks: GenerationTask[];
  setTasks: (tasks: GenerationTask[]) => void;
  setWallet: (wallet: WalletBalance) => void;
  notify: (toast: Toast) => void;
}) {
  const [mode, setMode] = useState<GenerationMode>('image_text_to_image');
  const [prompt, setPrompt] = useState('Cinematic cyberpunk portrait, controlled studio light, chromatic reflections, premium editorial composition');
  const [negative, setNegative] = useState('low quality, distorted anatomy, text artifacts, minors, public figures, non-consensual identity');
  const [aspect, setAspect] = useState('9:16');
  const [resolution, setResolution] = useState('1080p');
  const [duration, setDuration] = useState(5);
  const [audio, setAudio] = useState(true);
  const [referenceUrls, setReferenceUrls] = useState<string[]>([]);
  const [uploadName, setUploadName] = useState('NO REFERENCE LINKED');
  const [launching, setLaunching] = useState(false);
  const imageMode = mode.startsWith('image_');
  const estimate = imageMode ? 35 : duration * 18;

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      setUploadName(`UPLOADING ${file.name.toUpperCase()}...`);
      const result = await api.uploadReference(session.access_token, file);
      setUploadName(`${file.name.toUpperCase()} // ${short(result.asset.id)} STORED`);
      notify({ tone: 'cyan', message: 'REFERENCE // PRIVATE ASSET STORED' });
    } catch (error) {
      setUploadName('UPLOAD FAILED');
      notify({ tone: 'error', message: errorMessage(error) });
    } finally {
      event.target.value = '';
    }
  }

  async function launch() {
    if (prompt.trim().length < 12 || launching) return;
    setLaunching(true);
    try {
      let current = workspace;
      if (!current) {
        current = await api.createWorkspace(session.access_token);
        setWorkspace(current);
      }
      const task = await api.generation(session.access_token, {
        mode, prompt, negativePrompt: negative, aspectRatio: aspect, duration, resolution, audio,
        referenceUrls, projectId: current.project_id, sceneId: current.scene_id,
      });
      setTasks([task, ...tasks.filter((item) => item.id !== task.id)]);
      const balance = await api.wallet(session.access_token);
      setWallet(balance);
      notify({ tone: 'pink', message: `DEPLOYED // ${short(task.id)} // ${task.reserved_credits} CR` });
    } catch (error) {
      notify({ tone: 'error', message: errorMessage(error) });
    } finally {
      setLaunching(false);
    }
  }

  return (
    <section className="screen studio-screen">
      <div className="screen-heading"><div><p className="eyebrow">CONTENT DEPLOYMENT PROTOCOL</p><h1>DEPLOY CONTENT</h1></div><span className="mission-id">MISSION // {workspace ? short(workspace.project_id) : 'UNASSIGNED'}</span></div>
      <div className="deploy-grid">
        <form className="tactical-panel composer" onSubmit={(e) => { e.preventDefault(); void launch(); }}>
          <PanelHeader index="01" title="GENERATION VECTOR" status={imageMode ? 'IMAGE' : 'VIDEO'} />
          <label className="terminal-field"><span>PROMPT / MISSION DIRECTIVE</span><textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={7} /></label>
          <label className="terminal-field"><span>NEGATIVE CONSTRAINTS</span><textarea value={negative} onChange={(e) => setNegative(e.target.value)} rows={3} /></label>
          <div className="mode-grid">
            {([
              ['image_text_to_image', 'T2I'], ['image_to_image', 'I2I'], ['video_text_to_video', 'T2V'],
              ['video_image_to_video_first_frame', 'I2V'], ['video_image_to_video_first_last_frames', 'F/L'], ['video_multimodal_reference_to_video', 'MULTI'],
            ] as [GenerationMode, string][]).map(([value, label]) => (
              <button type="button" className={mode === value ? 'mode-cell active' : 'mode-cell'} key={value} onClick={() => setMode(value)}><span>{label}</span><small>{value.replaceAll('_', ' ')}</small></button>
            ))}
          </div>
          <label className="upload-zone"><input type="file" accept="image/*,video/*" onChange={upload} /><strong>＋ STORE PRIVATE REFERENCE</strong><span>{uploadName}</span></label>
          <label className="terminal-field"><span>PROVIDER REFERENCE URLS // ONE PER LINE</span><textarea rows={3} value={referenceUrls.join('\n')} onChange={(e) => setReferenceUrls(e.target.value.split('\n').map((v) => v.trim()).filter(Boolean))} placeholder="https://..." /></label>
        </form>
        <aside className="tactical-panel parameters">
          <PanelHeader index="02" title="OUTPUT PARAMETERS" status={`${estimate} CR`} />
          <ParamRow label="ASPECT RATIO"><select value={aspect} onChange={(e) => setAspect(e.target.value)}><option>9:16</option><option>16:9</option><option>1:1</option><option>4:3</option></select></ParamRow>
          <ParamRow label="RESOLUTION"><select value={resolution} onChange={(e) => setResolution(e.target.value)}><option>1080p</option><option>720p</option></select></ParamRow>
          {!imageMode && <ParamRow label="DURATION"><input type="range" min="3" max="15" value={duration} onChange={(e) => setDuration(Number(e.target.value))} /><b>{duration} SEC</b></ParamRow>}
          {!imageMode && <ParamRow label="AUDIO"><button type="button" className={audio ? 'toggle on' : 'toggle'} onClick={() => setAudio(!audio)}><i /> {audio ? 'ENABLED' : 'DISABLED'}</button></ParamRow>}
          <div className="cost-readout"><span>RESERVE ESTIMATE</span><strong>{estimate}</strong><small>CREDITS // FINAL CHARGE BY BACKEND LEDGER</small></div>
          <div className="policy-readout"><p>POLICY LAYER</p><span>18+ VERIFIED</span><span>MODERATION ACTIVE</span><span>PRIVATE REFS</span></div>
          <button className="launch-button" disabled={launching || prompt.trim().length < 12} onClick={() => void launch()}>{launching ? 'TRANSMITTING...' : '✦ INITIATE DEPLOYMENT'}</button>
        </aside>
        <section className="tactical-panel recent-missions">
          <PanelHeader index="03" title="RECENT TELEMETRY" status={`${tasks.length} TASKS`} />
          <TaskRows tasks={tasks.slice(0, 5)} />
        </section>
      </div>
    </section>
  );
}

function TelemetryScreen({ session, tasks, setTasks, notify }: { session: WebSession; tasks: GenerationTask[]; setTasks: (tasks: GenerationTask[]) => void; notify: (toast: Toast) => void }) {
  const [selected, setSelected] = useState<GenerationTask | null>(tasks[0] ?? null);
  async function refresh() {
    try {
      const result = await api.generations(session.access_token, 50);
      setTasks(result.items);
      if (selected) setSelected(result.items.find((item) => item.id === selected.id) ?? result.items[0] ?? null);
      else setSelected(result.items[0] ?? null);
      notify({ tone: 'cyan', message: 'TELEMETRY // SYNC COMPLETE' });
    } catch (error) {
      notify({ tone: 'error', message: errorMessage(error) });
    }
  }
  async function refreshSelected() {
    if (!selected) return;
    try {
      const result = await api.generationById(session.access_token, selected.id);
      setSelected(result);
      setTasks([result, ...tasks.filter((task) => task.id !== result.id)]);
    } catch (error) {
      notify({ tone: 'error', message: errorMessage(error) });
    }
  }
  return (
    <section className="screen telemetry-screen">
      <div className="screen-heading"><div><p className="eyebrow">MISSION DETAIL // TELEMETRY LOG</p><h1>GENERATION TELEMETRY</h1></div><button className="terminal-button" onClick={() => void refresh()}>↻ SYNC NETWORK</button></div>
      <div className="telemetry-layout">
        <section className="mission-list tactical-panel"><PanelHeader index="TASK" title="MISSION QUEUE" status={`${tasks.length} SIGNALS`} /><TaskRows tasks={tasks} selectedId={selected?.id} onSelect={setSelected} /></section>
        <section className="mission-detail tactical-panel">
          {selected ? <>
            <div className="detail-hero"><div><span>MISSION ID</span><h2>{selected.id}</h2></div><Status status={selected.status} /></div>
            <div className="telemetry-kpis"><Kpi label="MODEL" value={selected.model_code} /><Kpi label="RESERVED" value={`${selected.reserved_credits} CR`} /><Kpi label="CHARGED" value={`${selected.charged_credits} CR`} /><Kpi label="PROVIDER" value={selected.provider} /></div>
            <div className="log-terminal"><p>&gt; operation: {selected.operation}</p><p>&gt; provider_task: {selected.provider_task_id || 'AWAITING_HANDSHAKE'}</p><p>&gt; status: {selected.status}</p>{selected.error_message && <p className="error-line">&gt; ERROR {selected.error_code}: {selected.error_message}</p>}</div>
            <div className="result-grid">{selected.results.map((asset) => <a key={asset.asset_id} href={api.mediaUrl(asset.media_url)} target="_blank" rel="noreferrer" className="result-asset"><span>{asset.role.toUpperCase()}</span><strong>{short(asset.asset_id)}</strong><small>{asset.is_external ? 'EXTERNAL' : 'STORED'}</small></a>)}{selected.results.length === 0 && <div className="empty-terminal">NO RESULT SIGNALS // CALLBACK PENDING</div>}</div>
            <button className="terminal-button" onClick={() => void refreshSelected()}>REFRESH MISSION</button>
          </> : <div className="empty-terminal big">NO MISSION SELECTED</div>}
        </section>
      </div>
    </section>
  );
}

function ProfileScreen({ session, profile, setProfile, notify }: { session: WebSession; profile: Profile | null; setProfile: (profile: Profile) => void; notify: (toast: Toast) => void }) {
  const [publications, setPublications] = useState<Publication[]>([]);
  const [bio, setBio] = useState(profile?.bio ?? 'Operator profile // autonomous AI media unit');
  useEffect(() => { void api.myPublications(session.access_token).then((result) => setPublications(result.items)).catch(() => undefined); }, [session.access_token]);
  useEffect(() => { if (profile?.bio) setBio(profile.bio); }, [profile?.bio]);
  async function save() {
    try {
      const result = await api.updateProfile(session.access_token, { bio, visibility: profile?.visibility ?? 'public', display_name: session.display_name });
      setProfile(result); notify({ tone: 'pink', message: 'OPERATOR PROFILE // UPDATED' });
    } catch (error) { notify({ tone: 'error', message: errorMessage(error) }); }
  }
  async function toggleVisibility() {
    try {
      const result = await api.updateProfile(session.access_token, { visibility: profile?.visibility === 'public' ? 'private' : 'public' });
      setProfile(result);
    } catch (error) { notify({ tone: 'error', message: errorMessage(error) }); }
  }
  return (
    <section className="screen profile-screen">
      <div className="profile-banner"><div className="grid-sphere" /><div className="profile-identity"><div className="large-avatar">{session.display_name.slice(0, 2).toUpperCase()}</div><div><p>OPERATOR // {profile?.public_id ?? short(session.user_id)}</p><h1>{session.display_name.toUpperCase()}</h1><span>{profile?.visibility?.toUpperCase() ?? 'SYNCING'} PROFILE</span></div></div></div>
      <div className="profile-grid"><section className="tactical-panel profile-data"><PanelHeader index="01" title="OPERATOR DOSSIER" status={profile?.visibility?.toUpperCase() ?? '---'} /><Kpi label="USER ID" value={short(session.user_id)} /><Kpi label="ACCESS" value={session.capabilities.can_generate ? 'DEPLOY ENABLED' : 'RESTRICTED'} /><label className="terminal-field"><span>BIO TRANSMISSION</span><textarea rows={5} value={bio} onChange={(e) => setBio(e.target.value)} /></label><div className="button-row"><button className="terminal-button" onClick={() => void save()}>SAVE DOSSIER</button><button className="terminal-button" onClick={() => void toggleVisibility()}>TOGGLE VISIBILITY</button></div></section>
      <section className="tactical-panel profile-gallery"><PanelHeader index="02" title="PUBLISHED SIGNALS" status={`${publications.length} ITEMS`} /><div className="mini-gallery">{publications.map((publication) => <article key={publication.id}><img src={api.mediaUrl(publication.preview_url || publication.media_url)} alt={publication.title || 'Publication'} /><span>{publication.title || short(publication.id)}</span></article>)}{publications.length === 0 && <div className="empty-terminal big">NO PUBLISHED SIGNALS</div>}</div></section></div>
    </section>
  );
}

function BillingScreen({ session, wallet, setWallet, notify }: { session: WebSession; wallet: WalletBalance | null; setWallet: (wallet: WalletBalance) => void; notify: (toast: Toast) => void }) {
  const [packages, setPackages] = useState<CreditPackage[]>([]);
  const [selected, setSelected] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => { void Promise.all([api.packages().then((result) => { setPackages(result.items); setSelected((value) => value || result.items[0]?.code || ''); }), api.wallet(session.access_token).then(setWallet)]).catch(() => undefined); }, [session.access_token, setWallet]);
  async function checkout() {
    if (!selected || busy) return;
    setBusy(true);
    try {
      const order = await api.createPaymentOrder(session.access_token, selected);
      const result = await api.checkout(session.access_token, order.id);
      window.open(result.redirect_url, '_blank', 'noopener,noreferrer');
      notify({ tone: 'pink', message: `CHECKOUT // ${short(order.id)} OPENED` });
    } catch (error) { notify({ tone: 'error', message: errorMessage(error) }); }
    finally { setBusy(false); }
  }
  return (
    <section className="screen billing-screen"><div className="screen-heading"><div><p className="eyebrow">RESOURCE ALLOCATION</p><h1>CREDIT CORE</h1></div><span className="mission-id">LEDGER // APPEND-ONLY</span></div>
      <div className="wallet-hero"><div><span>AVAILABLE POWER</span><strong>{wallet?.total_available.toLocaleString('ru-RU') ?? '---'}</strong><small>CREDITS</small></div><div className="power-bars">{Array.from({ length: 18 }).map((_, index) => <i key={index} className={wallet && index < Math.min(18, Math.ceil(wallet.total_available / 100)) ? 'on' : ''} />)}</div><p>{wallet?.total_reserved ?? 0} RESERVED // {wallet?.total_balance ?? 0} TOTAL</p></div>
      <div className="package-grid">{packages.map((item) => <button key={item.code} className={selected === item.code ? 'package-card selected' : 'package-card'} onClick={() => setSelected(item.code)}><span>{item.is_popular ? 'POPULAR VECTOR' : 'CREDIT PACK'}</span><strong>{item.credits.toLocaleString('ru-RU')}</strong><small>CREDITS</small><p>{item.title}</p><b>{item.amount_major} {item.currency}</b></button>)}</div>
      <button className="launch-button billing-launch" disabled={!selected || busy} onClick={() => void checkout()}>{busy ? 'OPENING CHANNEL...' : 'INITIATE PAYMENT CHANNEL'}</button>
    </section>
  );
}

function AuthModal({ onClose, onAuthenticated, notify }: { onClose: () => void; onAuthenticated: (session: WebSession) => Promise<void>; notify: (toast: Toast) => void }) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!email.trim() || !name.trim()) return; setBusy(true);
    try { const session = await api.createSession(email.trim(), name.trim()); await onAuthenticated(session); }
    catch (error) { notify({ tone: 'error', message: errorMessage(error) }); }
    finally { setBusy(false); }
  }
  return <div className="modal-layer" role="dialog" aria-modal="true"><form className="auth-modal" onSubmit={(event) => void submit(event)}><button type="button" className="modal-close" onClick={onClose}>×</button><p className="eyebrow">IDENTITY HANDSHAKE</p><h2>INITIALIZE OPERATOR</h2><p>Website session is issued by the existing Core API. No second account database is created in the frontend.</p><label className="terminal-field"><span>EMAIL CHANNEL</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="operator@example.com" autoFocus /></label><label className="terminal-field"><span>CALLSIGN / DISPLAY NAME</span><input value={name} onChange={(event) => setName(event.target.value)} placeholder="OPERATOR_01" /></label><button className="launch-button" disabled={busy || !email.trim() || !name.trim()}>{busy ? 'HANDSHAKE...' : 'CONNECT TO CORE'}</button></form></div>;
}

function AgeGate({ onClose, onAccept }: { onClose: () => void; onAccept: () => void }) {
  return <div className="modal-layer" role="dialog" aria-modal="true"><section className="auth-modal age-modal"><button className="modal-close" onClick={onClose}>×</button><p className="eyebrow">RESTRICTED SECTOR</p><h2>18+ ACCESS GATE</h2><div className="age-number">18+</div><p>Подтверди совершеннолетие и правила платформы. Запрещены несовершеннолетние, сексуализация публичных лиц, не-согласованный интимный контент, принуждение, скрытая камера, насилие и другие категории, блокируемые Core policy.</p><div className="policy-tags"><span>NO MINORS</span><span>CONSENT REQUIRED</span><span>NO PUBLIC FIGURES</span><span>MODERATION ACTIVE</span></div><button className="launch-button" onClick={onAccept}>I AM 18+ // ACCEPT POLICY</button></section></div>;
}

function PanelHeader({ index, title, status }: { index: string; title: string; status: string }) { return <header className="panel-header"><span>{index}</span><h2>{title}</h2><b>{status}</b></header>; }
function ParamRow({ label, children }: { label: string; children: ReactNode }) { return <div className="param-row"><span>{label}</span><div>{children}</div></div>; }
function Kpi({ label, value }: { label: string; value: string }) { return <div className="kpi"><span>{label}</span><strong>{value}</strong></div>; }
function Status({ status }: { status: string }) { return <span className={`status status-${status}`}>● {status.toUpperCase()}</span>; }
function TaskRows({ tasks, selectedId, onSelect }: { tasks: GenerationTask[]; selectedId?: string; onSelect?: (task: GenerationTask) => void }) {
  if (tasks.length === 0) return <div className="empty-terminal">NO MISSIONS TRANSMITTED</div>;
  return <div className="task-rows">{tasks.map((task) => <button key={task.id} className={selectedId === task.id ? 'task-row selected' : 'task-row'} onClick={() => onSelect?.(task)} disabled={!onSelect}><span>{short(task.id)}</span><strong>{task.operation.replaceAll('_', ' ')}</strong><Status status={task.status} /><b>{task.reserved_credits} CR</b></button>)}</div>;
}
function short(value: string) { return value.slice(0, 8).toUpperCase(); }
function errorMessage(error: unknown) { return error instanceof Error ? error.message : 'UNKNOWN CORE ERROR'; }
