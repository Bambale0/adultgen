export type WebAppRouteId =
  | 'landing'
  | 'ageGate'
  | 'studio'
  | 'projects'
  | 'avatars'
  | 'feed'
  | 'collection'
  | 'profile'
  | 'billing'
  | 'partners'
  | 'support';

export type WebAppRoute = {
  id: WebAppRouteId;
  path: string;
  title: string;
  description: string;
  requiresAuth: boolean;
  requiresAdultConsent: boolean;
  isPrimary: boolean;
};

export const webAppRoutes: WebAppRoute[] = [
  {
    id: 'landing',
    path: '/',
    title: 'Главная',
    description: 'Публичный лендинг и вход в продукт.',
    requiresAuth: false,
    requiresAdultConsent: false,
    isPrimary: false,
  },
  {
    id: 'ageGate',
    path: '/age-gate',
    title: '18+',
    description: 'Подтверждение возраста и политики безопасности.',
    requiresAuth: false,
    requiresAdultConsent: false,
    isPrimary: false,
  },
  {
    id: 'studio',
    path: '/studio',
    title: 'Студия',
    description: 'Основной генератор: prompt, refs, модель, цена и запуск.',
    requiresAuth: true,
    requiresAdultConsent: true,
    isPrimary: true,
  },
  {
    id: 'projects',
    path: '/projects',
    title: 'Проекты',
    description: 'Проекты, сцены, статусы и результаты.',
    requiresAuth: true,
    requiresAdultConsent: true,
    isPrimary: true,
  },
  {
    id: 'avatars',
    path: '/avatars',
    title: 'Аватары',
    description: 'Приватные visual identity референсы.',
    requiresAuth: true,
    requiresAdultConsent: true,
    isPrimary: true,
  },
  {
    id: 'feed',
    path: '/feed',
    title: 'Лента',
    description: 'Общая лента с blur, likes, saves, remix и report.',
    requiresAuth: true,
    requiresAdultConsent: true,
    isPrimary: true,
  },
  {
    id: 'collection',
    path: '/collection',
    title: 'Коллекция',
    description: 'Сохранённые публикации пользователя.',
    requiresAuth: true,
    requiresAdultConsent: true,
    isPrimary: true,
  },
  {
    id: 'profile',
    path: '/profile',
    title: 'Профиль',
    description: 'Публичный или приватный профиль автора.',
    requiresAuth: true,
    requiresAdultConsent: true,
    isPrimary: true,
  },
  {
    id: 'billing',
    path: '/billing',
    title: 'Баланс',
    description: 'Кредиты, пакеты, подписки и checkout.',
    requiresAuth: true,
    requiresAdultConsent: false,
    isPrimary: true,
  },
  {
    id: 'partners',
    path: '/partners',
    title: 'Партнёрам',
    description: 'Реферальная программа и выплаты.',
    requiresAuth: true,
    requiresAdultConsent: false,
    isPrimary: false,
  },
  {
    id: 'support',
    path: '/support',
    title: 'Поддержка',
    description: 'Помощь по генерациям, оплатам и аккаунту.',
    requiresAuth: false,
    requiresAdultConsent: false,
    isPrimary: false,
  },
];

export const primaryWebAppRoutes = webAppRoutes.filter((route) => route.isPrimary);

export function findRouteByPath(pathname: string): WebAppRoute {
  return webAppRoutes.find((route) => route.path === pathname) ?? webAppRoutes[0];
}
