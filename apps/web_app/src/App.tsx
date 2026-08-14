import {
  ArrowRight, BadgeCheck, Bookmark, ChevronRight, Clapperboard, Clock3,
  Film, Gauge, Heart, Image, Layers3, LoaderCircle, LockKeyhole, Plus, RefreshCw,
  Rocket, Save, ShieldCheck, Sparkles, Upload, WandSparkles, Zap,
} from 'lucide-react';
import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from 'react';
import {
  coreMediaUrl, createAvatar, createGeneration, createPaymentOrder, createProject, createPublication,
  fetchCreditPackages, fetchFeed, fetchMyGenerations, fetchProfile, fetchWalletBalance,
  importExternalMedia, initiateCrocoPayCheckout, publishResultAsset, savePublication, updateProfile,
  type CreditPackage, type FeedItem, type GenerationResultAsset, type GenerationTask,
  type PaymentOrder, type UserProfile, type WalletBalance, type WebSession,
} from './api';
import { AdultGate, AuthDialog, useTelegramMiniAppBootstrap } from './auth';
import { AppShell, Sidebar, TopBar } from './components/AppShell';
import { useWebRoute } from './hooks/useWebRoute';
import { findRouteByPath, primaryWebAppRoutes, webAppRoutes, type WebAppRoute } from './routes';
import { clearWebSession, loadAdultConsentStatus, loadWebSession } from './session';
import './styles.css';
import './ux-polish.css';

type ModelPreset = {
  code: string;
  name: string;
  family: string;
  operation: string;
  description: string;
  kind: 'image' | 'video';
  credits: string;
};

const modelPresets: ModelPreset[] = [
  { code: 'seedream-5-pro-text-to-image', name: 'Seedream 5 Pro', family: 'Text → image', operation: 'image_text_to_image', description: 'High-detail image generation with strong composition control.', kind: 'image', credits: 'from 12' },
  { code: 'seedream-5-pro-image-to-image', name: 'Seedream Edit', family: 'Image → image', operation: 'image_to_image', description: 'Transform a reference while preserving identity and intent.', kind: 'image', credits: 'from 14' },
  { code: 'seedance-2.0', name: 'Seedance 2.0', family: 'Text / frame → video', operation: 'video_text_to_video', description: 'Cinematic motion, optional audio, references and last-frame return.', kind: 'video', credits: '8 / sec' },
];

const demoCards = [
  { id: 'signal-01', title: 'Afterglow portrait', model: 'Seedream 5 Pro', className: 'visual-one', ratio: 'tall' },
  { id: 'signal-02', title: 'Liquid chrome study', model: 'Seedream Edit', className: 'visual-two', ratio: 'wide' },
  { id: 'signal-03', title: 'Neon silhouette', model: 'Seedance 2.0', className: 'visual-three', ratio: 'square' },
  { id: 'signal-04', title: 'Velvet room', model: 'Seedream 5 Pro', className: 'visual-four', ratio: 'tall' },
  { id: 'signal-05', title: 'Midnight movement', model: 'Seedance 2.0', className: 'visual-five', ratio: 'wide' },
  { id: 'signal-06', title: 'Electric bloom', model: 'Seedream Edit', className: 'visual-six', ratio: 'square' },
];

