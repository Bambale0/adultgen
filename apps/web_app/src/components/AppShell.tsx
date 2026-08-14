import { Coins, LogOut, Menu, Plus, Search, ShieldCheck, Sparkles, X } from 'lucide-react';
import { useState, type ReactNode } from 'react';
import type { WebSession } from '../api';
import type { WebAppRoute } from '../routes';

type SidebarRoute = Pick<WebAppRoute, 'id' | 'title'> & Pick<WebAppRoute, 'icon'>;

export function AppShell({
  children,
  sidebar,
  topbar,
}: {
  children: ReactNode;
  sidebar: ReactNode;
  topbar: ReactNode;
}) {
  return (
    <div className="web-shell">
      {sidebar}
      <div className="shell-main">
        {topbar}
        <main className="page-canvas">{children}</main>
      </div>
    </div>
  );
}

export function Sidebar({
  routes,
  activeRoute,
  routeResolver,
  onNavigate,
  onCreate,
}: {
  routes: SidebarRoute[];
  activeRoute: WebAppRoute;
  routeResolver: (id: WebAppRoute['id']) => WebAppRoute;
  onNavigate: (route: WebAppRoute) => void;
  onCreate: () => void;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = (route: WebAppRoute) => {
    onNavigate(route);
    setMobileOpen(false);
  };

  return (
    <>
      <button className="mobile-menu-button" aria-label="Открыть меню" onClick={() => setMobileOpen(true)}>
        <Menu size={20} />
      </button>
      <aside className="sidebar" data-mobile-open={mobileOpen ? 'true' : 'false'}>
        <div className="brand-row">
          <div className="brand-mark"><Sparkles size={18} /></div>
          <div><strong>ADULTGEN</strong><span>CREATOR SYSTEM</span></div>
          <button className="mobile-close" aria-label="Закрыть меню" onClick={() => setMobileOpen(false)}><X /></button>
        </div>
        <button className="primary-action sidebar-create" onClick={onCreate}><Plus size={17} /> Create</button>
        <nav aria-label="Основная навигация сайта">
          {routes.map((route) => {
            const Icon = route.icon;
            return (
              <button
                className={`route-button ${activeRoute.id === route.id ? 'active' : ''}`}
                key={route.id}
                onClick={() => navigate(routeResolver(route.id))}
              >
                <Icon size={18} />
                <span>{route.title}</span>
              </button>
            );
          })}
        </nav>
        <div className="sidebar-foot">
          <div className="safety-note"><ShieldCheck size={16} /><span>Consent-aware<br />generation</span></div>
          <span className="version-label">SYSTEM 0.1 / BETA</span>
        </div>
      </aside>
      {mobileOpen && <button className="sidebar-scrim" aria-label="Закрыть меню" onClick={() => setMobileOpen(false)} />}
    </>
  );
}

export function TopBar({
  activeRoute,
  routes,
  session,
  balance,
  onNavigate,
  onSignIn,
  onSignOut,
}: {
  activeRoute: WebAppRoute;
  routes: WebAppRoute[];
  session: WebSession | null;
  balance: number | null;
  onNavigate: (route: WebAppRoute) => void;
  onSignIn: () => void;
  onSignOut: () => void;
}) {
  return (
    <header className="topbar">
      <div className="route-context">
        <span>{activeRoute.eyebrow}</span>
        <select
          aria-label="Route selector"
          value={activeRoute.id}
          onChange={(event) => onNavigate(routes.find((route) => route.id === event.target.value) || routes[0])}
        >
          {routes.map((route) => <option key={route.id} value={route.id}>{route.title}</option>)}
        </select>
      </div>
      <label className="search-control"><Search size={17} /><input placeholder="Search creations" /></label>
      <div className="topbar-actions" aria-live="polite">
        {session ? (
          <>
            <button className="credit-pill" onClick={() => onNavigate(routes.find((r) => r.id === 'billing') || routes[0])}>
              <Coins size={16} /><strong>{balance ?? '—'}</strong><span>credits</span>
            </button>
            <button className="profile-chip" onClick={() => onNavigate(routes.find((r) => r.id === 'profile') || routes[0])}>
              <span className="avatar-dot">{session.display_name.slice(0, 1).toUpperCase()}</span>
              <span>{session.display_name}</span>
            </button>
            <button className="icon-button" aria-label="Выйти" onClick={onSignOut}><LogOut size={18} /></button>
          </>
        ) : <button className="secondary-action" onClick={onSignIn}>Sign in</button>}
      </div>
    </header>
  );
}
