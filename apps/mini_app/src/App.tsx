import { useMemo, useState } from 'react';

import { PlaceholderPage } from './pages';
import { findRouteByPath, primaryNavRouteIds, routes, type MiniAppRouteId } from './routes';

export function App() {
  const initialRoute = useMemo(() => findRouteByPath(window.location.pathname), []);
  const [activeRouteId, setActiveRouteId] = useState<MiniAppRouteId>(initialRoute.id);
  const activeRoute = routes.find((route) => route.id === activeRouteId) ?? routes[0];

  return (
    <main className="app-shell">
      <header className="topbar">
        <span className="brand">AdultGen</span>
        <span className="status-pill">MVP shell</span>
      </header>

      <PlaceholderPage routeId={activeRoute.id} />

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
    </main>
  );
}