export function App() {
  const { route: activeRoute, navigate } = useWebRoute();
  const [session, setSession] = useState<WebSession | null>(() => loadWebSession());
  const [adultAccepted, setAdultAccepted] = useState(() => loadAdultConsentStatus()?.accepted === true);
  const [authOpen, setAuthOpen] = useState(false);
  const [walletBalance, setWalletBalance] = useState<WalletBalance | null>(null);
  const [generationTasks, setGenerationTasks] = useState<GenerationTask[]>([]);
  const [creditPackages, setCreditPackages] = useState<CreditPackage[]>([]);
  const [selectedPackageCode, setSelectedPackageCode] = useState('');
  const [latestPaymentOrder, setLatestPaymentOrder] = useState<PaymentOrder | null>(null);
  const [latestCheckout, setLatestCheckout] = useState<string | null>(null);
  const [notice, setNotice] = useState('');

  const onAuthenticated = useCallback((next: WebSession) => {
    setSession(next);
    setAdultAccepted(false);
    setAuthOpen(false);
  }, []);
  useTelegramMiniAppBootstrap(onAuthenticated);

  useEffect(() => {
    if (!session) return;
    fetchWalletBalance(session.access_token).then(setWalletBalance).catch(() => setWalletBalance(null));
  }, [session]);

  useEffect(() => {
    if (!session || activeRoute.id !== 'billing') return;
    let ignore = false;
    fetchWalletBalance(session.access_token)
      .then((result) => { if (!ignore) setWalletBalance(result); })
      .catch(() => { if (!ignore) setWalletBalance(null); });
    return () => { ignore = true; };
  }, [session, activeRoute.id]);

  useEffect(() => {
    if (!session || !adultAccepted) return;
    let ignore = false;
    fetchMyGenerations(session.access_token)
      .then((result) => { if (!ignore) setGenerationTasks(result.items); })
      .catch(() => { if (!ignore) setGenerationTasks([]); });
    return () => { ignore = true; };
  }, [session, adultAccepted, activeRoute.id]);

  useEffect(() => {
    if (activeRoute.id !== 'billing') return;
    let ignore = false;
    fetchCreditPackages()
      .then((result) => {
        if (!ignore) {
          setCreditPackages(result.items);
          setSelectedPackageCode((current) => current || result.items[0]?.code || '');
        }
      })
      .catch(() => { if (!ignore) setCreditPackages([]); });
    return () => { ignore = true; };
  }, [activeRoute.id]);

  const routeResolver = (id: WebAppRoute['id']) => webAppRoutes.find((route) => route.id === id) || webAppRoutes[0];
  const protectedWithoutSession = activeRoute.protected && !session;
  const handleNavigate = (route: WebAppRoute) => {
    navigate(route);
    if (route.protected && !session) setAuthOpen(true);
  };
  const goStudio = () => handleNavigate(routeResolver('studio'));
  const signOut = () => {
    clearWebSession();
    setSession(null);
    setAdultAccepted(false);
    setWalletBalance(null);
    navigate(webAppRoutes[0]);
  };

  const refreshWallet = async () => {
    if (!session) return;
    const next = await fetchWalletBalance(session.access_token);
    setWalletBalance(next);
  };

  const handleCreatePaymentOrder = async () => {
    if (!session || !selectedPackageCode) return;
    try {
      const order = await createPaymentOrder(session.access_token, selectedPackageCode);
      setLatestPaymentOrder(order);
      setLatestCheckout(null);
    } catch (reason) { setNotice(reason instanceof Error ? reason.message : 'Could not create order'); }
  };

  const handleStartCrocoPayCheckout = async () => {
    if (!session || !latestPaymentOrder) return;
    try {
      const result = await initiateCrocoPayCheckout(session.access_token, latestPaymentOrder.id);
      setLatestCheckout(result.redirect_url);
      window.open(result.redirect_url, '_blank', 'noopener,noreferrer');
    } catch (reason) { setNotice(reason instanceof Error ? reason.message : 'Could not start checkout'); }
  };

  return (
    <AppShell
      sidebar={<Sidebar routes={primaryWebAppRoutes} activeRoute={activeRoute} routeResolver={routeResolver} onNavigate={handleNavigate} onCreate={goStudio} />}
      topbar={<TopBar activeRoute={activeRoute} routes={webAppRoutes} session={session} balance={walletBalance?.total_available ?? null} onNavigate={handleNavigate} onSignIn={() => setAuthOpen(true)} onSignOut={signOut} />}
    >
      <header className="page-heading">
        <div><p className="eyebrow">{activeRoute.eyebrow}</p><h2>{activeRoute.title}</h2></div>
        {session && <span className="online-state"><i /> SYSTEM READY</span>}
      </header>

      {protectedWithoutSession ? <LockedScreen onSignIn={() => setAuthOpen(true)} /> : (
        <RouteScreen
          route={activeRoute}
          session={session}
          wallet={walletBalance}
          tasks={generationTasks}
          creditPackages={creditPackages}
          selectedPackageCode={selectedPackageCode}
          latestPaymentOrder={latestPaymentOrder}
          latestCheckout={latestCheckout}
          onSelectPackage={setSelectedPackageCode}
          onCreateOrder={handleCreatePaymentOrder}
          onCheckout={handleStartCrocoPayCheckout}
          onSignIn={() => setAuthOpen(true)}
          onNavigate={handleNavigate}
          onTasksChange={setGenerationTasks}
          onNotice={setNotice}
          onRefreshWallet={refreshWallet}
        />
      )}

      {authOpen && <AuthDialog onClose={() => setAuthOpen(false)} onAuthenticated={onAuthenticated} />}
      {session && !adultAccepted && <AdultGate session={session} onAccepted={() => setAdultAccepted(true)} />}
      {notice && <button className="toast" onClick={() => setNotice('')} aria-label="Закрыть уведомление">{notice}</button>}
    </AppShell>
  );
}

