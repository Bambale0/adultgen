import { ApiClient } from "./api.js";
import { demoProfile, demoPublications } from "./demo-data.js";
import { buildGenerationPayload, escapeHtml, estimateCredits, filterFeed, formatCompactNumber, parseRoute, readBoolean } from "./core.js";
import { icon } from "./icons.js";

const root = document.querySelector("#app");
const api = new ApiClient();
const tg = globalThis.Telegram?.WebApp;

const state = {
  route: parseRoute(location.pathname),
  feed: demoPublications,
  tab: "live",
  query: "",
  demo: true,
  ageConfirmed: readBoolean(localStorage, "adultgen.age-confirmed"),
  toast: null,
  create: {
    mode: "image",
    prompt: "Кинематографичный портрет взрослого персонажа в неоновом городе, мокрый асфальт, глубокий контраст, реалистичная оптика",
    aspectRatio: "9:16",
    duration: 5,
    resolution: "720p",
    returnLastFrame: true,
    allowRemix: true,
    publishToFeed: false,
    promptPublic: false,
    referenceDataUrl: "",
    referenceName: "",
  },
};

const nav = [
  ["/feed", "feed", "Лента", "feed"],
  ["/create", "create", "Создать", "create"],
  ["/projects", "projects", "Проекты", "projects"],
  ["/profile/operator-01", "profile", "Профиль", "profile"],
];

function go(path) {
  history.pushState({}, "", path);
  state.route = parseRoute(path);
  scrollTo({ top: 0, behavior: "instant" });
  render();
}

function isActive(id) {
  const current = state.route.name === "publication" ? "feed" : state.route.name;
  return current === id;
}

function shell(content, className = "") {
  const navMarkup = nav.map(([route, id, label, glyph]) => `<button class="nav-item ${isActive(id) ? "is-active" : ""}" data-route="${route}">${icon(glyph, 20)}<span>${label}</span></button>`).join("");
  return `<div class="scanlines" aria-hidden="true"></div>
    <div class="shell ${className}">
      <aside class="sidebar">
        <button class="brand" data-route="/feed"><b>AG</b><span><strong>ADULTGEN</strong><small>NEURAL MEDIA STUDIO</small></span></button>
        <div class="core-status"><i></i>${state.demo ? "DEMO CHANNEL" : "CORE LINK ACTIVE"}</div>
        <nav>${navMarkup}</nav>
        <div class="sidebar-foot"><button class="balance" data-route="/billing"><span>Баланс</span><strong>420 CR</strong><small>Пополнить →</small></button><p>${icon("shield", 15)} 18+ / SAFE POLICY</p></div>
      </aside>
      <header class="topbar"><button class="mobile-brand" data-route="/feed"><b>AG</b><span>ADULTGEN</span></button><span class="top-signal"><i></i>${state.demo ? "DEMO" : "CORE API"}</span><div><button class="icon-btn" data-focus-search aria-label="Поиск">${icon("search", 19)}</button><button class="credit" data-route="/billing">${icon("wallet", 16)} 420</button><button class="avatar" data-route="/profile/operator-01"><img src="${demoProfile.avatar}" alt="Профиль" /></button></div></header>
      <main id="main-content" class="content" tabindex="-1">${content}</main>
      <nav class="mobile-nav">${navMarkup}</nav>
    </div>
    ${state.toast ? `<div class="toast ${state.toast.type}"><strong>${escapeHtml(state.toast.title)}</strong><span>${escapeHtml(state.toast.message)}</span></div>` : ""}
    ${state.ageConfirmed ? "" : ageGate()}`;
}

function feedPage() {
  const items = filterFeed(state.feed, state.query, state.tab);
  return shell(`<section class="page feed-page">
    <header class="feed-tools"><div class="tabs">${[["live", "LIVE"], ["trending", "В ТРЕНДЕ"], ["following", "ПОДПИСКИ"]].map(([id, label]) => `<button class="${state.tab === id ? "is-active" : ""}" data-tab="${id}">${label}</button>`).join("")}</div><label class="search">${icon("search", 17)}<input id="feed-search" type="search" value="${escapeHtml(state.query)}" placeholder="Поиск по ленте..." /></label><button class="primary" data-route="/create">${icon("create", 17)} СОЗДАТЬ</button></header>
    <div class="heading"><div><span>PUBLIC SIGNAL // 18+</span><h1>ПУЛЬС СООБЩЕСТВА</h1></div><p>${items.length} публикаций</p></div>
    ${items.length ? `<div class="feed-grid">${items.map(card).join("")}</div>` : empty("Ничего не найдено", "Измени запрос или режим ленты.")}
  </section>`);
}

