import { Aperture, Boxes, Clapperboard, Compass, CreditCard, Images, UserRound } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export type WebAppRouteId =
  | 'discover'
  | 'studio'
  | 'generations'
  | 'projects'
  | 'avatars'
  | 'billing'
  | 'profile';

export type WebAppRoute = {
  id: WebAppRouteId;
  path: string;
  title: string;
  eyebrow: string;
  icon: LucideIcon;
  protected: boolean;
};

export const webAppRoutes: WebAppRoute[] = [
  { id: 'discover', path: '/', title: 'Discover', eyebrow: 'Curated signal', icon: Compass, protected: false },
  { id: 'studio', path: '/studio', title: 'Create', eyebrow: 'Generation studio', icon: Aperture, protected: true },
  { id: 'generations', path: '/generations', title: 'Generations', eyebrow: 'Live queue', icon: Clapperboard, protected: true },
  { id: 'projects', path: '/projects', title: 'Projects', eyebrow: 'Scenes and stories', icon: Boxes, protected: true },
  { id: 'avatars', path: '/avatars', title: 'Assets', eyebrow: 'Private identities', icon: Images, protected: true },
  { id: 'billing', path: '/billing', title: 'Plans & credits', eyebrow: 'Wallet', icon: CreditCard, protected: true },
  { id: 'profile', path: '/profile', title: 'Profile', eyebrow: 'Creator identity', icon: UserRound, protected: true },
];

export const primaryWebAppRoutes = webAppRoutes;

export function findRouteByPath(pathname: string): WebAppRoute {
  return webAppRoutes.find((route) => route.path === pathname) || webAppRoutes[0];
}