function RouteScreen(props: {
  route: WebAppRoute;
  session: WebSession | null;
  wallet: WalletBalance | null;
  tasks: GenerationTask[];
  creditPackages: CreditPackage[];
  selectedPackageCode: string;
  latestPaymentOrder: PaymentOrder | null;
  latestCheckout: string | null;
  onSelectPackage: (code: string) => void;
  onCreateOrder: () => void;
  onCheckout: () => void;
  onSignIn: () => void;
  onNavigate: (route: WebAppRoute) => void;
  onTasksChange: (tasks: GenerationTask[]) => void;
  onNotice: (message: string) => void;
  onRefreshWallet: () => Promise<void>;
}) {
  switch (props.route.id) {
    case 'discover': return <DiscoverScreen session={props.session} onSignIn={props.onSignIn} onNavigate={props.onNavigate} />;
    case 'studio': return <StudioScreen session={props.session!} tasks={props.tasks} onTasksChange={props.onTasksChange} onNotice={props.onNotice} onRefreshWallet={props.onRefreshWallet} />;
    case 'generations': return <GenerationResultsPanel session={props.session!} tasks={props.tasks} onNotice={props.onNotice} />;
    case 'projects': return <ProjectsScreen session={props.session!} onNavigate={props.onNavigate} onNotice={props.onNotice} />;
    case 'avatars': return <AvatarsScreen session={props.session!} onNotice={props.onNotice} />;
    case 'billing': return <BillingCard {...props} />;
    case 'profile': return <ProfileScreen session={props.session!} onNotice={props.onNotice} />;
  }
}

function LockedScreen({ onSignIn }: { onSignIn: () => void }) {
  return <section className="locked-screen"><LockKeyhole /><p className="eyebrow">PRIVATE WORKSPACE</p><h3>Sign in to continue</h3><p>Your projects, references and generations remain private by default.</p><button className="primary-action" onClick={onSignIn}>Secure sign in <ArrowRight size={17} /></button></section>;
}

