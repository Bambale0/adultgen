import { useMemo, useState } from 'react';

import { findRouteByPath, primaryWebAppRoutes, webAppRoutes, type WebAppRoute } from './routes';

const routeCopy: Record<string, { eyebrow: string; cta: string }> = {
  landing: {
    eyebrow: 'Web-first AI media platform',
    cta: 'Перейти к 18+ gate',
  },
  ageGate: {
    eyebrow: 'Safety before content',
    cta: 'Мне есть 18 лет',
  },
  studio: {
    eyebrow: 'Generation studio',
    cta: 'Создать генерацию',
  },
  projects: {
    eyebrow: 'Workspace',
    cta: 'Открыть проекты',
  },
  avatars: {
    eyebrow: 'Private references',
    cta: 'Добавить аватар',
  },
  feed: {
    eyebrow: 'Adult feed',
    cta: 'Открыть ленту',
  },
  collection: {
    eyebrow: 'Saved media',
    cta: 'Открыть коллекцию',
  },
  profile: {
    eyebrow: 'Creator profile',
    cta: 'Настроить профиль',
  },
  billing: {
    eyebrow: 'Credits and checkout',
    cta: 'Пополнить баланс',
  },
  partners: {
    eyebrow: 'Referral program',
    cta: 'Открыть кабинет',
  },
  support: {
    eyebrow: 'Help desk',
    cta: 'Написать в поддержку',
  },
};

export function App() {
  const initialRoute = useMemo(() => findRouteByPath(window.location.pathname), []);
  const [activeRoute, setActiveRoute] = useState<WebAppRoute>(initialRoute);
  const copy = routeCopy[activeRoute.id];

  return (
    <main className="web-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">AdultGen</p>
          <h1>Web App</h1>
          <p className="sidebar-copy">
            Основной продукт теперь сайт-приложение. Telegram остаётся companion-каналом
            для входа, уведомлений, зеркал и поддержки.
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
      </aside>

      <section className="hero-card">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h2>{activeRoute.title}</h2>
        <p>{activeRoute.description}</p>

        <div className="guard-grid">
          <GuardPill label="Auth" enabled={activeRoute.requiresAuth} />
          <GuardPill label="18+ consent" enabled={activeRoute.requiresAdultConsent} />
          <GuardPill label="Primary route" enabled={activeRoute.isPrimary} />
        </div>

        <button className="primary-button" type="button">
          {copy.cta}
        </button>
      </section>

      <section className="route-map">
        <p className="eyebrow">Route manifest</p>
        {webAppRoutes.map((route) => (
          <button
            key={route.id}
            type="button"
            className={route.id === activeRoute.id ? 'map-row active' : 'map-row'}
            onClick={() => setActiveRoute(route)}
          >
            <span>{route.path}</span>
            <strong>{route.title}</strong>
          </button>
        ))}
      </section>
    </main>
  );
}

function GuardPill({ label, enabled }: { label: string; enabled: boolean }) {
  return <span className={enabled ? 'guard-pill enabled' : 'guard-pill'}>{label}</span>;
}
