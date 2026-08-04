import { useEffect, useMemo, useState } from 'react';

import {
  acceptAdultConsent,
  fetchAdultConsentStatus,
  type AdultConsentStatus,
} from './adultConsent';
import { useTelegramMiniAppAuth } from './auth';
import { CreateFlowStarter } from './createFlow';
import { PlaceholderPage } from './pages';
import { findRouteByPath, primaryNavRouteIds, routes, type MiniAppRouteId } from './routes';
import { prepareTelegramViewport } from './telegram';

export function App() {
  const authState = useTelegramMiniAppAuth();
  const initialRoute = useMemo(() => findRouteByPath(window.location.pathname), []);
  const [activeRouteId, setActiveRouteId] = useState<MiniAppRouteId>(initialRoute.id);
  const [adultConsent, setAdultConsent] = useState<AdultConsentStatus | null>(null);
  const [adultConsentError, setAdultConsentError] = useState<string | null>(null);
  const activeRoute = routes.find((route) => route.id === activeRouteId) ?? routes[0];

  useEffect(() => {
    prepareTelegramViewport();
  }, []);

  useEffect(() => {
    if (authState.status !== 'authenticated') return;

    let cancelled = false;
    async function loadAdultConsent() {
      try {
        const status = await fetchAdultConsentStatus(authState.session.access_token);
        if (!cancelled) setAdultConsent(status);
      } catch (error) {
        if (!cancelled) {
          setAdultConsentError(
            error instanceof Error ? error.message : 'Adult consent status failed.',
          );
        }
      }
    }

    void loadAdultConsent();
    return () => {
      cancelled = true;
    };
  }, [authState]);

  if (authState.status === 'loading') {
    return <StatusScreen title="Проверяем вход" description="Подтверждаем Telegram initData на сервере." />;
  }

  if (authState.status === 'missing-telegram') {
    return (
      <StatusScreen
        title="Откройте через Telegram"
        description="Mini App должен запускаться из Telegram, чтобы backend мог проверить initData."
      />
    );
  }

  if (authState.status === 'error') {
    return <StatusScreen title="Ошибка авторизации" description={authState.message} />;
  }

  const feedBlockedByAdultGate = activeRoute.requiresAdultConsent && !adultConsent?.accepted;

  async function handleAcceptAdultConsent() {
    if (authState.status !== 'authenticated') return;
    setAdultConsentError(null);
    try {
      const status = await acceptAdultConsent(authState.session.access_token);
      setAdultConsent(status);
    } catch (error) {
      setAdultConsentError(
        error instanceof Error ? error.message : 'Adult consent accept failed.',
      );
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <span className="brand">AdultGen</span>
        <span className="status-pill">user #{authState.session.telegram_user_id}</span>
      </header>

      {authState.session.is_blocked ? (
        <StatusScreen
          title="Аккаунт ограничен"
          description="Доступ к приложению ограничен. Обратитесь в поддержку."
        />
      ) : feedBlockedByAdultGate ? (
        <AdultGate
          policyVersion={adultConsent?.policy_version ?? 'adult-policy-v1'}
          error={adultConsentError}
          onAccept={() => void handleAcceptAdultConsent()}
        />
      ) : activeRoute.id === 'create' ? (
        <CreateFlowStarter accessToken={authState.session.access_token} />
      ) : (
        <PlaceholderPage routeId={activeRoute.id} />
      )}

      {!authState.session.is_blocked && (
        <nav className="bottom-nav" aria-label="Основная навигация">
          {primaryNavRouteIds.map((routeId) => {
            const route = routes.find((item) => item.id === routeId);
            if (!route) return null;

            return (
              <button
                key={route.id}
                className={route.id === activeRouteId ? 'nav-button active' : 'nav-button'}
                type="button"
                onClick={() => setActiveRouteId(route.id)}
              >
                {route.title}
              </button>
            );
          })}
        </nav>
      )}
    </main>
  );
}

function StatusScreen({ title, description }: { title: string; description: string }) {
  return (
    <main className="app-shell centered-shell">
      <section className="page-card compact-card">
        <p className="eyebrow">Mini App Auth</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </section>
    </main>
  );
}

function AdultGate({
  policyVersion,
  error,
  onAccept,
}: {
  policyVersion: string;
  error: string | null;
  onAccept: () => void;
}) {
  return (
    <section className="page-card adult-gate-card">
      <p className="eyebrow">18+ consent · {policyVersion}</p>
      <h1>Лента 18+</h1>
      <p>
        В ленте может быть откровенный контент. Подтвердите, что вам есть 18 лет,
        вы понимаете правила и соглашаетесь с blur/moderation-контуром.
      </p>
      {error && <p className="error-text">{error}</p>}
      <button className="primary-button" type="button" onClick={onAccept}>
        Мне есть 18 лет, открыть ленту
      </button>
    </section>
  );
}