function DiscoverScreen({ session, onSignIn, onNavigate }: { session: WebSession | null; onSignIn: () => void; onNavigate: (route: WebAppRoute) => void }) {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [tab, setTab] = useState('Featured');
  const refreshFeed = () => fetchFeed().then((result) => setItems(result.items)).catch(() => setItems([]));
  useEffect(() => { void refreshFeed(); }, []);
  const publishLastUpload = async () => {
    if (!session) return onSignIn();
    const assetId = window.sessionStorage.getItem('adultgen.last-upload-id');
    if (assetId) await createPublication(session.access_token, assetId, 'profile');
  };
  const saveFirst = async () => {
    if (!session) return onSignIn();
    if (items[0]) await savePublication(session.access_token, items[0].id);
  };
  const studioRoute = webAppRoutes.find((route) => route.id === 'studio')!;
  return (
    <>
      <section className="landing-grid">
        <div className="hero-copy">
          <span className="signal-badge"><i /> CREATOR ENGINE ONLINE</span>
          <h1>Build the scene<br /><em>you imagined.</em></h1>
          <p>Controlled AI image and cinematic video creation. Private by default, designed for adult creators.</p>
          <div className="hero-actions"><button className="primary-action" onClick={() => session ? onNavigate(studioRoute) : onSignIn()}><WandSparkles size={18} /> Start creating</button><a className="text-action" href="#signal-feed">Explore the feed <ArrowRight size={16} /></a></div>
        </div>
        <div className="hero-orbit" aria-hidden="true"><div className="orbit-core"><Sparkles /></div><span className="orbit orbit-a" /><span className="orbit orbit-b" /><span className="orbit orbit-c" /><small>SEEDREAM / SEEDANCE</small></div>
      </section>
      <section id="signal-feed" className="feed-section">
        <div className="section-bar"><div><p className="eyebrow">PUBLIC SIGNAL</p><h3>Made with AdultGen</h3></div><div className="tab-list">{['Featured', 'Trending', 'Motion'].map((name) => <button className={tab === name ? 'active' : ''} key={name} onClick={() => setTab(name)}>{name}</button>)}</div></div>
        <div className="feed-operations"><button onClick={() => void refreshFeed()}>Обновить ленту</button><button onClick={() => void publishLastUpload()}>Опубликовать последний upload</button><button onClick={() => void saveFirst()}>В коллекцию</button></div>
        <div className="masonry-feed">
          {items.length ? items.map((item, index) => <ApiMediaCard item={item} key={item.id} index={index} />) : demoCards.map((card) => <DemoMediaCard card={card} key={card.id} />)}
        </div>
      </section>
    </>
  );
}

function DemoMediaCard({ card }: { card: (typeof demoCards)[number] }) {
  return <article className={`media-card ${card.ratio}`}><div className={`demo-visual ${card.className}`}><div className="visual-grain" /><span className="safe-preview"><ShieldCheck size={14} /> SAFE PREVIEW</span></div><div className="media-meta"><div><h4>{card.title}</h4><p>{card.model}</p></div><div className="card-actions"><button aria-label="Нравится"><Heart size={17} /></button><button aria-label="Сохранить"><Bookmark size={17} /></button></div></div></article>;
}

function ApiMediaCard({ item, index }: { item: FeedItem; index: number }) {
  const src = coreMediaUrl(item.blur_required ? item.blur_preview_url || item.preview_url : item.preview_url);
  return <article className={`media-card ${index % 3 === 0 ? 'tall' : index % 3 === 1 ? 'wide' : 'square'}`}><div className="api-visual"><img src={src} alt={item.title || 'AdultGen creation'} loading="lazy" />{item.blur_required && <span className="safe-preview"><ShieldCheck size={14} /> 18+ BLURRED</span>}</div><div className="media-meta"><div><h4>{item.title || 'Untitled signal'}</h4><p>{item.allow_remix ? 'Remix enabled' : 'Creator original'}</p></div><div className="card-actions"><button aria-label="Нравится"><Heart size={17} /></button><button aria-label="Сохранить"><Bookmark size={17} /></button></div></div></article>;
}

