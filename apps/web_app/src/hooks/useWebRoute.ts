import { useCallback, useEffect, useState } from 'react';
import { findRouteByPath, type WebAppRoute } from '../routes';

export function useWebRoute() {
  const [route, setRoute] = useState<WebAppRoute>(() => findRouteByPath(window.location.pathname));

  useEffect(() => {
    const handlePopState = () => setRoute(findRouteByPath(window.location.pathname));
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = useCallback((route: WebAppRoute) => {
    if (window.location.pathname !== route.path) window.history.pushState({}, '', route.path);
    setRoute(route);
  }, []);

  return { route, routeId: route.id, navigate };
}
