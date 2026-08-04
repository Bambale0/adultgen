import routeManifest from '../routes.manifest.json';

export type MiniAppRouteId =
  | 'home'
  | 'feed'
  | 'create'
  | 'projects'
  | 'profile'
  | 'avatars'
  | 'balance'
  | 'partner'
  | 'settings'
  | 'support';

export type MiniAppRoute = {
  id: MiniAppRouteId;
  path: string;
  title: string;
  requiresAuth: boolean;
  requiresAdultConsent: boolean;
};

export const routes = routeManifest as MiniAppRoute[];

export const primaryNavRouteIds: MiniAppRouteId[] = [
  'home',
  'feed',
  'create',
  'projects',
  'profile',
];

export function findRouteByPath(pathname: string): MiniAppRoute {
  return routes.find((route) => route.path === pathname) ?? routes[0];
}
