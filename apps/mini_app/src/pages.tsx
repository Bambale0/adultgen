import type { MiniAppRouteId } from './routes';

type PageCopy = {
  eyebrow: string;
  title: string;
  description: string;
};

const pageCopy: Record<MiniAppRouteId, PageCopy> = {
  home: {
    eyebrow: 'AdultGen',
    title: 'Главная',
    description: 'Стартовая точка Mini App: быстрый вход в создание, баланс, проекты и ленту.',
  },
  feed: {
    eyebrow: '18+ gate required',
    title: 'Лента',
    description: 'Единая вертикальная лента с blur/consent-контуром, лайками, коллекцией и ремиксами.',
  },
  create: {
    eyebrow: 'Generation flow',
    title: 'Создать',
    description: 'Создание сцены: аватар, основной кадр, референсы, движение, звук и расчёт стоимости.',
  },
  projects: {
    eyebrow: 'Workspace',
    title: 'Проекты',
    description: 'Список проектов, сцен, статусов генерации и утверждённых дублей.',
  },
  profile: {
    eyebrow: 'Public/private',
    title: 'Профиль',
    description: 'Публичный или приватный профиль, опубликованные работы и реферальная ссылка.',
  },
  avatars: {
    eyebrow: 'Private references',
    title: 'Мои аватары',
    description: 'Приватные наборы фото для сохранения внешности персонажа в генерациях.',
  },
  balance: {
    eyebrow: 'Wallet ledger',
    title: 'Баланс',
    description: 'Кредиты, покупки, подписочные и бонусные начисления с правильным порядком списания.',
  },
  partner: {
    eyebrow: 'Referral',
    title: 'Партнёрский кабинет',
    description: 'Комиссии, pending/available баланс и ручные заявки на вывод.',
  },
  settings: {
    eyebrow: 'Safety',
    title: 'Настройки / 18+',
    description: 'Adult consent, blur-настройки и контроль показа откровенного контента.',
  },
  support: {
    eyebrow: 'Help',
    title: 'Поддержка',
    description: 'Канал для ошибок генерации, платежей, доступа и спорных случаев.',
  },
};

export function PlaceholderPage({ routeId }: { routeId: MiniAppRouteId }) {
  const copy = pageCopy[routeId];

  return (
    <section className="page-card">
      <p className="eyebrow">{copy.eyebrow}</p>
      <h1>{copy.title}</h1>
      <p>{copy.description}</p>
    </section>
  );
}