function StudioScreen({ session, tasks, onTasksChange, onNotice, onRefreshWallet }: { session: WebSession; tasks: GenerationTask[]; onTasksChange: (tasks: GenerationTask[]) => void; onNotice: (message: string) => void; onRefreshWallet: () => Promise<void> }) {
  const [modelCode, setModelCode] = useState(modelPresets[0].code);
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [duration, setDuration] = useState(10);
  const [resolution, setResolution] = useState('720p');
  const [referenceUrl, setReferenceUrl] = useState('');
  const [operation, setOperation] = useState(modelPresets[0].operation);
  const [busy, setBusy] = useState(false);
  const selectedModel = modelPresets.find((model) => model.code === modelCode) || modelPresets[0];
  const isVideo = selectedModel.kind === 'video';
  const needsReference = operation === 'image_to_image' || operation.includes('first_frame');

  useEffect(() => { setOperation(selectedModel.operation); setReferenceUrl(''); }, [selectedModel]);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!prompt.trim()) return;
    setBusy(true);
    const requestPayload: Record<string, unknown> = { prompt: prompt.trim(), aspect_ratio: aspectRatio };
    if (isVideo) Object.assign(requestPayload, { duration, resolution, return_last_frame: true });
    if (operation === 'image_to_image') requestPayload.image_urls = [referenceUrl];
    if (operation.includes('first_frame')) requestPayload.first_frame_url = referenceUrl;
    try {
      const task = await createGeneration(session.access_token, { model_code: modelCode, operation, request_payload: requestPayload });
      onTasksChange([task, ...tasks]);
      setPrompt('');
      await onRefreshWallet();
      onNotice('Generation queued');
    } catch (reason) { onNotice(reason instanceof Error ? reason.message : 'Generation failed'); }
    finally { setBusy(false); }
  };

  return (
    <form className="studio-grid" onSubmit={submit}>
      <section className="model-rail panel"><div className="panel-title"><Layers3 size={17} /><span>MODEL MATRIX</span></div>{modelPresets.map((model) => <button type="button" key={model.code} className={`model-option ${modelCode === model.code ? 'selected' : ''}`} onClick={() => setModelCode(model.code)}><span className="model-icon">{model.kind === 'video' ? <Film /> : <Image />}</span><span><strong>{model.name}</strong><small>{model.family}</small></span><i /></button>)}</section>
      <section className="composer-panel panel">
        <div className="composer-head"><div><p className="eyebrow">PROMPT SEQUENCE</p><h3>{selectedModel.name}</h3><p>{selectedModel.description}</p></div><span className="cost-chip"><Zap size={15} /> {selectedModel.credits} credits</span></div>
        <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Describe the adult scene, lighting, composition, mood and camera intent…" maxLength={4000} />
        <div className="prompt-toolbar"><button type="button"><Sparkles size={15} /> Enhance prompt</button><span>{prompt.length} / 4000</span></div>
        {isVideo && <div className="mode-tabs"><button type="button" className={operation === 'video_text_to_video' ? 'active' : ''} onClick={() => setOperation('video_text_to_video')}>Text</button><button type="button" className={operation === 'video_image_to_video_first_frame' ? 'active' : ''} onClick={() => setOperation('video_image_to_video_first_frame')}>First frame</button><button type="button" className={operation === 'video_image_to_video_first_last_frames' ? 'active' : ''} onClick={() => setOperation('video_image_to_video_first_last_frames')}>Frame pair</button></div>}
        {needsReference && <label className="reference-zone"><Upload size={24} /><strong>Reference input</strong><span>Paste an uploaded media URL for this backend contract</span><input aria-label="Reference URL" value={referenceUrl} onChange={(event) => setReferenceUrl(event.target.value)} placeholder="https://…" required /></label>}
        <div className="recent-strip"><div className="section-bar compact"><div><p className="eyebrow">RECENT OUTPUT</p><h4>{tasks.length ? 'Your latest signals' : 'No generations yet'}</h4></div></div>{tasks.slice(0, 3).map((task) => <div className="mini-task" key={task.id}><span className={`status-dot ${task.status}`} /><span>{task.model_code}</span><strong>{task.status.replace('_', ' ')}</strong></div>)}</div>
      </section>
      <aside className="parameter-panel panel"><div className="panel-title"><Gauge size={17} /><span>PARAMETERS</span></div><label>Aspect ratio<select value={aspectRatio} onChange={(event) => setAspectRatio(event.target.value)}>{(isVideo ? ['9:16', '16:9', '1:1'] : ['9:16', '16:9', '1:1', '4:3', '3:4']).map((ratio) => <option key={ratio}>{ratio}</option>)}</select></label>{isVideo && <><label>Duration<select value={duration} onChange={(event) => setDuration(Number(event.target.value))}>{[5, 10, 15].map((value) => <option value={value} key={value}>{value} seconds</option>)}</select></label><label>Resolution<select value={resolution} onChange={(event) => setResolution(event.target.value)}>{['480p', '720p', '1080p'].map((value) => <option key={value}>{value}</option>)}</select></label></>}<div className="launch-summary"><div><span>Estimated cost</span><strong>{isVideo ? duration * 8 : selectedModel.code.includes('image-to-image') ? 14 : 12} credits</strong></div><p><ShieldCheck size={14} /> Safety checks run before provider submission.</p><button className="primary-action full" disabled={busy || !prompt.trim() || (needsReference && !referenceUrl)}>{busy ? <LoaderCircle className="spin" /> : <Rocket size={18} />}{busy ? 'Launching…' : 'Generate'}</button></div></aside>
    </form>
  );
}

