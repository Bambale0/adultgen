import { useEffect, useMemo, useState } from 'react';

import { useTelegramMiniAppAuth } from './auth';
import { PlaceholderPage } from './pages';
import { findRouteByPath, primaryNavRouteIds, routes, type MiniAppRouteId } from './routes';
import { prepareTelegramViewport } from './telegram';

export function App() {
  const authState = useTelegramMiniAppAuth();
  const initialRoute = useMemo(() => findRouteByPath(window.location.pathname), []);
  const [activeRouteId, setActiveRouteId] = useState<MiniAppRouteId>(initialRoute.id);
  const activeRoute = routes.find((route) => route.id === activeRouteId) ?? routes[0];

  useEffect(() => {
    prepareTelegramViewport();
  }, []);

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
