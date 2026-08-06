import { useEffect, useState } from 'react';

import { App } from './App';
import { createWebSession } from './api';
import { AppShell, Sidebar, TopBar } from './components/AppShell';
import { PublicGeneratorLanding } from './components/PublicGeneratorLanding';
import { useWebRoute } from './hooks/useWebRoute';
import { primaryWebAppRoutes, webAppRoutes, type WebAppRoute } from './routes';
import { loadWebSession, saveWebSession } from './session';

type ShellExtractionStage = 'legacy-app-shell-migration' | 'contract-harness';

function getShellExtractionStage(): ShellExtractionStage {
  return 'legacy-app-shell-migration';
}

function routeFromButton(button: HTMLButtonElement) {
  const title = button.textContent?.trim();
  if (!title) return null;
  return webAppRoutes.find((route) => route.title === title) ?? null;
}

function routeFromSelect(select: HTMLSelectElement) {
  if (select.getAttribute('aria-label') !== 'Route selector') return null;
  return webAppRoutes.find((route) => route.id === select.value) ?? null;
}

function resolveRoute(routeId: WebAppRoute['id']) {
  return webAppRoutes.find((route) => route.id === routeId) ?? null;
}

function shouldRenderPublicLanding(activeRoute: WebAppRoute, hasSession: boolean) {
  return activeRoute.id === 'landing' || (activeRoute.requiresAuth && !hasSession);
}

function ShellContractHarness({ activeRoute, navigate }: { activeRoute: WebAppRoute; navigate: (route: WebAppRoute) => void }) {
  const stage = getShellExtractionStage();
  if (stage !== 'contract-harness') return null;

  return (
    <AppShell
      activeRoute={activeRoute}
      sidebar={
        <Sidebar
          activeRoute={activeRoute}
          routes={primaryWebAppRoutes}
          onNavigate={navigate}
          routeResolver={resolveRoute}
        />
      }
      topbar={
        <TopBar
          activeRoute={activeRoute}
          routes={webAppRoutes}
          statusMessage={null}
          errorMessage={null}
          onNavigate={navigate}
        />
      }
    >
      <span hidden>Shell extraction contract</span>
    </AppShell>
  );
}

export function RoutedUserApp() {
  const [activeRoute, navigate] = useWebRoute();
  const [hasSession, setHasSession] = useState(() => Boolean(loadWebSession()));
  const [isStarting, setIsStarting] = useState(false);

  useEffect(() => {
    function handleClick(event: MouseEvent) {
      const target = event.target instanceof Element ? event.target : null;
      const button = target?.closest<HTMLButtonElement>('.route-button');
      if (!button) return;

      const route = routeFromButton(button);
      if (route) navigate(route);
    }

    function handleChange(event: Event) {
      const target = event.target;
      if (!(target instanceof HTMLSelectElement)) return;

      const route = routeFromSelect(target);
      if (route) navigate(route);
    }

    window.addEventListener('click', handleClick);
    window.addEventListener('change', handleChange);
    return () => {
      window.removeEventListener('click', handleClick);
      window.removeEventListener('change', handleChange);
    };
  }, [navigate]);

  async function startPublicSession() {
    const existingSession = loadWebSession();
    if (existingSession) {
      setHasSession(true);
      navigate(resolveRoute('ageGate') ?? resolveRoute('studio') ?? webAppRoutes[0]);
      return;
    }

    setIsStarting(true);
    try {
      const session = await createWebSession('creator@example.com', 'AdultGen creator');
      saveWebSession(session);
      setHasSession(true);
      navigate(resolveRoute('ageGate') ?? resolveRoute('studio') ?? webAppRoutes[0]);
    } finally {
      setIsStarting(false);
    }
  }

  function openStudio() {
    if (!hasSession) {
      void startPublicSession();
      return;
    }
    navigate(resolveRoute('studio') ?? webAppRoutes[0]);
  }

  const showPublicLanding = shouldRenderPublicLanding(activeRoute, hasSession);

  return (
    <>
      <ShellContractHarness activeRoute={activeRoute} navigate={navigate} />
      {showPublicLanding ? (
        <PublicGeneratorLanding
          blockedRouteTitle={activeRoute.id === 'landing' ? null : activeRoute.title}
          isStarting={isStarting}
          onStart={() => void startPublicSession()}
          onOpenStudio={openStudio}
        />
      ) : (
        <App key={activeRoute.path} />
      )}
    </>
  );
}