function card(item, index = 0) {
  return `<article class="card ${escapeHtml(item.aspect)}" style="--delay:${index * 40}ms"><button class="card-media" data-route="/publication/${encodeURIComponent(item.id)}"><img src="${escapeHtml(item.media)}" alt="${escapeHtml(item.title)}" loading="${index > 2 ? "lazy" : "eager"}" /><span class="grid-overlay"></span><em>${escapeHtml(item.status)}</em></button><div class="card-body"><div><h2>${escapeHtml(item.title)}</h2><p>${escapeHtml(item.author)} · ${escapeHtml(item.model)}</p></div><div class="metrics"><span>${icon("heart", 14)}${formatCompactNumber(item.likes)}</span><span>${formatCompactNumber(item.views)} VIEWS</span></div><div class="tags">${item.tags.map((tag) => `<span>#${escapeHtml(tag)}</span>`).join("")}</div></div></article>`;
}

function createPage() {
  const form = state.create;
  return shell(`<section class="page create-page"><header class="create-head"><div><span>GENERATION CONSOLE</span><h1>СОЗДАТЬ СЦЕНУ</h1><p>Промпт, референс и параметры отправляются в существующий Core API.</p></div><b>${icon("shield", 15)} POLICY ACTIVE</b></header>
    <form id="generation-form" class="composer"><div class="composer-main">
      <section class="panel"><header><i>01</i><h2>РЕФЕРЕНС</h2><small>OPTIONAL</small></header><label class="dropzone ${form.referenceDataUrl ? "has-image" : ""}" for="reference-file">${form.referenceDataUrl ? `<img src="${form.referenceDataUrl}" alt="Референс" />` : `${icon("upload", 34)}<strong>ВЫБЕРИ ФАЙЛ</strong><span>JPG, PNG, WEBP · до 25 MB</span>`}<input id="reference-file" type="file" accept="image/jpeg,image/png,image/webp" /></label>${form.referenceName ? `<div class="file-chip">${escapeHtml(form.referenceName)}<button type="button" data-remove-reference>${icon("close", 15)}</button></div>` : ""}</section>
      <section class="panel"><header><i>02</i><h2>ПРОМПТ</h2><small>${form.prompt.length}/1200</small></header><textarea id="generation-prompt" maxlength="1200" required>${escapeHtml(form.prompt)}</textarea><div class="prompt-tools"><button type="button" data-preset="cinematic">CINEMATIC</button><button type="button" data-preset="portrait">PORTRAIT</button><button type="button" data-preset="motion">MOTION</button></div></section>
      <section class="terminal"><p>&gt; CORE_API <strong>READY</strong></p><p>&gt; SAFETY POLICY <strong>ENFORCED</strong></p><p>&gt; ESTIMATED RESERVE <strong>${estimateCredits(form)} CR</strong></p></section>
    </div><aside class="panel settings"><header><i>03</i><h2>ПАРАМЕТРЫ</h2></header><fieldset><legend>Результат</legend><div class="segments"><button type="button" class="${form.mode === "image" ? "is-active" : ""}" data-mode="image">ИЗОБРАЖЕНИЕ</button><button type="button" class="${form.mode === "video" ? "is-active" : ""}" data-mode="video">ВИДЕО</button></div></fieldset><label>Модель<select disabled><option>${form.mode === "video" ? "Seedance 2.0" : form.referenceDataUrl ? "Seedream 5 Pro · Edit" : "Seedream 5 Pro · T2I"}</option></select></label><fieldset><legend>Формат</legend><div class="ratios">${["9:16", "1:1", "16:9"].map((ratio) => `<button type="button" class="${form.aspectRatio === ratio ? "is-active" : ""}" data-ratio="${ratio}">${ratio}</button>`).join("")}</div></fieldset>${form.mode === "video" ? `<label>Длительность <output>${form.duration}s</output><input id="duration-range" type="range" min="5" max="15" step="5" value="${form.duration}" /></label>` : ""}<div class="switches"><label><input type="checkbox" data-toggle="allowRemix" ${form.allowRemix ? "checked" : ""} />Разрешить ремикс</label><label><input type="checkbox" data-toggle="publishToFeed" ${form.publishToFeed ? "checked" : ""} />После проверки — в ленту</label></div><button class="launch" type="submit">ЗАПУСТИТЬ · ${estimateCredits(form)} CR ${icon("arrow", 18)}</button><small>Фактическая стоимость и policy-check подтверждаются сервером.</small></aside></form>
  </section>`);
}

