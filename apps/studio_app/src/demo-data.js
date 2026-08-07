import { FEED_UNIT } from "./media/feed-unit.js";

function sceneData({ start, end, accent, label, motif = "orb" }) {
  const shape = motif === "rider"
    ? '<path d="M180 430c55-110 150-176 282-170l92 60-76 42-116-14-84 92z" fill="rgba(8,10,16,.78)"/><circle cx="392" cy="287" r="62" fill="rgba(8,10,16,.85)"/>'
    : motif === "city"
      ? '<path d="M0 390 92 244l74 96 74-156 94 180 82-210 96 236v250H0z" fill="rgba(5,7,15,.78)"/><path d="M70 160h30v300H70zm148-80h38v380h-38zm178 70h28v310h-28z" fill="rgba(255,255,255,.08)"/>'
      : motif === "android"
        ? '<ellipse cx="300" cy="280" rx="112" ry="146" fill="rgba(5,7,12,.82)"/><path d="M202 240h196M220 306h160M300 134v292" stroke="rgba(255,255,255,.18)" stroke-width="3"/>'
        : '<circle cx="300" cy="300" r="150" fill="none" stroke="rgba(255,255,255,.2)" stroke-width="28"/><circle cx="300" cy="300" r="76" fill="rgba(5,7,12,.8)"/>';
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="760" viewBox="0 0 600 760"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${start}"/><stop offset="1" stop-color="${end}"/></linearGradient><filter id="n"><feTurbulence baseFrequency=".75" numOctaves="2" seed="8" type="fractalNoise"/><feColorMatrix values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 .14 0"/></filter></defs><rect width="600" height="760" fill="url(#g)"/><rect width="600" height="760" filter="url(#n)" opacity=".28"/>${shape}<path d="M0 590 600 360v400H0z" fill="${accent}" opacity=".14"/><g fill="none" stroke="${accent}" opacity=".35"><path d="M40 64h170M390 690h170"/><path d="M60 100v130M540 530v130"/></g><text x="40" y="700" fill="white" opacity=".7" font-family="monospace" font-size="18" letter-spacing="4">${label}</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

const CITY = sceneData({ start: "#10152f", end: "#4a0e5f", accent: "#22d3ee", label: "NIGHT DISTRICT", motif: "city" });
const CYBORG = sceneData({ start: "#17181e", end: "#54535e", accent: "#ff2bbd", label: "SYNTHETIC", motif: "android" });
const BIKE = sceneData({ start: "#130917", end: "#661246", accent: "#ff2bbd", label: "HYPERDRIVE", motif: "rider" });
const OPERATOR = sceneData({ start: "#081d27", end: "#32133d", accent: "#22d3ee", label: "VANGUARD", motif: "orb" });

export const demoPublications = [
  {
    id: "neon-rain-01",
    title: "NEON RAIN // 01",
    author: "@lilac.proto",
    media: FEED_UNIT,
    aspect: "portrait",
    model: "Seedream 5 Pro",
    status: "SYNCED",
    likes: 18420,
    views: 128400,
    tags: ["portrait", "neon", "cinematic"],
    description: "Кинематографичный портрет в дождливом неоновом мегаполисе. Сохранён характер света и силуэт персонажа.",
    trending: true,
    following: true,
    explicit: false,
  },
  {
    id: "night-district",
    title: "NIGHT DISTRICT",
    author: "@nexus.frame",
    media: CITY,
    aspect: "landscape",
    model: "Seedream 5 Pro",
    status: "PUBLIC",
    likes: 9310,
    views: 74300,
    tags: ["city", "environment", "purple"],
    description: "Визуальное исследование ночного района: высокий контраст, дождь и глубокая перспектива.",
    trending: true,
    following: false,
    explicit: false,
  },
  {
    id: "synthetic-portrait",
    title: "SYNTHETIC PORTRAIT",
    author: "@operator.k3n",
    media: CYBORG,
    aspect: "tall",
    model: "Seedream 5 Pro",
    status: "REMIXABLE",
    likes: 12770,
    views: 88900,
    tags: ["portrait", "monochrome", "android"],
    description: "Сдержанный монохромный портрет с техническими деталями и мягким светом.",
    trending: false,
    following: true,
    explicit: false,
  },
  {
    id: "hyperdrive",
    title: "HYPERDRIVE",
    author: "@velocity.lab",
    media: BIKE,
    aspect: "landscape",
    model: "Seedance 2.0",
    status: "VIDEO",
    likes: 22140,
    views: 192300,
    tags: ["vehicle", "motion", "video"],
    description: "Динамический тест движения камеры и светового следа для короткой видеосцены.",
    trending: true,
    following: true,
    explicit: false,
  },
  {
    id: "vanguard-frame",
    title: "VANGUARD FRAME",
    author: "@operator.01",
    media: OPERATOR,
    aspect: "tall",
    model: "Seedance 2.0",
    status: "SECURE",
    likes: 15620,
    views: 104900,
    tags: ["character", "cockpit", "reference"],
    description: "Первый кадр для видеосцены. Акцент на характере персонажа и интерфейсном свете кабины.",
    trending: false,
    following: false,
    explicit: false,
  },
];

export const demoProfile = {
  publicId: "operator-01",
  displayName: "OPERATOR_01",
  handle: "@operator.01",
  bio: "AI-режиссёр и автор cinematic-сцен. Собираю персонажей, свет и движение в единый визуальный протокол.",
  avatar: FEED_UNIT,
  stats: [
    { label: "Публикации", value: "124" },
    { label: "Реакции", value: "98.4K" },
    { label: "Ремиксы", value: "1.024" },
  ],
};
