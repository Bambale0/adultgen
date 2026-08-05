import { useEffect } from 'react';

import { App } from './App';
import { useWebRoute } from './hooks/useWebRoute';
import { webAppRoutes } from './routes';

function routeFromButton(button: HTMLButtonElement) {
  const title = button.textContent?.trim();
  if (!title) return null;
  return webAppRoutes.find((route) => route.title === title) ?? null;
}

function routeFromSelect(select: HTMLSelectElement) {
  if (select.getAttribute('aria-label') !== 'Route selector') return null;
  return webAppRoutes.find((route) => route.id === select.value) ?? null;
}

export function RoutedUserApp() {
  const [activeRoute, navigate] = useWebRoute();

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

  return <App key={activeRoute.path} />;
}
