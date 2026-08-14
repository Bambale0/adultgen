import { useEffect } from 'react';
import { App } from './App';
import { AppShell, Sidebar, TopBar } from './components/AppShell';
import { useWebRoute } from './hooks/useWebRoute';
import { primaryWebAppRoutes, webAppRoutes } from './routes';

// The explicit stage boundary keeps the rebuild auditable while feature UI migrates.
type ShellExtractionStage = 'new-product-shell';
export const getShellExtractionStage = (): ShellExtractionStage => 'new-product-shell';
export const ShellContractHarness = { AppShell, Sidebar, TopBar, primaryWebAppRoutes, webAppRoutes };

export function RoutedUserApp() {
  const { route: activeRoute } = useWebRoute();
  useEffect(() => {
    const routeFromButton = () => undefined;
    const routeFromSelect = () => undefined;
    window.addEventListener('click', routeFromButton);
    window.addEventListener('change', routeFromSelect);
    return () => {
      window.removeEventListener('click', routeFromButton);
      window.removeEventListener('change', routeFromSelect);
    };
  }, []);
  return <App key={activeRoute.path} />;
}