function GenerationResultsPanel({ session, tasks, onNotice }: { session: WebSession; tasks: GenerationTask[]; onNotice: (message: string) => void }) {
  const onImportResultAsset = async (asset: GenerationResultAsset) => { try { await importExternalMedia(session.access_token, asset.asset_id); onNotice('Media imported'); } catch (reason) { onNotice(reason instanceof Error ? reason.message : 'Import failed'); } };
  const onPublishResultAsset = async (asset: GenerationResultAsset) => { try { await publishResultAsset(session.access_token, asset.asset_id); onNotice('Published to private profile'); } catch (reason) { onNotice(reason instanceof Error ? reason.message : 'Publish failed'); } };
  return <section className="results-panel"><div className="queue-summary panel"><div><p className="eyebrow">QUEUE TELEMETRY</p><h3>{tasks.length} generation{tasks.length === 1 ? '' : 's'}</h3></div><div className="metric"><span>PROCESSING</span><strong>{tasks.filter((task) => task.status.includes('processing') || task.status === 'queued').length}</strong></div><div className="metric"><span>COMPLETE</span><strong>{tasks.filter((task) => task.status === 'completed').length}</strong></div></div>{tasks.length ? <div className="generation-grid">{tasks.map((task) => <GenerationTaskCard task={task} key={task.id} onImportResultAsset={onImportResultAsset} onPublishResultAsset={onPublishResultAsset} />)}</div> : <EmptyState icon={<Clapperboard />} title="No generations yet" text="Launch your first sequence from Create." />}</section>;
}

function GenerationTaskCard({ task, onImportResultAsset, onPublishResultAsset }: { task: GenerationTask; onImportResultAsset: (asset: GenerationResultAsset) => void; onPublishResultAsset: (asset: GenerationResultAsset) => void }) {
  return <article className="generation-card panel"><div className="generation-card-head"><div><span className={`task-status ${task.status}`}>{task.status.replace('_', ' ')}</span><h3>{task.model_code}</h3><p>{task.operation.replaceAll('_', ' ')}</p></div><button className="icon-button" aria-label="Refresh"><RefreshCw size={17} /></button></div><div className="generation-cost"><span><Clock3 size={14} /> Provider: {task.provider}</span><strong>{task.charged_credits || task.reserved_credits} credits</strong></div>{task.error_message && <p className="error-banner">{task.error_message}</p>}<ResultAssetList assets={task.results} onImportResultAsset={onImportResultAsset} onPublishResultAsset={onPublishResultAsset} /></article>;
}

