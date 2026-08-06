import type { ReactNode } from 'react';

import type { WebAppRoute } from '../routes';

type SidebarRoute = Pick<WebAppRoute, 'id' | 'title'>;

type SidebarProps = {
  activeRoute: WebAppRoute;
  routes: SidebarRoute[];
  walletCreditsLabel?: string | null;
  onNavigate: (route: WebAppRoute) => void;
  routeResolver: (routeId: WebAppRoute['id']) => WebAppRoute | null;
  sessionPanel?: ReactNode;
};

type TopBarProps = {
  activeRoute: WebAppRoute;
  routes: WebAppRoute[];
  statusMessage: string | null;
  errorMessage: string | null;
  onNavigate: (route: WebAppRoute) => void;
};

type AppShellProps = {
  activeRoute: WebAppRoute;
  sidebar: ReactNode;
  topbar: ReactNode;
  children: ReactNode;
};

export function AppShell({ activeRoute, sidebar, topbar, children }: AppShellProps) {
  return (
    <main className="web-shell" data-route-id={activeRoute.id}>
      {sidebar}
      <section className="main-panel">
        {topbar}
        {children}
      </section>
    </main>
  );
}

export function Sidebar({
  activeRoute,
  routes,
  walletCreditsLabel,
  onNavigate,
  routeResolver,
  sessionPanel,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <div>
        <p className="eyebrow">AdultGen</p>
        <h1>AI Studio</h1>
        <p className="sidebar-copy">
          Основной продукт — сайт-приложение: генерация, медиа, публикации, лента, профиль и биллинг.
          Telegram остаётся companion-каналом для уведомлений, deep links и поддержки.
        </p>
        {walletCreditsLabel && <span className="status-pill">{walletCreditsLabel}</span>}
      </div>
      <nav className="route-nav" aria-label="Основная навигация сайта">
        {routes.map((route) => {
          const resolvedRoute = routeResolver(route.id);
          return (
            <button
              key={route.id}
              type="button"
              className={route.id === activeRoute.id ? 'route-button active' : 'route-button'}
              onClick={() => {
                if (resolvedRoute) onNavigate(resolvedRoute);
              }}
            >
              {route.title}
            </button>
          );
        })}
      </nav>
      {sessionPanel}
    </aside>
  );
}

export function TopBar({ activeRoute, routes, statusMessage, errorMessage, onNavigate }: TopBarProps) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">{activeRoute.path}</p>
        <h2>{activeRoute.title}</h2>
      </div>
      <div className="topbar-actions" aria-live="polite">
        <select
          aria-label="Route selector"
          value={activeRoute.id}
          onChange={(event) => {
            const nextRoute = routes.find((route) => route.id === event.target.value);
            if (nextRoute) onNavigate(nextRoute);
          }}
        >
          {routes.map((route) => (
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
