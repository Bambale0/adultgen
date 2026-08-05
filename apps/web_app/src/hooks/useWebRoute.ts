import { useCallback, useEffect, useState } from 'react';

import { findRouteByPath, type WebAppRoute } from '../routes';

function currentRoute(): WebAppRoute {
  return findRouteByPath(window.location.pathname);
}

export function useWebRoute(): [WebAppRoute, (route: WebAppRoute) => void] {
  const [activeRoute, setActiveRoute] = useState<WebAppRoute>(() => currentRoute());

  useEffect(() => {
    function handlePopState() {
      setActiveRoute(currentRoute());
    }

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = useCallback((route: WebAppRoute) => {
    setActiveRoute(route);
    if (window.location.pathname !== route.path) {
      window.history.pushState({ routeId: route.id }, '', route.path);
    }
  }, []);

  return [activeRoute, navigate];
}