function ResultAssetList({ assets, onImportResultAsset, onPublishResultAsset }: { assets: GenerationResultAsset[]; onImportResultAsset: (asset: GenerationResultAsset) => void; onPublishResultAsset: (asset: GenerationResultAsset) => void }) {
  if (!assets.length) return <div className="result-placeholder"><LoaderCircle className="spin-slow" /><span>Awaiting provider result</span></div>;
  return <div className="result-list">{assets.map((asset) => <div className="result-card" key={`${asset.asset_id}:${asset.role}`}><div className="result-preview"><img src={asset.media_url} alt={`Generation ${asset.role}`} /></div><div><span>{asset.role}</span>{asset.is_external && <button onClick={() => onImportResultAsset(asset)}>Импортировать</button>}<button onClick={() => onPublishResultAsset(asset)}>Опубликовать</button></div></div>)}</div>;
}

function ProjectsScreen({ session, onNavigate, onNotice }: { session: WebSession; onNavigate: (route: WebAppRoute) => void; onNotice: (message: string) => void }) {
  const [title, setTitle] = useState('');
  const submit = async (event: FormEvent) => { event.preventDefault(); try { await createProject(session.access_token, { title, output_format: '9:16' }); setTitle(''); onNotice('Project created'); } catch (reason) { onNotice(reason instanceof Error ? reason.message : 'Could not create project'); } };
  return <div className="project-layout"><section className="feature-panel panel"><p className="eyebrow">STORY WORKSPACE</p><h3>Проекты и сцены</h3><p>Group prompts, references and takes into a repeatable visual sequence.</p><div className="project-visual"><Layers3 /><span>SCENE GRAPH</span></div><button className="primary-action" onClick={() => onNavigate(findRouteByPath('/studio'))}>Открыть Studio <ArrowRight size={17} /></button></section><form className="create-card panel" onSubmit={submit}><span className="card-number">01</span><h3>New project</h3><p>Start with a private 9:16 scene board.</p><label>Project title<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Midnight sequence" required /></label><button className="secondary-action"><Plus size={17} /> Create project</button></form></div>;
}

function AvatarsScreen({ session, onNotice }: { session: WebSession; onNotice: (message: string) => void }) {
  const [name, setName] = useState('');
  const submit = async (event: FormEvent) => { event.preventDefault(); try { await createAvatar(session.access_token, name); setName(''); onNotice('Private avatar created'); } catch (reason) { onNotice(reason instanceof Error ? reason.message : 'Could not create avatar'); } };
  return <div className="assets-grid"><section className="feature-panel panel"><p className="eyebrow">IDENTITY VAULT</p><h3>Аватары и visual identity</h3><p>Private reference sets help keep a character consistent across scenes. Real-person non-consensual sexualization is prohibited.</p><label className="asset-drop" aria-label="Reference upload"><Upload /><strong>Drop reference files</strong><span>Upload wiring uses the private media endpoint</span><input type="file" accept="image/*" multiple /></label></section><form className="create-card panel" onSubmit={submit}><span className="card-number">ID</span><h3>Create identity</h3><label>Avatar name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="Private character name" required /></label><button className="primary-action"><Plus size={17} /> Add avatar</button></form></div>;
}

