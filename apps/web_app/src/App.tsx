import { useMemo, useState } from 'react';

import {
  acceptAdultConsent,
  createGenerationTask,
  createStarterWorkspace,
  createWebSession,
  fetchAdultConsent,
  fetchMyProfile,
  updateMyProfile,
  type AdultConsentStatus,
  type GenerationMode,
  type GenerationTask,
  type Profile,
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

type WorkspaceDraft = {
  avatar_id: string;
  project_id: string;
  scene_id: string;
};

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

export function App() {
  const initialRoute = useMemo(() => findRouteByPath(window.location.pathname), []);
  const [activeRoute, setActiveRoute] = useState<WebAppRoute>(initialRoute);
  const [session, setSession] = useState<WebSession | null>(() => loadWebSession());
  const [adultConsent, setAdultConsent] = useState<AdultConsentStatus | null>(() => loadAdultConsentStatus());
  const [workspace, setWorkspace] = useState<WorkspaceDraft | null>(null);
  const [latestTask, setLatestTask] = useState<GenerationTask | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [studio, setStudio] = useState<StudioState>(defaultStudioState);
  const [email, setEmail] = useState('creator@example.com');
  const [displayName, setDisplayName] = useState('AdultGen creator');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const routeBlockedByAuth = activeRoute.requiresAuth && !session;
  const routeBlockedByAge = activeRoute.requiresAdultConsent && !adultConsent?.accepted;

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
    setActiveRoute(webAppRoutes.find((route) => route.id === 'ageGate') ?? activeRoute);
  }

  async function handleAcceptAdultConsent() {
    if (!session) return;
    const result = await runAction('Фиксируем подтверждение 18+…', () => acceptAdultConsent(session.access_token));
    if (!result) return;
    saveAdultConsentStatus(result);
    setAdultConsent(result);
    setActiveRoute(webAppRoutes.find((route) => route.id === 'studio') ?? activeRoute);
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
    if (result) setLatestTask(result);
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

  function handleLogout() {
    clearWebSession();
    setSession(null);
    setAdultConsent(null);
    setWorkspace(null);
    setLatestTask(null);
    setProfile(null);
    setActiveRoute(webAppRoutes[0]);
  }

  return (
    <main className="web-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">AdultGen</p>
          <h1>AI Studio</h1>
          <p className="sidebar-copy">
            Основной продукт — сайт-приложение: генерация, проекты, лента, профиль и биллинг.
            Telegram остаётся companion-каналом для уведомлений, deep links и поддержки.
          </p>
        </div>

        <nav className="route-nav" aria-label="Основная навигация сайта">
          {primaryWebAppRoutes.map((route) => (
            <button
              key={route.id}
              type="button"
              className={route.id === activeRoute.id ? 'route-button active' : 'route-button'}
              onClick={() => setActiveRoute(route)}
            >
              {route.title}
            </button>
          ))}
        </nav>

        <SessionPanel session={session} adultConsent={adultConsent} onLogout={handleLogout} />
      </aside>

      <section className="main-panel">
        <TopBar
          activeRoute={activeRoute}
          statusMessage={statusMessage}
          errorMessage={errorMessage}
          onNavigate={setActiveRoute}
        />

        {routeBlockedByAuth ? (
          <LoginCard
            email={email}
            displayName={displayName}
            setEmail={setEmail}
            setDisplayName={setDisplayName}
            onLogin={() => void handleLogin()}
          />
        ) : routeBlockedByAge ? (
          <AgeGateCard
            onAccept={() => void handleAcceptAdultConsent()}
            onRefresh={() => void handleRefreshConsent()}
          />
        ) : activeRoute.id === 'landing' ? (
          <LandingCard onStart={() => setActiveRoute(webAppRoutes.find((route) => route.id === 'studio') ?? activeRoute)} />
        ) : activeRoute.id === 'ageGate' ? (
          <AgeGateCard
            onAccept={() => void handleAcceptAdultConsent()}
            onRefresh={() => void handleRefreshConsent()}
          />
        ) : activeRoute.id === 'studio' ? (
          <StudioCard
            studio={studio}
            setStudio={setStudio}
            workspace={workspace}
            latestTask={latestTask}
            onPrepareWorkspace={() => void handlePrepareWorkspace()}
            onLaunch={() => void handleLaunchGeneration()}
          />
        ) : activeRoute.id === 'profile' ? (
          <ProfileCard
            profile={profile}
            onLoad={() => void handleLoadProfile()}
            onToggleVisibility={() => void handleToggleProfileVisibility()}
          />
        ) : (
          <ProductSection route={activeRoute} session={session} adultConsent={adultConsent} latestTask={latestTask} />
        )}
      </section>
    </main>
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
    <header className="topbar">
      <div>
        <p className="eyebrow">{activeRoute.path}</p>
        <h2>{activeRoute.title}</h2>
      </div>
      <div className="topbar-actions">
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
    <section className="card stack-card">
      <p className="eyebrow">Website auth</p>
      <h3>Вход в сайт-приложение</h3>
      <p>
        Для MVP используем web session endpoint. Позже этот слой можно заменить на email OTP,
        OAuth, wallet login или полноценную регистрацию без изменения Core token-контракта.
      </p>
      <label>
        Email
        <input value={email} onChange={(event) => setEmail(event.target.value)} />
      </label>
      <label>
        Имя профиля
        <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
      </label>
      <button className="primary-button" type="button" onClick={onLogin}>
        Войти и получить Core token
      </button>
    </section>
  );
}

function AgeGateCard({ onAccept, onRefresh }: { onAccept: () => void; onRefresh: () => void }) {
  return (
    <section className="card stack-card danger-card">
      <p className="eyebrow">18+ safety gate</p>
      <h3>Подтверждение возраста и правил</h3>
      <p>
        Перед доступом к Studio и Feed пользователь подтверждает, что ему есть 18 лет,
        соглашается с blur/moderation-контуром и понимает запреты на minors, public figures,
        non-consensual identity, violence, coercion и hidden camera контент.
      </p>
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
      <div className="card hero-card">
        <p className="eyebrow">Web-first adult AI generation</p>
        <h3>Сайт как основной продукт, Telegram как companion</h3>
        <p>
          UX строится вокруг генератора: prompt, negative prompt, референсы, аватары,
          проекты, лента, коллекция, профиль, биллинг и партнёрский кабинет.
        </p>
        <button className="primary-button" type="button" onClick={onStart}>
          Открыть Studio
        </button>
      </div>
      <MetricCard label="Core API" value="ready" text="Auth, generation, workspace, profiles, collection." />
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
  onPrepareWorkspace,
  onLaunch,
}: {
  studio: StudioState;
  setStudio: (value: StudioState) => void;
  workspace: WorkspaceDraft | null;
  latestTask: GenerationTask | null;
  onPrepareWorkspace: () => void;
  onLaunch: () => void;
}) {
  const estimatedCredits = estimateCredits(studio.mode, studio.duration_seconds);

  return (
    <section className="studio-grid">
      <form className="card stack-card" onSubmit={(event) => event.preventDefault()}>
        <p className="eyebrow">Generation Studio</p>
        <h3>Создание фото/видео</h3>
        <label>
          Режим
          <select
            value={studio.mode}
            onChange={(event) => setStudio({ ...studio, mode: event.target.value as GenerationMode })}
          >
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
          <textarea
            rows={5}
            value={studio.prompt}
            onChange={(event) => setStudio({ ...studio, prompt: event.target.value })}
          />
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
          Reference URLs, по одному на строку
          <textarea
            rows={3}
            value={studio.reference_urls}
            onChange={(event) => setStudio({ ...studio, reference_urls: event.target.value })}
          />
        </label>
        <div className="form-grid">
          <label>
            Aspect ratio
            <select
              value={studio.aspect_ratio}
              onChange={(event) => setStudio({ ...studio, aspect_ratio: event.target.value })}
            >
              <option value="9:16">9:16</option>
              <option value="16:9">16:9</option>
              <option value="1:1">1:1</option>
              <option value="4:5">4:5</option>
            </select>
          </label>
          <label>
            Resolution
            <select
              value={studio.resolution}
              onChange={(event) => setStudio({ ...studio, resolution: event.target.value })}
            >
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
        </div>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={studio.generate_audio}
            onChange={(event) => setStudio({ ...studio, generate_audio: event.target.checked })}
          />
          Generate audio for video
        </label>
        <div className="button-row">
          <button className="ghost-button" type="button" onClick={onPrepareWorkspace}>
            Подготовить проект
          </button>
          <button className="primary-button" type="button" onClick={onLaunch}>
            Запустить за ~{estimatedCredits} credits
          </button>
        </div>
      </form>

      <aside className="card stack-card preview-card">
        <p className="eyebrow">Preview / state</p>
        <h3>Контроль перед запуском</h3>
        <StateRow label="Workspace" value={workspace ? 'готов' : 'не создан'} />
        <StateRow label="Mode" value={studio.mode} />
        <StateRow label="Estimated credits" value={String(estimatedCredits)} />
        <StateRow label="Latest task" value={latestTask ? `${latestTask.status} · ${latestTask.id}` : 'нет'} />
        <p className="hint">
          Для Seedance режимы first frame, first+last и multimodal refs считаются отдельными режимами.
          Studio не смешивает их в один payload.
        </p>
      </aside>
    </section>
  );
}

function ProfileCard({
  profile,
  onLoad,
  onToggleVisibility,
}: {
  profile: Profile | null;
  onLoad: () => void;
  onToggleVisibility: () => void;
}) {
  return (
    <section className="card stack-card">
      <p className="eyebrow">Creator profile</p>
      <h3>Публичный / приватный профиль</h3>
      <StateRow label="Public ID" value={profile?.public_id ?? 'ещё не загружен'} />
      <StateRow label="Visibility" value={profile?.visibility ?? 'unknown'} />
      <StateRow label="Display name" value={profile?.display_name ?? 'not set'} />
      <div className="button-row">
        <button className="ghost-button" type="button" onClick={onLoad}>
          Загрузить профиль
        </button>
        <button className="primary-button" type="button" onClick={onToggleVisibility}>
          Переключить public/private
        </button>
      </div>
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
    <section className="landing-grid">
      <div className="card hero-card">
        <p className="eyebrow">{route.path}</p>
        <h3>{route.title}</h3>
        <p>{route.description}</p>
      </div>
      <MetricCard label="Auth" value={session ? 'yes' : 'no'} text="Protected routes use Core bearer token." />
      <MetricCard label="18+" value={adultConsent?.accepted ? 'accepted' : 'required'} text="Feed/Studio gated by adult consent." />
      <MetricCard label="Latest task" value={latestTask?.status ?? 'none'} text="Generation lifecycle is already wired to Core." />
    </section>
  );
}

function SessionPanel({
  session,
  adultConsent,
  onLogout,
}: {
  session: WebSession | null;
  adultConsent: AdultConsentStatus | null;
  onLogout: () => void;
}) {
  return (
    <section className="session-panel">
      <p className="eyebrow">Session</p>
      <StateRow label="User" value={session?.display_name ?? 'guest'} />
      <StateRow label="Email" value={session?.email ?? 'not signed in'} />
      <StateRow label="Adult gate" value={adultConsent?.accepted ? 'accepted' : 'not accepted'} />
      {session && (
        <button className="ghost-button full-width" type="button" onClick={onLogout}>
          Выйти
        </button>
      )}
    </section>
  );
}

function MetricCard({ label, value, text }: { label: string; value: string; text: string }) {
  return (
    <article className="card metric-card">
      <p className="eyebrow">{label}</p>
      <strong>{value}</strong>
      <span>{text}</span>
    </article>
  );
}

function StateRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="state-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function estimateCredits(mode: GenerationMode, durationSeconds: number): number {
  if (mode.startsWith('image_')) return 10;
  return Math.max(1, durationSeconds) * 20;
}
