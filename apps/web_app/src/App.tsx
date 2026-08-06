import { useEffect, useMemo, useState, type ChangeEvent } from 'react';

import {
  acceptAdultConsent,
  coreMediaUrl,
  createGenerationTask,
  createPaymentOrder,
  createPublication,
  createStarterWorkspace,
  createWebSession,
  fetchAdultConsent,
  fetchCreditPackages,
  fetchFeed,
  fetchGenerationTask,
  fetchMyGenerations,
  fetchMyProfile,
  fetchMyPublications,
  fetchSavedCollection,
  fetchWalletBalance,
  importExternalMedia,
  initiateCrocoPayCheckout,
  savePublication,
  updateMyProfile,
  uploadReferenceMedia,
  uploadTemporaryMedia,
  type AdultConsentStatus,
  type CreditPackage,
  type FeedResponse,
  type GenerationMode,
  type GenerationResultAsset,
  type GenerationTask,
  type MediaAsset,
  type PaymentOrder,
  type Profile,
  type Publication,
  type PublicationVisibility,
  type ProviderCheckoutResponse,
  type WalletBalance,
  type WebSession,
} from './api';
import { findRouteByPath, primaryWebAppRoutes, webAppRoutes, type WebAppRoute } from './routes';
import {
  clearWebSession,
  loadAdultConsentStatus,
  loadWebSession,
  saveAdultConsentStatus,
  saveWebSession,
} from './session';

type WorkspaceDraft = { avatar_id: string; project_id: string; scene_id: string };

type StudioState = {
  mode: GenerationMode;
  prompt: string;
  negative_prompt: string;
  duration_seconds: number;
  aspect_ratio: string;
  resolution: string;
  generate_audio: boolean;
  reference_urls: string;
};

const defaultStudioState: StudioState = {
  mode: 'video_image_to_video_first_frame',
  prompt: 'Cinematic adult AI scene, realistic lighting, controlled composition, premium editorial look.',
  negative_prompt: 'minors, public figures, non-consensual identity, violence, coercion, hidden camera, low quality',
  duration_seconds: 5,
  aspect_ratio: '9:16',
  resolution: '1080p',
  generate_audio: true,
  reference_urls: '',
};

const secondaryWebAppRoutes = webAppRoutes.filter(
  (route) => !route.isPrimary && route.id !== 'landing' && route.id !== 'ageGate',
);

function resolveRoute(routeId: WebAppRoute['id']): WebAppRoute {
  return webAppRoutes.find((route) => route.id === routeId) ?? webAppRoutes[0];
}