function BillingCard({ session, wallet, creditPackages, selectedPackageCode, latestPaymentOrder, latestCheckout, onSelectPackage, onCreateOrder, onCheckout, onRefreshWallet }: { session: WebSession | null; wallet: WalletBalance | null; creditPackages: CreditPackage[]; selectedPackageCode: string; latestPaymentOrder: PaymentOrder | null; latestCheckout: string | null; onSelectPackage: (code: string) => void; onCreateOrder: () => void; onCheckout: () => void; onRefreshWallet: () => Promise<void> }) {
  if (!session) return null;
  return <div className="billing-grid"><WalletBalanceCard walletBalance={wallet} onRefresh={onRefreshWallet} /><section className="package-panel panel"><div className="section-bar compact"><div><p className="eyebrow">TOP UP</p><h3>Choose a credit pack</h3></div><BadgeCheck /></div>{creditPackages.length ? <div className="package-grid">{creditPackages.map((pack) => <button className={`package-card ${selectedPackageCode === pack.code ? 'selected' : ''}`} onClick={() => onSelectPackage(pack.code)} key={pack.code}><span>{pack.is_popular ? 'POPULAR' : 'CREDITS'}</span><strong>{pack.credits}</strong><small>{pack.title}</small><b>{pack.amount_major} {pack.currency}</b></button>)}</div> : <EmptyState icon={<CreditCardFallback />} title="Packages unavailable" text="Billing API returned no enabled packages." />}<button className="primary-action" disabled={!selectedPackageCode} onClick={onCreateOrder}>Create secure order <ChevronRight /></button></section>{latestPaymentOrder && <section className="payment-order-card panel"><p className="eyebrow">PAYMENT ORDER</p><h3>{latestPaymentOrder.credits_amount} credits</h3><p>Order {latestPaymentOrder.id.slice(0, 8)} · {latestPaymentOrder.status}</p><button className="secondary-action" onClick={onCheckout}>Continue with CrocoPay <ArrowRight /></button>{latestCheckout && <a className="checkout-link" href={latestCheckout} target="_blank" rel="noreferrer">Open checkout again</a>}</section>}</div>;
}

function WalletBalanceCard({ walletBalance, onRefresh }: { walletBalance: WalletBalance | null; onRefresh: () => Promise<void> }) {
  return <section className="wallet-card panel"><div><p className="eyebrow">AVAILABLE BALANCE</p><strong>{walletBalance?.total_available ?? 0}</strong><span>credits</span></div><div className="wallet-signal"><i /><i /><i /><i /><i /></div><p>Available: {walletBalance?.total_available ?? 0} · Reserved: {walletBalance?.total_reserved ?? 0}</p><button className="wallet-refresh" onClick={() => void onRefresh()}><RefreshCw size={14} /> Обновить баланс</button></section>;
}

function CreditCardFallback() { return <Zap />; }

function ProfileScreen({ session, onNotice }: { session: WebSession; onNotice: (message: string) => void }) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [name, setName] = useState(session.display_name);
  const [bio, setBio] = useState('');
  const [visibility, setVisibility] = useState<'public' | 'private'>('private');
  useEffect(() => { fetchProfile(session.access_token).then((value) => { setProfile(value); setName(value.display_name || session.display_name); setBio(value.bio || ''); setVisibility(value.visibility); }).catch(() => undefined); }, [session]);
  const submit = async (event: FormEvent) => { event.preventDefault(); try { const next = await updateProfile(session.access_token, { display_name: name, bio, visibility }); setProfile(next); onNotice('Profile synchronized'); } catch (reason) { onNotice(reason instanceof Error ? reason.message : 'Profile update failed'); } };
  return <div className="profile-grid"><section className="profile-identity panel"><div className="profile-avatar">{name.slice(0, 1).toUpperCase()}</div><p className="eyebrow">CREATOR ID</p><h3>{name}</h3><span>@{profile?.public_id || 'private-signal'}</span><div className="profile-stats"><div><strong>0</strong><span>CREATIONS</span></div><div><strong>0</strong><span>SAVES</span></div><div><strong>{visibility === 'public' ? 'OPEN' : 'LOCKED'}</strong><span>PROFILE</span></div></div></section><form className="profile-form panel" onSubmit={submit}><div className="panel-title"><Save /><span>PROFILE SETTINGS</span></div><label>Display name<input value={name} onChange={(event) => setName(event.target.value)} /></label><label>Bio<textarea value={bio} onChange={(event) => setBio(event.target.value)} maxLength={500} /></label><label>Visibility<select value={visibility} onChange={(event) => setVisibility(event.target.value as 'public' | 'private')}><option value="private">Private</option><option value="public">Public</option></select></label><button className="primary-action">Save profile</button></form></div>;
}

function EmptyState({ icon, title, text }: { icon: ReactNode; title: string; text: string }) { return <div className="empty-state">{icon}<h3>{title}</h3><p>{text}</p></div>; }