function publicationPage(id) {
  const item = state.feed.find((entry) => entry.id === id) || state.feed[0];
  return shell(`<section class="detail"><div class="detail-media"><img src="${escapeHtml(item.media)}" alt="${escapeHtml(item.title)}" /><span class="grid-overlay"></span><div><button class="float-btn">${icon("heart", 20)}</button><button class="float-btn" data-route="/create">${icon("remix", 20)}</button></div></div><div class="detail-copy"><header><div><span>PUBLICATION // ${escapeHtml(item.status)}</span><h1>${escapeHtml(item.title)}</h1><p>${escapeHtml(item.author)} · ${escapeHtml(item.model)}</p></div><button class="icon-btn" data-route="/feed">${icon("close", 20)}</button></header><div class="telemetry"><div><span>LIKES</span><strong>${formatCompactNumber(item.likes)}</strong></div><div><span>VIEWS</span><strong>${formatCompactNumber(item.views)}</strong></div><div><span>FORMAT</span><strong>${escapeHtml(item.aspect)}</strong></div></div><section><h2>ОПИСАНИЕ</h2><p>${escapeHtml(item.description)}</p><div class="tags">${item.tags.map((tag) => `<span>#${escapeHtml(tag)}</span>`).join("")}</div></section><div class="detail-actions"><button class="primary" data-route="/create">${icon("remix", 17)} СОЗДАТЬ РЕМИКС</button><button class="secondary">СОХРАНИТЬ</button></div><section class="log"><h2>СИСТЕМНЫЙ ЛОГ</h2><article><img src="${demoProfile.avatar}" alt="" /><div><strong>@operator.01</strong><span>T-00:04:12</span><p>Композиция и световая схема сохранены.</p></div></article><article><img src="${state.feed[2]?.media || demoProfile.avatar}" alt="" /><div><strong>CORE_MOD</strong><span>T-00:02:45</span><p>Проверка завершена. Публикация доступна для ремикса.</p></div></article></section></div></section>`, "immersive");
}

function profilePage() {
  const p = demoProfile;
  return shell(`<section class="page profile-page"><header class="profile panel"><img src="${p.avatar}" alt="${escapeHtml(p.displayName)}" /><div><span>CREATOR PROFILE // VERIFIED</span><h1>${escapeHtml(p.displayName)}</h1><p>${escapeHtml(p.bio)}</p><div><button class="primary" data-route="/create">${icon("create", 17)} СОЗДАТЬ</button><button class="secondary">РЕДАКТИРОВАТЬ</button></div></div><aside>${p.stats.map((stat) => `<div><span>${escapeHtml(stat.label)}</span><strong>${escapeHtml(stat.value)}</strong></div>`).join("")}</aside></header><div class="heading"><div><span>CREATOR ARCHIVE</span><h2>ПУБЛИКАЦИИ</h2></div></div><div class="profile-grid">${state.feed.map(card).join("")}</div></section>`);
}

function placeholder(title, text, action = "") {
  return shell(`<section class="page placeholder">${empty(title, text, action)}</section>`);
}

function billingPage() {
  return shell(`<section class="page placeholder"><div class="billing panel"><span>CREDIT SYSTEM</span><h1>420 CR</h1><p>Демонстрационный баланс. Платёжный UI подключается к существующим billing endpoints отдельным срезом.</p><div><button><strong>500 CR</strong><span>STARTER</span></button><button class="featured"><strong>1500 CR</strong><span>CREATOR</span></button><button><strong>5000 CR</strong><span>STUDIO</span></button></div></div></section>`);
}

function empty(title, text, action = "") {
  return `<div class="empty">${icon("feed", 31)}<h2>${title}</h2><p>${text}</p>${action}</div>`;
}

function ageGate() {
  return `<div class="age-gate" role="dialog" aria-modal="true"><div><b>18+</b><span>AGE & CONSENT GATE</span><h2>ДОСТУП ТОЛЬКО ДЛЯ ВЗРОСЛЫХ</h2><p>Запрещены материалы с несовершеннолетними, насилием, принуждением, эксплуатацией и использованием личности реального человека без согласия.</p><label><input id="age-checkbox" type="checkbox" /> Мне исполнилось 18 лет, и я принимаю правила безопасного использования.</label><button id="age-confirm" class="launch" disabled>ПОДТВЕРДИТЬ И ВОЙТИ</button><small>После авторизации согласие синхронизируется с Core API.</small></div></div>`;
}

function notify(title, message = "", type = "info") {
  state.toast = { title, message, type };
  render();
  setTimeout(() => { state.toast = null; render(); }, 3200);
}

async function bootstrap() {
  tg?.ready?.();
  tg?.expand?.();
  if (!tg?.initData) return;
  try {
    await api.authenticateTelegram({ botUsername: document.documentElement.dataset.botUsername || "adultgen_bot", initData: tg.initData, startPayload: tg.initDataUnsafe?.start_param || null });
    state.demo = false;
    const response = await api.feed();
    if (response?.items?.length) state.feed = response.items.map((item) => ({ ...item, author: `@${String(item.user_id).slice(0, 8)}`, media: item.blur_required ? item.blur_preview_url || item.preview_url : item.preview_url, aspect: "portrait", model: "Core API", status: String(item.status).toUpperCase(), likes: 0, views: 0, tags: item.prompt_public ? ["prompt-open"] : ["publication"], trending: false, following: false }));
  } catch (error) {
    console.warn("Core API unavailable; demo mode stays active.", error);
  }
}

function render() {
  const { name, params } = state.route;
  root.innerHTML = name === "feed" ? feedPage() : name === "create" ? createPage() : name === "publication" ? publicationPage(params.id) : name === "profile" ? profilePage() : name === "projects" ? placeholder("ПРОЕКТЫ ПОДКЛЮЧАЮТСЯ", "Следующий срез добавит сцены, референсы и историю генераций.", '<button class="primary" data-route="/create">СОЗДАТЬ СЦЕНУ</button>') : name === "billing" ? billingPage() : placeholder("МАРШРУТ НЕ НАЙДЕН", "Вернись в ленту.", '<button class="primary" data-route="/feed">В ЛЕНТУ</button>');
}

function updateCreate(key, value) { state.create[key] = value; render(); }

document.addEventListener("click", async (event) => {
  const route = event.target.closest("[data-route]");
  if (route) return go(route.dataset.route);
  const tab = event.target.closest("[data-tab]");
  if (tab) { state.tab = tab.dataset.tab; return render(); }
  const mode = event.target.closest("[data-mode]");
  if (mode) return updateCreate("mode", mode.dataset.mode);
  const ratio = event.target.closest("[data-ratio]");
  if (ratio) return updateCreate("aspectRatio", ratio.dataset.ratio);
  if (event.target.closest("[data-remove-reference]")) { state.create.referenceDataUrl = ""; state.create.referenceName = ""; return render(); }
  const preset = event.target.closest("[data-preset]");
  if (preset) {
    const values = { cinematic: "Кинематографичная сцена, глубокая перспектива, реалистичная оптика, объёмный свет", portrait: "Выразительный портрет взрослого персонажа, естественная анатомия, editorial-свет", motion: "Плавный dolly-in, стабильная идентичность персонажа, естественная инерция движения" };
    return updateCreate("prompt", values[preset.dataset.preset]);
  }
  if (event.target.closest("[data-focus-search]")) document.querySelector("#feed-search")?.focus();
  if (event.target.id === "age-confirm") { localStorage.setItem("adultgen.age-confirmed", "1"); state.ageConfirmed = true; render(); if (api.token) api.acceptAdultConsent().catch(console.warn); }
});

document.addEventListener("input", (event) => {
  if (event.target.id === "feed-search") { state.query = event.target.value; const cursor = event.target.selectionStart; render(); const input = document.querySelector("#feed-search"); input?.focus(); input?.setSelectionRange(cursor, cursor); }
  if (event.target.id === "generation-prompt") state.create.prompt = event.target.value;
  if (event.target.id === "duration-range") updateCreate("duration", Number(event.target.value));
  if (event.target.id === "age-checkbox") document.querySelector("#age-confirm").disabled = !event.target.checked;
  if (event.target.matches("[data-toggle]")) state.create[event.target.dataset.toggle] = event.target.checked;
});

document.addEventListener("change", (event) => {
  if (event.target.id !== "reference-file") return;
  const file = event.target.files?.[0];
  if (!file) return;
  if (file.size > 25 * 1024 * 1024) return notify("Файл слишком большой", "Максимальный размер — 25 MB.", "error");
  const reader = new FileReader();
  reader.onload = () => { state.create.referenceDataUrl = String(reader.result || ""); state.create.referenceName = file.name; render(); };
  reader.readAsDataURL(file);
});

document.addEventListener("submit", async (event) => {
  if (event.target.id !== "generation-form") return;
  event.preventDefault();
  if (!state.create.prompt.trim()) return notify("Нужен промпт", "Опиши будущий результат.", "error");
  const payload = buildGenerationPayload(state.create);
  if (!api.token) return notify("DEMO: задача поставлена", `${payload.model_code} · резерв ${estimateCredits(state.create)} CR`, "success");
  try { const task = await api.createGeneration(payload); notify("Генерация запущена", `Task ${String(task.id).slice(0, 8)} · ${task.status}`, "success"); }
  catch (error) { notify("Не удалось запустить", error.message || "Core API вернул ошибку.", "error"); }
});

addEventListener("popstate", () => { state.route = parseRoute(location.pathname); render(); });
render();
bootstrap().finally(render);