export function App() {
  const initialRoute = useMemo(() => findRouteByPath(window.location.pathname), []);
  const [activeRoute, setActiveRoute] = useState<WebAppRoute>(initialRoute);
  const [session, setSession] = useState<WebSession | null>(() => loadWebSession());
  const [adultConsent, setAdultConsent] = useState<AdultConsentStatus | null>(() => loadAdultConsentStatus());
  const [workspace, setWorkspace] = useState<WorkspaceDraft | null>(null);
  const [latestTask, setLatestTask] = useState<GenerationTask | null>(null);
  const [generationTasks, setGenerationTasks] = useState<GenerationTask[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [studio, setStudio] = useState<StudioState>(defaultStudioState);
  const [uploadedAssets, setUploadedAssets] = useState<MediaAsset[]>([]);
  const [myPublications, setMyPublications] = useState<Publication[]>([]);
  const [feed, setFeed] = useState<FeedResponse>({ items: [] });
  const [savedItems, setSavedItems] = useState<{ publication_id: string; saved_at: string }[]>([]);
  const [creditPackages, setCreditPackages] = useState<CreditPackage[]>([]);
  const [selectedPackageCode, setSelectedPackageCode] = useState('creator_1500');
  const [latestPaymentOrder, setLatestPaymentOrder] = useState<PaymentOrder | null>(null);
  const [latestCheckout, setLatestCheckout] = useState<ProviderCheckoutResponse | null>(null);
  const [walletBalance, setWalletBalance] = useState<WalletBalance | null>(null);
  const [email, setEmail] = useState('creator@example.com');
  const [displayName, setDisplayName] = useState('AdultGen creator');
  const [publishTitle, setPublishTitle] = useState('Web Studio result');
  const [publishDescription, setPublishDescription] = useState('Generated and published from AdultGen website app.');
  const [publishVisibility, setPublishVisibility] = useState<PublicationVisibility>('feed');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const routeBlockedByAuth = activeRoute.requiresAuth && !session;
  const routeBlockedByAge = activeRoute.requiresAdultConsent && !adultConsent?.accepted;

  function navigate(route: WebAppRoute) {
    setActiveRoute(route);
    if (window.location.pathname !== route.path) {
      window.history.replaceState(null, '', route.path);
    }
  }

  useEffect(() => {
    if (!session || !adultConsent?.accepted) return;

    let ignore = false;
    fetchMyGenerations(session.access_token)
      .then((result) => {
        if (!ignore) setGenerationTasks(result.items);
      })
      .catch(() => {
        if (!ignore) setGenerationTasks([]);
      });

    return () => {
      ignore = true;
    };
  }, [session, adultConsent?.accepted]);

  useEffect(() => {
    if (activeRoute.id !== 'billing') return;

    let ignore = false;
    fetchCreditPackages()
      .then((result) => {
        if (!ignore) {
          setCreditPackages(result.items);
          if (!result.items.some((item) => item.code === selectedPackageCode)) {
            setSelectedPackageCode(result.items[0]?.code ?? 'creator_1500');
          }
        }
      })
      .catch(() => {
        if (!ignore) setCreditPackages([]);
      });

    return () => {
      ignore = true;
    };
  }, [activeRoute.id, selectedPackageCode]);

  useEffect(() => {
    if (!session || activeRoute.id !== 'billing') return;

    let ignore = false;
    fetchWalletBalance(session.access_token)
      .then((result) => {
        if (!ignore) setWalletBalance(result);
      })
      .catch(() => {
        if (!ignore) setWalletBalance(null);
      });

    return () => {
      ignore = true;
    };
  }, [session, activeRoute.id]);

  async function runAction<T>(message: string, action: () => Promise<T>): Promise<T | null> {
    setStatusMessage(message);
    setErrorMessage(null);
    try {
      const result = await action();
      setStatusMessage('Готово.');
      return result;
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unknown error.');
      setStatusMessage(null);
      return null;
    }
  }

  async function handleLogin() {
    const result = await runAction('Создаём web-сессию…', () => createWebSession(email, displayName));
    if (!result) return;
    saveWebSession(result);
    setSession(result);
    navigate(resolveRoute('ageGate'));
  }

  async function handleAcceptAdultConsent() {
    if (!session) return;
    const result = await runAction('Фиксируем подтверждение 18+…', () => acceptAdultConsent(session.access_token));
    if (!result) return;
    saveAdultConsentStatus(result);
    setAdultConsent(result);
    navigate(resolveRoute('studio'));
  }

  async function handleRefreshConsent() {
    if (!session) return;
    const result = await runAction('Проверяем consent…', () => fetchAdultConsent(session.access_token));
    if (!result) return;
    saveAdultConsentStatus(result);
    setAdultConsent(result);
  }

  async function handlePrepareWorkspace() {
    if (!session) return;
    const result = await runAction('Создаём аватар, проект и первую сцену…', () =>
      createStarterWorkspace(session.access_token),
    );
    if (result) setWorkspace(result);
  }

  async function handleLaunchGeneration() {
    if (!session) return;
    const refs = studio.reference_urls
      .split('\n')
      .map((item) => item.trim())
      .filter(Boolean);
    const result = await runAction('Резервируем кредиты и создаём generation task…', () =>
      createGenerationTask(session.access_token, {
        ...studio,
        reference_urls: refs,
        avatar_id: workspace?.avatar_id,
        project_id: workspace?.project_id,
        scene_id: workspace?.scene_id,
      }),
    );
    if (!result) return;
    setLatestTask(result);
    setGenerationTasks((items) => [result, ...items.filter((item) => item.id !== result.id)]);
    await refreshWalletBalance();
  }

  async function handleRefreshLatestTask() {
    if (!session || !latestTask) return;
    const result = await runAction('Обновляем статус последней задачи…', () =>
      fetchGenerationTask(session.access_token, latestTask.id),
    );
    if (!result) return;
    setLatestTask(result);
    setGenerationTasks((items) => [result, ...items.filter((item) => item.id !== result.id)]);
    await refreshWalletBalance();
  }

  async function handleRefreshGenerationTasks() {
    if (!session) return;
    const result = await runAction('Загружаем последние генерации…', () => fetchMyGenerations(session.access_token));
    if (result) setGenerationTasks(result.items);
  }

  async function handleImportResultAsset(assetId: string, taskId?: string) {
    if (!session) return;
    const result = await runAction('Импортируем provider media в storage…', () =>
      importExternalMedia(session.access_token, assetId),
    );
    if (!result) return;
    const refreshedTaskId = taskId ?? latestTask?.id;
    if (refreshedTaskId) {
      const refreshedTask = await fetchGenerationTask(session.access_token, refreshedTaskId);
      setLatestTask((current) => (current?.id === refreshedTask.id ? refreshedTask : current));
      setGenerationTasks((items) => [refreshedTask, ...items.filter((item) => item.id !== refreshedTask.id)]);
    }
  }

  async function handlePublishResultAsset(asset: GenerationResultAsset) {
    if (!session) return;
    if (asset.is_external) {
      setErrorMessage('Сначала импортируй external result media в storage.');
      return;
    }
    const publication = await runAction('Публикуем result asset…', () =>
      createPublication(session.access_token, {
        asset_id: asset.asset_id,
        title: publishTitle || 'Generated result',
        description: publishDescription || 'Generated from AdultGen website app.',
        visibility: publishVisibility,
        is_explicit: true,
        blur_required: true,
        allow_remix: true,
        prompt_public: false,
        project_id: workspace?.project_id ?? null,
      }),
    );
    if (!publication) return;
    setMyPublications((items) => [publication, ...items]);
    if (publication.visibility === 'feed') setFeed((current) => ({ items: [publication, ...current.items] }));
  }

  async function handleUploadMedia(event: ChangeEvent<HTMLInputElement>, kind: 'temporary' | 'reference') {
    const file = event.target.files?.[0];
    if (!session || !file) return;
    const result = await runAction(`Загружаем ${kind === 'reference' ? 'референс' : 'temp media'}…`, () =>
      kind === 'reference' ? uploadReferenceMedia(session.access_token, file) : uploadTemporaryMedia(session.access_token, file),
    );
    if (result) setUploadedAssets((items) => [result.asset, ...items]);
    event.target.value = '';
  }

  async function handlePublishLatestAsset() {
    if (!session) return;
    const asset = uploadedAssets[0];
    if (!asset) {
      setErrorMessage('Сначала загрузи media asset.');
      return;
    }
    const publication = await runAction('Публикуем media asset…', () =>
      createPublication(session.access_token, {
        asset_id: asset.id,
        title: publishTitle,
        description: publishDescription,
        visibility: publishVisibility,
        is_explicit: true,
        blur_required: true,
        allow_remix: true,
        prompt_public: false,
        project_id: workspace?.project_id ?? null,
      }),
    );
    if (!publication) return;
    setMyPublications((items) => [publication, ...items]);
    if (publication.visibility === 'feed') setFeed((current) => ({ items: [publication, ...current.items] }));
  }

  async function handleRefreshFeed() {
    const result = await runAction('Загружаем feed…', () => fetchFeed());
    if (result) setFeed(result);
  }

  async function handleSavePublication(publicationId: string) {
    if (!session) return;
    await runAction('Сохраняем публикацию в коллекцию…', () => savePublication(session.access_token, publicationId));
    const collection = await fetchSavedCollection(session.access_token);
    setSavedItems(collection.items);
  }

  async function handleRefreshCollection() {
    if (!session) return;
    const result = await runAction('Загружаем коллекцию…', () => fetchSavedCollection(session.access_token));
    if (result) setSavedItems(result.items);
  }

  async function handleRefreshMyPublications() {
    if (!session) return;
    const result = await runAction('Загружаем мои публикации…', () => fetchMyPublications(session.access_token));
    if (result) setMyPublications(result.items);
  }

  async function handleLoadProfile() {
    if (!session) return;
    const result = await runAction('Загружаем профиль…', () => fetchMyProfile(session.access_token));
    if (result) setProfile(result);
  }

  async function handleToggleProfileVisibility() {
    if (!session) return;
    const current = profile ?? (await fetchMyProfile(session.access_token));
    const nextVisibility = current.visibility === 'public' ? 'private' : 'public';
    const result = await runAction('Обновляем видимость профиля…', () =>
      updateMyProfile(session.access_token, {
        visibility: nextVisibility,
        display_name: displayName,
        bio: 'AI media creator profile powered by AdultGen web app.',
      }),
    );
    if (result) setProfile(result);
  }

  async function handleRefreshBillingPackages() {
    const result = await runAction('Загружаем credit packages…', () => fetchCreditPackages());
    if (!result) return;
    setCreditPackages(result.items);
    if (!result.items.some((item) => item.code === selectedPackageCode)) {
      setSelectedPackageCode(result.items[0]?.code ?? 'creator_1500');
    }
  }

  async function handleCreatePaymentOrder() {
    if (!session) return;
    const result = await runAction('Создаём payment order…', () =>
      createPaymentOrder(session.access_token, selectedPackageCode, 'crocopay'),
    );
    if (!result) return;
    setLatestPaymentOrder(result);
    setLatestCheckout(null);
  }

  async function handleStartCrocoPayCheckout() {
    if (!session) return;
    let order = latestPaymentOrder;
    if (!order || order.package_code !== selectedPackageCode || order.status === 'paid') {
      order = await createPaymentOrder(session.access_token, selectedPackageCode, 'crocopay');
      setLatestPaymentOrder(order);
    }
    const result = await runAction('Создаём CrocoPay checkout…', () =>
      initiateCrocoPayCheckout(session.access_token, order.id),
    );
    if (!result) return;
    setLatestPaymentOrder(result.order);
    setLatestCheckout(result);
    window.open(result.redirect_url, '_blank', 'noopener,noreferrer');
  }

  async function refreshWalletBalance() {
    if (!session) return;
    const result = await runAction('Обновляем баланс…', () => fetchWalletBalance(session.access_token));
    if (result) setWalletBalance(result);
  }

  function handleLogout() {
    clearWebSession();
    setSession(null);
    setAdultConsent(null);
    setWorkspace(null);
    setLatestTask(null);
    setGenerationTasks([]);
    setProfile(null);
    setUploadedAssets([]);
    setMyPublications([]);
    setFeed({ items: [] });
    setSavedItems([]);
    setCreditPackages([]);
    setLatestPaymentOrder(null);
    setLatestCheckout(null);
    setWalletBalance(null);
    navigate(webAppRoutes[0]);
  }

  function renderActiveScreen() {
    if (routeBlockedByAuth) {
      return (
        <LoginCard
          email={email}
          displayName={displayName}
          setEmail={setEmail}
          setDisplayName={setDisplayName}
          onLogin={() => void handleLogin()}
        />
      );
    }
    if (routeBlockedByAge) {
      return <AgeGateCard onAccept={() => void handleAcceptAdultConsent()} onRefresh={() => void handleRefreshConsent()} />;
    }

    switch (activeRoute.id) {
      case 'landing':
        return <LandingCard onStart={() => navigate(resolveRoute('studio'))} />;
      case 'ageGate':
        return <AgeGateCard onAccept={() => void handleAcceptAdultConsent()} onRefresh={() => void handleRefreshConsent()} />;
      case 'studio':
        return (
          <StudioCard
            studio={studio}
            setStudio={setStudio}
            workspace={workspace}
            latestTask={latestTask}
            generationTasks={generationTasks}
            uploadedAssets={uploadedAssets}
            onPrepareWorkspace={() => void handlePrepareWorkspace()}
            onLaunch={() => void handleLaunchGeneration()}
            onRefreshLatestTask={() => void handleRefreshLatestTask()}
            onRefreshGenerationTasks={() => void handleRefreshGenerationTasks()}
            onImportResultAsset={(assetId, taskId) => void handleImportResultAsset(assetId, taskId)}
            onPublishResultAsset={(asset) => void handlePublishResultAsset(asset)}
            onUploadReference={(event) => void handleUploadMedia(event, 'reference')}
            onUploadTemporary={(event) => void handleUploadMedia(event, 'temporary')}
            onPublishLatestAsset={() => void handlePublishLatestAsset()}
            publishTitle={publishTitle}
            publishDescription={publishDescription}
            publishVisibility={publishVisibility}
            setPublishTitle={setPublishTitle}
            setPublishDescription={setPublishDescription}
            setPublishVisibility={setPublishVisibility}
          />
        );
      case 'projects':
        return (
          <ProjectsCard
            workspace={workspace}
            latestTask={latestTask}
            generationTasks={generationTasks}
            onPrepareWorkspace={() => void handlePrepareWorkspace()}
            onOpenStudio={() => navigate(resolveRoute('studio'))}
          />
        );
      case 'avatars':
        return (
          <AvatarsCard
            workspace={workspace}
            uploadedAssets={uploadedAssets}
            onUploadReference={(event) => void handleUploadMedia(event, 'reference')}
            onPrepareWorkspace={() => void handlePrepareWorkspace()}
          />
        );
      case 'feed':
        return <FeedCard feed={feed} onRefresh={() => void handleRefreshFeed()} onSave={(id) => void handleSavePublication(id)} />;
      case 'collection':
        return <CollectionCard savedItems={savedItems} onRefresh={() => void handleRefreshCollection()} />;
      case 'profile':
        return (
          <ProfileCard
            profile={profile}
            publications={myPublications}
            onLoad={() => void handleLoadProfile()}
            onToggleVisibility={() => void handleToggleProfileVisibility()}
            onRefreshPublications={() => void handleRefreshMyPublications()}
          />
        );
      case 'billing':
        return (
          <BillingCard
            packages={creditPackages}
            selectedPackageCode={selectedPackageCode}
            latestOrder={latestPaymentOrder}
            latestCheckout={latestCheckout}
            walletBalance={walletBalance}
            onSelectPackage={setSelectedPackageCode}
            onRefreshPackages={() => void handleRefreshBillingPackages()}
            onCreateOrder={() => void handleCreatePaymentOrder()}
            onStartCheckout={() => void handleStartCrocoPayCheckout()}
            onRefreshWallet={() => void refreshWalletBalance()}
          />
        );
      case 'partners':
        return <PartnersCard session={session} walletBalance={walletBalance} onOpenBilling={() => navigate(resolveRoute('billing'))} />;
      case 'support':
        return <SupportCard session={session} onOpenStudio={() => navigate(resolveRoute('studio'))} onOpenBilling={() => navigate(resolveRoute('billing'))} />;
      default:
        return <ProductSection route={activeRoute} session={session} adultConsent={adultConsent} latestTask={latestTask} />;
    }
  }

  return (
    <main className="web-shell app-product-shell">
      <a className="skip-link" href="#main-content">
        Перейти к основному содержимому
      </a>
      <aside className="sidebar" aria-label="Навигация AdultGen">
        <div>
          <p className="eyebrow">AdultGen</p>
          <h1>AI Studio</h1>
          <p className="sidebar-copy">
            Генерация, медиа, публикации, профиль, биллинг и операционные статусы в одном web-first продукте.
          </p>
        </div>
        <RouteGroup title="Рабочие экраны" routes={primaryWebAppRoutes} activeRoute={activeRoute} onNavigate={navigate} />
        <RouteGroup title="Сервис" routes={secondaryWebAppRoutes} activeRoute={activeRoute} onNavigate={navigate} />
        <SessionPanel session={session} adultConsent={adultConsent} walletBalance={walletBalance} onLogout={handleLogout} />
      </aside>
      <section className="main-panel" id="main-content" tabIndex={-1}>
        <TopBar
          activeRoute={activeRoute}
          statusMessage={statusMessage}
          errorMessage={errorMessage}
          onNavigate={navigate}
        />
        {renderActiveScreen()}
      </section>
    </main>
  );
}

function RouteGroup({
  title,
  routes,
  activeRoute,
  onNavigate,
}: {
  title: string;
  routes: WebAppRoute[];
  activeRoute: WebAppRoute;
  onNavigate: (route: WebAppRoute) => void;
}) {
  if (routes.length === 0) return null;
  return (
    <nav className="route-nav" aria-label={title}>
      <p className="route-group-title">{title}</p>
      {routes.map((route) => (
        <button
          key={route.id}
          type="button"
          className={route.id === activeRoute.id ? 'route-button active' : 'route-button'}
          aria-current={route.id === activeRoute.id ? 'page' : undefined}
          title={route.description}
          onClick={() => onNavigate(route)}
        >
          <span>{route.title}</span>
          <small>{route.path}</small>
        </button>
      ))}
    </nav>
  );
}

function TopBar({
  activeRoute,
  statusMessage,
  errorMessage,
  onNavigate,
}: {
  activeRoute: WebAppRoute;
  statusMessage: string | null;
  errorMessage: string | null;
  onNavigate: (route: WebAppRoute) => void;
}) {
  return (
    <header className="topbar app-topbar">
      <div>
        <p className="eyebrow">{activeRoute.path}</p>
        <h2>{activeRoute.title}</h2>
        <p className="muted-text topbar-description">{activeRoute.description}</p>
      </div>
      <div className="topbar-actions" aria-live="polite">
        <label className="route-selector-label">
          <span>Экран</span>
          <select
            aria-label="Route selector"
            value={activeRoute.id}
            onChange={(event) => {
              const nextRoute = webAppRoutes.find((route) => route.id === event.target.value);
              if (nextRoute) onNavigate(nextRoute);
            }}
          >
            {webAppRoutes.map((route) => (
              <option key={route.id} value={route.id}>
                {route.title}
              </option>
            ))}
          </select>
        </label>
        {statusMessage && <span className="status-pill">{statusMessage}</span>}
        {errorMessage && <span className="status-pill error">{errorMessage}</span>}
      </div>
    </header>
  );
}

function LoginCard({
  email,
  displayName,
  setEmail,
  setDisplayName,
  onLogin,
}: {
  email: string;
  displayName: string;
  setEmail: (value: string) => void;
  setDisplayName: (value: string) => void;
  onLogin: () => void;
}) {
  return (
    <section className="card stack-card auth-card">
      <p className="eyebrow">Website auth</p>
      <h3>Вход в сайт-приложение</h3>
      <p>
        Для MVP используем web session endpoint. Позже этот слой можно заменить на email OTP, OAuth, wallet login
        или полноценную регистрацию без изменения Core token-контракта.
      </p>
      <div className="form-grid">
        <label>
          Email
          <input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label>
          Имя профиля
          <input autoComplete="name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
        </label>
      </div>
      <button className="primary-button" type="button" onClick={onLogin} disabled={!email.trim() || !displayName.trim()}>
        Войти и получить Core token
      </button>
    </section>
  );
}

function AgeGateCard({ onAccept, onRefresh }: { onAccept: () => void; onRefresh: () => void }) {
  return (
    <section className="card stack-card danger-card age-gate-card">
      <p className="eyebrow">18+ safety gate</p>
      <h3>Подтверждение возраста и правил</h3>
      <p>
        Перед доступом к Studio и Feed пользователь подтверждает, что ему есть 18 лет, соглашается с
        blur/moderation-контуром и понимает запреты на minors, public figures, non-consensual identity, violence,
        coercion и hidden camera контент.
      </p>
      <div className="policy-grid" aria-label="Ключевые правила">
        <GuardPill label="18+ only" enabled />
        <GuardPill label="No minors" enabled />
        <GuardPill label="No public figures" enabled />
        <GuardPill label="Consent required" enabled />
      </div>
      <div className="button-row">
        <button className="primary-button" type="button" onClick={onAccept}>
          Мне есть 18 лет, продолжить
        </button>
        <button className="ghost-button" type="button" onClick={onRefresh}>
          Проверить статус
        </button>
      </div>
    </section>
  );
}

function LandingCard({ onStart }: { onStart: () => void }) {
  return (
    <section className="landing-grid">
      <div className="card hero-card product-hero-card">
        <p className="eyebrow">Web-first adult AI generation</p>
        <h3>Сайт как основной продукт, Telegram как companion</h3>
        <p>
          UX строится вокруг генератора: prompt, negative prompt, uploads, референсы, проекты, лента, коллекция,
          профиль, биллинг и партнёрский кабинет.
        </p>
        <button className="primary-button" type="button" onClick={onStart}>
          Открыть Studio
        </button>
      </div>
      <MetricCard label="Media" value="upload" text="Reference/temp uploads и publication flow." />
      <MetricCard label="Safety" value="18+" text="Adult gate и запретные категории до контента." />
      <MetricCard label="Models" value="Kie" text="Seedream 5 Pro + Seedance 2.0 через capability layer." />
    </section>
  );
}

function StudioCard({
  studio,
  setStudio,
  workspace,
  latestTask,
  generationTasks,
  uploadedAssets,
  onPrepareWorkspace,
  onLaunch,
  onRefreshLatestTask,
  onRefreshGenerationTasks,
  onImportResultAsset,
  onPublishResultAsset,
  onUploadReference,
  onUploadTemporary,
  onPublishLatestAsset,
  publishTitle,
  publishDescription,
  publishVisibility,
  setPublishTitle,
  setPublishDescription,
  setPublishVisibility,
}: {
  studio: StudioState;
  setStudio: (value: StudioState) => void;
  workspace: WorkspaceDraft | null;
  latestTask: GenerationTask | null;
  generationTasks: GenerationTask[];
  uploadedAssets: MediaAsset[];
  onPrepareWorkspace: () => void;
  onLaunch: () => void;
  onRefreshLatestTask: () => void;
  onRefreshGenerationTasks: () => void;
  onImportResultAsset: (assetId: string, taskId?: string) => void;
  onPublishResultAsset: (asset: GenerationResultAsset) => void;
  onUploadReference: (event: ChangeEvent<HTMLInputElement>) => void;
  onUploadTemporary: (event: ChangeEvent<HTMLInputElement>) => void;
  onPublishLatestAsset: () => void;
  publishTitle: string;
  publishDescription: string;
  publishVisibility: PublicationVisibility;
  setPublishTitle: (value: string) => void;
  setPublishDescription: (value: string) => void;
  setPublishVisibility: (value: PublicationVisibility) => void;
}) {
  const estimatedCredits = estimateCredits(studio.mode, studio.duration_seconds);
  const canLaunch = studio.prompt.trim().length > 10;

  return (
    <section className="studio-grid ux-studio-grid">
      <form className="card stack-card studio-compose-card" onSubmit={(event) => event.preventDefault()}>
        <div className="section-heading-row">
          <div>
            <p className="eyebrow">Generation Studio</p>
            <h3>Создание фото/видео</h3>
          </div>
          <span className="status-pill">{estimatedCredits} credits</span>
        </div>
        <label>
          Режим
          <select value={studio.mode} onChange={(event) => setStudio({ ...studio, mode: event.target.value as GenerationMode })}>
            <option value="image_text_to_image">Image · text-to-image</option>
            <option value="image_to_image">Image · image-to-image</option>
            <option value="video_text_to_video">Video · text-to-video</option>
            <option value="video_image_to_video_first_frame">Video · first frame</option>
            <option value="video_image_to_video_first_last_frames">Video · first + last frame</option>
            <option value="video_multimodal_reference_to_video">Video · multimodal refs</option>
          </select>
        </label>
        <label>
          Prompt
          <textarea rows={5} value={studio.prompt} onChange={(event) => setStudio({ ...studio, prompt: event.target.value })} />
          <small>Опиши сцену, стиль, камеру, свет и ограничения. Главная кнопка активна после нормального prompt.</small>
        </label>
        <label>
          Negative prompt
          <textarea
            rows={3}
            value={studio.negative_prompt}
            onChange={(event) => setStudio({ ...studio, negative_prompt: event.target.value })}
          />
        </label>
        <label>
          reference_urls, по одному на строку
          <textarea
            rows={3}
            value={studio.reference_urls}
            onChange={(event) => setStudio({ ...studio, reference_urls: event.target.value })}
          />
        </label>
        <div className="form-grid">
          <label>
            Aspect ratio
            <select value={studio.aspect_ratio} onChange={(event) => setStudio({ ...studio, aspect_ratio: event.target.value })}>
              <option value="9:16">9:16 vertical</option>
              <option value="16:9">16:9 wide</option>
              <option value="1:1">1:1 square</option>
            </select>
          </label>
          <label>
            Resolution
            <select value={studio.resolution} onChange={(event) => setStudio({ ...studio, resolution: event.target.value })}>
              <option value="720p">720p</option>
              <option value="1080p">1080p</option>
            </select>
          </label>
          <label>
            Duration
            <input
              type="number"
              min="1"
              max="15"
              value={studio.duration_seconds}
              onChange={(event) => setStudio({ ...studio, duration_seconds: Number(event.target.value) })}
            />
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={studio.generate_audio}
              onChange={(event) => setStudio({ ...studio, generate_audio: event.target.checked })}
            />
            Generate audio
          </label>
        </div>
      </form>

      <aside className="card stack-card run-card">
        <p className="eyebrow">Run summary</p>
        <h3>{estimatedCredits} credits</h3>
        <ProgressSteps workspace={workspace} latestTask={latestTask} uploads={uploadedAssets.length} />
        <p>Сначала создаём workspace, затем generation task с резервом кредитов. Результаты приходят через callback.</p>
        <div className="button-row sticky-action-row">
          <button className="ghost-button" type="button" onClick={onPrepareWorkspace}>
            Подготовить workspace
          </button>
          <button className="primary-button" type="button" onClick={onLaunch} disabled={!canLaunch}>
            Запустить генерацию
          </button>
          <button className="ghost-button" type="button" onClick={onRefreshLatestTask} disabled={!latestTask}>
            Обновить последнюю задачу
          </button>
        </div>
        {workspace && <CodeBlock value={JSON.stringify(workspace, null, 2)} />}
        {latestTask && <GenerationTaskCard task={latestTask} compact />}
      </aside>

      <aside className="card stack-card media-publish-card">
        <p className="eyebrow">Media + Publish</p>
        <h3>Uploads и публикация</h3>
        <div className="form-grid">
          <label>
            Reference upload
            <input type="file" accept="image/*,video/*,audio/*" onChange={onUploadReference} />
          </label>
          <label>
            Temporary result upload
            <input type="file" accept="image/*,video/*" onChange={onUploadTemporary} />
          </label>
        </div>
        <AssetList assets={uploadedAssets} />
        <label>
          Publish title
          <input value={publishTitle} onChange={(event) => setPublishTitle(event.target.value)} />
        </label>
        <label>
          Publish description
          <textarea rows={3} value={publishDescription} onChange={(event) => setPublishDescription(event.target.value)} />
        </label>
        <label>
          Куда публиковать
          <select value={publishVisibility} onChange={(event) => setPublishVisibility(event.target.value as PublicationVisibility)}>
            <option value="profile">Только профиль</option>
            <option value="feed">Общая лента</option>
          </select>
        </label>
        <button className="ghost-button" type="button" onClick={onPublishLatestAsset} disabled={uploadedAssets.length === 0}>
          Опубликовать последний upload
        </button>
      </aside>

      <GenerationResultsPanel
        tasks={generationTasks}
        onRefresh={onRefreshGenerationTasks}
        onImportResultAsset={onImportResultAsset}
        onPublishResultAsset={onPublishResultAsset}
      />
    </section>
  );
}

function ProgressSteps({ workspace, latestTask, uploads }: { workspace: WorkspaceDraft | null; latestTask: GenerationTask | null; uploads: number }) {
  return (
    <ol className="progress-steps" aria-label="Путь создания">
      <li className={workspace ? 'done' : ''}>Workspace</li>
      <li className={latestTask ? 'done' : ''}>Generation</li>
      <li className={uploads > 0 || (latestTask?.results.length ?? 0) > 0 ? 'done' : ''}>Media</li>
      <li>Publish</li>
    </ol>
  );
}

function ProjectsCard({
  workspace,
  latestTask,
  generationTasks,
  onPrepareWorkspace,
  onOpenStudio,
}: {
  workspace: WorkspaceDraft | null;
  latestTask: GenerationTask | null;
  generationTasks: GenerationTask[];
  onPrepareWorkspace: () => void;
  onOpenStudio: () => void;
}) {
  return (
    <section className="landing-grid projects-screen">
      <div className="card hero-card">
        <p className="eyebrow">Projects</p>
        <h3>Проекты и сцены</h3>
        <p>
          Этот экран показывает текущий workspace, последнюю задачу и историю генераций. Так пользователь понимает,
          где он находится, даже если пришёл по deep link.
        </p>
        <div className="button-row">
          <button className="primary-button" type="button" onClick={onOpenStudio}>
            Открыть Studio
          </button>
          <button className="ghost-button" type="button" onClick={onPrepareWorkspace}>
            Создать workspace
          </button>
        </div>
      </div>
      <MetricCard label="Workspace" value={workspace ? 'ready' : 'empty'} text="Аватар, проект и первая сцена." />
      <MetricCard label="Tasks" value={String(generationTasks.length)} text="Последние generation tasks." />
      <MetricCard label="Latest" value={latestTask?.status ?? 'none'} text="Текущий статус последней задачи." />
      <section className="card stack-card results-panel">
        <p className="eyebrow">Project state</p>
        {workspace ? <CodeBlock value={JSON.stringify(workspace, null, 2)} /> : <EmptyState title="Workspace ещё не создан" action="Нажми “Создать workspace” или открой Studio." />}
        {latestTask && <GenerationTaskCard task={latestTask} compact />}
      </section>
    </section>
  );
}

function AvatarsCard({
  workspace,
  uploadedAssets,
  onUploadReference,
  onPrepareWorkspace,
}: {
  workspace: WorkspaceDraft | null;
  uploadedAssets: MediaAsset[];
  onUploadReference: (event: ChangeEvent<HTMLInputElement>) => void;
  onPrepareWorkspace: () => void;
}) {
  return (
    <section className="studio-grid avatars-screen">
      <div className="card stack-card">
        <p className="eyebrow">Avatar references</p>
        <h3>Аватары и visual identity</h3>
        <p>
          Здесь собираются приватные референсы и workspace avatar id. Дальше этот экран можно развить в полноценную
          библиотеку персонажей.
        </p>
        <div className="button-row">
          <button className="primary-button" type="button" onClick={onPrepareWorkspace}>
            Подготовить avatar workspace
          </button>
        </div>
        {workspace ? <CodeBlock value={JSON.stringify({ avatar_id: workspace.avatar_id }, null, 2)} /> : <EmptyState title="Аватар ещё не создан" action="Создай workspace, чтобы получить avatar_id." />}
      </div>
      <aside className="card stack-card">
        <p className="eyebrow">References</p>
        <h3>Загрузка референсов</h3>
        <label>
          Reference upload
          <input type="file" accept="image/*,video/*,audio/*" onChange={onUploadReference} />
        </label>
        <AssetList assets={uploadedAssets} />
      </aside>
    </section>
  );
}

function BillingCard({
  packages,
  selectedPackageCode,
  latestOrder,
  latestCheckout,
  walletBalance,
  onSelectPackage,
  onRefreshPackages,
  onCreateOrder,
  onStartCheckout,
  onRefreshWallet,
}: {
  packages: CreditPackage[];
  selectedPackageCode: string;
  latestOrder: PaymentOrder | null;
  latestCheckout: ProviderCheckoutResponse | null;
  walletBalance: WalletBalance | null;
  onSelectPackage: (code: string) => void;
  onRefreshPackages: () => void;
  onCreateOrder: () => void;
  onStartCheckout: () => void;
  onRefreshWallet: () => void;
}) {
  const selectedPackage = packages.find((item) => item.code === selectedPackageCode);
  return (
    <section className="billing-grid">
      <div className="card stack-card billing-hero">
        <p className="eyebrow">Website billing</p>
        <h3>Кредиты для генераций</h3>
        <p>
          Billing flow: выбрать package → создать PaymentOrder → получить CrocoPay checkout → ждать webhook, который
          начислит purchased credits через wallet ledger.
        </p>
        <div className="button-row sticky-action-row">
          <button className="ghost-button" type="button" onClick={onRefreshPackages}>
            Обновить пакеты
          </button>
          <button className="ghost-button" type="button" onClick={onRefreshWallet}>
            Обновить баланс
          </button>
          <button className="primary-button" type="button" onClick={onCreateOrder} disabled={!selectedPackage}>
            Создать order
          </button>
          <button className="primary-button" type="button" onClick={onStartCheckout} disabled={!selectedPackage}>
            Оплатить через CrocoPay
          </button>
        </div>
      </div>
      <WalletBalanceCard walletBalance={walletBalance} />
      <div className="package-grid" aria-label="Credit packages">
        {packages.length === 0 ? (
          <section className="card stack-card">
            <EmptyState title="Пакеты ещё не загружены" action="Нажми “Обновить пакеты”." />
          </section>
        ) : (
          packages.map((item) => (
            <button
              key={item.code}
              type="button"
              className={item.code === selectedPackageCode ? 'package-card selected' : 'package-card'}
              aria-pressed={item.code === selectedPackageCode}
              onClick={() => onSelectPackage(item.code)}
            >
              {item.is_popular && <span className="guard-pill enabled">popular</span>}
              <strong>{item.title}</strong>
              <span>{item.credits.toLocaleString('ru-RU')} credits</span>
              <small>
                {item.amount_major} {item.currency}
              </small>
              <p>{item.description}</p>
            </button>
          ))
        )}
      </div>
      <aside className="card stack-card">
        <p className="eyebrow">Selected package</p>
        {selectedPackage ? <CodeBlock value={JSON.stringify(selectedPackage, null, 2)} /> : <p className="muted-text">Нет выбранного пакета.</p>}
      </aside>
      <aside className="card stack-card">
        <p className="eyebrow">Latest payment order</p>
        {latestOrder ? <PaymentOrderSummary order={latestOrder} checkout={latestCheckout} /> : <p className="muted-text">Order ещё не создан.</p>}
      </aside>
    </section>
  );
}

function WalletBalanceCard({ walletBalance }: { walletBalance: WalletBalance | null }) {
  return (
    <aside className="card stack-card wallet-balance-card">
      <p className="eyebrow">Wallet balance</p>
      <h3>{walletBalance ? walletBalance.total_available.toLocaleString('ru-RU') : '—'} credits</h3>
      <div className="wallet-balance-grid">
        <MetricCard label="Available" value={String(walletBalance?.total_available ?? 0)} text="Можно тратить на генерации." />
        <MetricCard label="Reserved" value={String(walletBalance?.total_reserved ?? 0)} text="Зарезервировано под задачи." />
        <MetricCard label="Total" value={String(walletBalance?.total_balance ?? 0)} text={walletBalance?.currency ?? 'credits'} />
      </div>
      {walletBalance ? (
        <div className="item-list">
          {walletBalance.buckets.map((bucket) => (
            <div className="item-row" key={bucket.bucket}>
              <strong>{bucket.bucket}</strong>
              <span>
                {bucket.available} available · {bucket.reserved} reserved
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted-text">Баланс появится после входа и загрузки /wallet/me.</p>
      )}
    </aside>
  );
}

function PaymentOrderSummary({ order, checkout }: { order: PaymentOrder; checkout: ProviderCheckoutResponse | null }) {
  return (
    <div className="payment-order-card">
      <div className="section-heading-row">
        <div>
          <strong>{order.package_code}</strong>
          <small>{order.id}</small>
        </div>
        <span className={`task-status ${order.status}`}>{order.status}</span>
      </div>
      <div className="guard-grid">
        <GuardPill label={`${order.credits_amount} credits`} enabled />
        <GuardPill label={`${order.amount_minor} ${order.currency}`} enabled />
        <GuardPill label={order.external_payment_id ? 'provider id' : 'no provider id'} enabled={Boolean(order.external_payment_id)} />
      </div>
      <small>Expires: {new Date(order.expires_at).toLocaleString('ru-RU')}</small>
      {order.checkout_url && (
        <a className="text-link" href={order.checkout_url} target="_blank" rel="noreferrer">
          Open internal checkout
        </a>
      )}
      {order.callback_url && <small>Callback token URL prepared for provider webhook.</small>}
      {order.provider_checkout_url && (
        <a className="text-link" href={order.provider_checkout_url} target="_blank" rel="noreferrer">
          Open provider checkout
        </a>
      )}
      {checkout && (
        <a className="primary-button checkout-link" href={checkout.redirect_url} target="_blank" rel="noreferrer">
          Перейти к оплате
        </a>
      )}
    </div>
  );
}

function GenerationResultsPanel({
  tasks,
  onRefresh,
  onImportResultAsset,
  onPublishResultAsset,
}: {
  tasks: GenerationTask[];
  onRefresh: () => void;
  onImportResultAsset: (assetId: string, taskId?: string) => void;
  onPublishResultAsset: (asset: GenerationResultAsset) => void;
}) {
  return (
    <section className="card stack-card results-panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Generation history</p>
          <h3>Результаты генераций</h3>
        </div>
        <button className="ghost-button" type="button" onClick={onRefresh}>
          Обновить список
        </button>
      </div>
      <p>
        После Kie callback здесь появятся result assets. External assets сначала импортируются в storage, потом их можно
        публиковать в профиль или общую ленту.
      </p>
      {tasks.length === 0 ? (
        <EmptyState title="Пока нет generation tasks" action="Запусти генерацию или обнови список." />
      ) : (
        <div className="generation-grid">
          {tasks.map((task) => (
            <GenerationTaskCard
              key={task.id}
              task={task}
              onImportResultAsset={(assetId) => onImportResultAsset(assetId, task.id)}
              onPublishResultAsset={onPublishResultAsset}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function GenerationTaskCard({
  task,
  compact = false,
  onImportResultAsset,
  onPublishResultAsset,
}: {
  task: GenerationTask;
  compact?: boolean;
  onImportResultAsset?: (assetId: string) => void;
  onPublishResultAsset?: (asset: GenerationResultAsset) => void;
}) {
  return (
    <article className="generation-card">
      <div className="generation-card-head">
        <div>
          <strong>{task.operation}</strong>
          <small>{task.id}</small>
        </div>
        <span className={`task-status ${task.status}`}>{task.status}</span>
      </div>
      <div className="guard-grid">
        <GuardPill label={`${task.reserved_credits} reserved`} enabled />
        <GuardPill label={`${task.charged_credits} charged`} enabled={task.charged_credits > 0} />
        <GuardPill label={task.provider_task_id ? 'provider id' : 'no provider id'} enabled={Boolean(task.provider_task_id)} />
      </div>
      {task.error_message && (
        <p className="muted-text">
          {task.error_code}: {task.error_message}
        </p>
      )}
      {!compact && <ResultAssetList assets={task.results} onImport={onImportResultAsset} onPublish={onPublishResultAsset} />}
    </article>
  );
}

function ResultAssetList({
  assets,
  onImport,
  onPublish,
}: {
  assets: GenerationResultAsset[];
  onImport?: (assetId: string) => void;
  onPublish?: (asset: GenerationResultAsset) => void;
}) {
  if (assets.length === 0) return <p className="muted-text">Результатов пока нет: ждём callback от провайдера.</p>;
  return (
    <div className="result-list">
      {assets.map((asset) => (
        <div className="result-card" key={`${asset.role}-${asset.asset_id}`}>
          <div className="result-preview">
            {asset.role === 'video' ? (
              <video controls preload="metadata" src={coreMediaUrl(asset.media_url)} />
            ) : (
              <img alt={`${asset.role} result`} src={coreMediaUrl(asset.media_url)} loading="lazy" />
            )}
          </div>
          <div className="result-meta">
            <strong>{asset.role}</strong>
            <small>{asset.asset_id}</small>
            <GuardPill label={asset.is_external ? 'external' : 'stored'} enabled={!asset.is_external} />
            <div className="button-row">
              {asset.is_external && onImport && (
                <button className="ghost-button small-button" type="button" onClick={() => onImport(asset.asset_id)}>
                  Импортировать
                </button>
              )}
              {onPublish && (
                <button
                  className="primary-button small-button"
                  type="button"
                  disabled={asset.is_external}
                  onClick={() => onPublish(asset)}
                >
                  Опубликовать
                </button>
              )}
              <a className="text-link" href={coreMediaUrl(asset.media_url)} target="_blank" rel="noreferrer">
                Открыть media
              </a>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function AssetList({ assets }: { assets: MediaAsset[] }) {
  if (assets.length === 0) return <p className="muted-text">Пока нет загруженных assets.</p>;
  return (
    <div className="item-list">
      {assets.slice(0, 5).map((asset) => (
        <div className="item-row" key={asset.id}>
          <strong>{asset.media_type}</strong>
          <span>{asset.mime_type}</span>
          <small>{asset.id}</small>
        </div>
      ))}
    </div>
  );
}

function FeedCard({ feed, onRefresh, onSave }: { feed: FeedResponse; onRefresh: () => void; onSave: (publicationId: string) => void }) {
  return (
    <section className="card stack-card feed-screen">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Common Feed</p>
          <h3>Лента публикаций</h3>
        </div>
        <button className="primary-button" type="button" onClick={onRefresh}>
          Обновить ленту
        </button>
      </div>
      <PublicationList publications={feed.items} onSave={onSave} />
    </section>
  );
}

function CollectionCard({ savedItems, onRefresh }: { savedItems: { publication_id: string; saved_at: string }[]; onRefresh: () => void }) {
  return (
    <section className="card stack-card">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Saved Collection</p>
          <h3>Коллекция</h3>
        </div>
        <button className="primary-button" type="button" onClick={onRefresh}>
          Обновить коллекцию
        </button>
      </div>
      <div className="item-list">
        {savedItems.length === 0 ? (
          <EmptyState title="Пока ничего не сохранено" action="Сохраняй публикации из ленты." />
        ) : (
          savedItems.map((item) => (
            <div className="item-row" key={item.publication_id}>
              <strong>{item.publication_id}</strong>
              <span>{new Date(item.saved_at).toLocaleString()}</span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function ProfileCard({
  profile,
  publications,
  onLoad,
  onToggleVisibility,
  onRefreshPublications,
}: {
  profile: Profile | null;
  publications: Publication[];
  onLoad: () => void;
  onToggleVisibility: () => void;
  onRefreshPublications: () => void;
}) {
  return (
    <section className="studio-grid profile-screen">
      <div className="card stack-card">
        <p className="eyebrow">Creator Profile</p>
        <h3>Профиль автора</h3>
        <p>Управление публичностью профиля и быстрый доступ к своим публикациям.</p>
        <div className="button-row">
          <button className="ghost-button" type="button" onClick={onLoad}>
            Загрузить профиль
          </button>
          <button className="primary-button" type="button" onClick={onToggleVisibility}>
            Переключить public/private
          </button>
          <button className="ghost-button" type="button" onClick={onRefreshPublications}>
            Мои публикации
          </button>
        </div>
        {profile ? <ProfileSummary profile={profile} /> : <EmptyState title="Профиль ещё не загружен" action="Нажми “Загрузить профиль”." />}
      </div>
      <section className="card stack-card">
        <p className="eyebrow">My publications</p>
        <h3>Публикации профиля</h3>
        <PublicationList publications={publications} />
      </section>
    </section>
  );
}

function ProfileSummary({ profile }: { profile: Profile }) {
  return (
    <div className="profile-summary">
      <div>
        <strong>{profile.display_name ?? 'Без имени'}</strong>
        <span>{profile.visibility}</span>
      </div>
      <small>public_id: {profile.public_id}</small>
      {profile.bio && <p>{profile.bio}</p>}
    </div>
  );
}

function PublicationList({ publications, onSave }: { publications: Publication[]; onSave?: (publicationId: string) => void }) {
  if (publications.length === 0) return <EmptyState title="Публикаций пока нет" action="Создай или обнови список." />;
  return (
    <div className="publication-grid">
      {publications.map((publication) => (
        <article className="publication-card" key={publication.id}>
          {publication.preview_url ? (
            <img
              className="publication-preview"
              alt={publication.title || 'Publication preview'}
              src={coreMediaUrl(publication.preview_url)}
              loading="lazy"
            />
          ) : (
            <div className="publication-placeholder" aria-label="No preview available" />
          )}
          <div className="publication-card-body">
            <strong>{publication.title || 'Untitled publication'}</strong>
            <span>
              {publication.visibility} · {publication.status}
            </span>
            <small>
              {publication.blur_required ? 'blur required' : 'no blur'} · remix {publication.allow_remix ? 'on' : 'off'}
            </small>
            <small>asset {publication.asset_id}</small>
            {onSave && (
              <button className="ghost-button small-button" type="button" onClick={() => onSave(publication.id)}>
                В коллекцию
              </button>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}

function PartnersCard({
  session,
  walletBalance,
  onOpenBilling,
}: {
  session: WebSession | null;
  walletBalance: WalletBalance | null;
  onOpenBilling: () => void;
}) {
  return (
    <section className="landing-grid partners-screen">
      <div className="card hero-card">
        <p className="eyebrow">Partners</p>
        <h3>Партнёрский контур</h3>
        <p>
          Сейчас это рабочий экран-основа: показывает статус аккаунта, платежеспособность и следующие блоки для
          referral/withdrawal. Он больше не выглядит как заглушка.
        </p>
        <button className="primary-button" type="button" onClick={onOpenBilling}>
          Проверить баланс
        </button>
      </div>
      <MetricCard label="Auth" value={session ? 'active' : 'guest'} text={session?.email ?? 'Нет web-session.'} />
      <MetricCard label="Credits" value={String(walletBalance?.total_available ?? 0)} text="Доступный баланс." />
      <MetricCard label="Status" value="MVP" text="Referral ledger будет подключён отдельным PR." />
      <section className="card stack-card results-panel">
        <p className="eyebrow">Partner checklist</p>
        <div className="item-list">
          <div className="item-row"><strong>1. Referral links</strong><span>Следующий слой — personal invite links.</span></div>
          <div className="item-row"><strong>2. Commission ledger</strong><span>Начисления должны идти через audit-friendly wallet events.</span></div>
          <div className="item-row"><strong>3. Withdrawals</strong><span>Выплаты только после compliance/manual review.</span></div>
        </div>
      </section>
    </section>
  );
}

function SupportCard({
  session,
  onOpenStudio,
  onOpenBilling,
}: {
  session: WebSession | null;
  onOpenStudio: () => void;
  onOpenBilling: () => void;
}) {
  return (
    <section className="studio-grid support-screen">
      <div className="card stack-card">
        <p className="eyebrow">Support</p>
        <h3>Поддержка</h3>
        <p>Быстрые маршруты для типовых проблем: генерация, медиа, оплата, аккаунт и политика контента.</p>
        <div className="button-row">
          <button className="primary-button" type="button" onClick={onOpenStudio}>
            Проблема с генерацией
          </button>
          <button className="ghost-button" type="button" onClick={onOpenBilling}>
            Проблема с оплатой
          </button>
        </div>
        <GuardPill label={session ? `session ${session.email}` : 'guest support'} enabled={Boolean(session)} />
      </div>
      <section className="card stack-card">
        <p className="eyebrow">FAQ</p>
        <h3>Что проверить сначала</h3>
        <div className="item-list">
          <div className="item-row"><strong>Генерация не стартует</strong><span>Проверь 18+, prompt, баланс и workspace.</span></div>
          <div className="item-row"><strong>Результата нет</strong><span>Обнови Generation history: provider callback может идти асинхронно.</span></div>
          <div className="item-row"><strong>Оплата не зачислилась</strong><span>Открой Billing и проверь latest order / webhook status.</span></div>
        </div>
      </section>
    </section>
  );
}

function ProductSection({
  route,
  session,
  adultConsent,
  latestTask,
}: {
  route: WebAppRoute;
  session: WebSession | null;
  adultConsent: AdultConsentStatus | null;
  latestTask: GenerationTask | null;
}) {
  return (
    <section className="card stack-card">
      <p className="eyebrow">{route.path}</p>
      <h3>{route.title}</h3>
      <p>{route.description}</p>
      <div className="guard-grid">
        <GuardPill label="Auth" enabled={Boolean(session)} />
        <GuardPill label="18+ consent" enabled={Boolean(adultConsent?.accepted)} />
        <GuardPill label="Latest task" enabled={Boolean(latestTask)} />
      </div>
    </section>
  );
}

function SessionPanel({
  session,
  adultConsent,
  walletBalance,
  onLogout,
}: {
  session: WebSession | null;
  adultConsent: AdultConsentStatus | null;
  walletBalance: WalletBalance | null;
  onLogout: () => void;
}) {
  return (
    <section className="session-panel" aria-label="Состояние сессии">
      <p className="eyebrow">Session</p>
      <GuardPill label="Web token" enabled={Boolean(session)} />
      <GuardPill label="18+ accepted" enabled={Boolean(adultConsent?.accepted)} />
      {walletBalance && <GuardPill label={`${walletBalance.total_available} credits`} enabled={walletBalance.total_available > 0} />}
      {session && (
        <>
          <small>{session.email}</small>
          <div className="capability-list" aria-label="Capabilities">
            <GuardPill label="generate" enabled={session.capabilities.can_generate} />
            <GuardPill label="publish feed" enabled={session.capabilities.can_publish_feed} />
            <GuardPill label="payments" enabled={session.capabilities.can_use_payments} />
          </div>
          <button className="ghost-button" type="button" onClick={onLogout}>
            Выйти
          </button>
        </>
      )}
    </section>
  );
}

function MetricCard({ label, value, text }: { label: string; value: string; text: string }) {
  return (
    <div className="card metric-card">
      <p className="eyebrow">{label}</p>
      <strong>{value}</strong>
      <span>{text}</span>
    </div>
  );
}

function EmptyState({ title, action }: { title: string; action: string }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <span>{action}</span>
    </div>
  );
}

function GuardPill({ label, enabled }: { label: string; enabled: boolean }) {
  return <span className={enabled ? 'guard-pill enabled' : 'guard-pill'}>{label}</span>;
}

function CodeBlock({ value }: { value: string }) {
  return <pre className="code-block">{value}</pre>;
}

function estimateCredits(mode: GenerationMode, durationSeconds: number): number {
  if (mode.startsWith('image_')) return 35;
  return Math.max(1, durationSeconds) * 18;
}
