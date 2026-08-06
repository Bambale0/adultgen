import { useState } from 'react';

import './PublicGeneratorLanding.css';

type PublicGeneratorLandingProps = {
  blockedRouteTitle?: string | null;
  isStarting?: boolean;
  onStart: (prompt: string) => void | Promise<void>;
  onOpenStudio: () => void;
};

const contentTabs = ['Для вас', 'Изображения', 'Видео', 'GIF'];
const quickModes = ['Text to image', 'Image to video', 'Reference style', 'Cinematic scene'];
const privacyModes = ['Private by default', 'Blur previews', '18+ gate'];

const feedItems = [
  {
    title: 'Neon portrait',
    prompt: 'cinematic neon portrait, soft shadows, premium lighting',
    creator: '@adultgen.studio',
    tone: 'violet',
    mode: 'Text to image',
    stats: '18.4K',
  },
  {
    title: 'Editorial studio',
    prompt: 'premium editorial studio lighting, controlled composition',
    creator: '@creator.lab',
    tone: 'rose',
    mode: 'Reference style',
    stats: '12.8K',
  },
  {
    title: 'Anime night',
    prompt: 'anime scene, blue moonlight, detailed frame, cinematic camera',
    creator: '@animeflow',
    tone: 'blue',
    mode: 'Image to video',
    stats: '9.6K',
  },
  {
    title: 'Private concept',
    prompt: 'private character concept, controlled pose, soft cinematic light',
    creator: '@private.render',
    tone: 'amber',
    mode: 'Cinematic scene',
    stats: '7.1K',
  },
  {
    title: 'Creator feed',
    prompt: 'published previews with save, report, remix and privacy controls',
    creator: '@feed.ops',
    tone: 'magenta',
    mode: 'Gallery preview',
    stats: '6.3K',
  },
];

const defaultPrompt =
  'Cinematic AI scene, premium realistic lighting, controlled composition, editorial look, high detail';

export function PublicGeneratorLanding({
  blockedRouteTitle,
  isStarting = false,
  onStart,
  onOpenStudio,
}: PublicGeneratorLandingProps) {
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [selectedMode, setSelectedMode] = useState(quickModes[1]);
  const [selectedTab, setSelectedTab] = useState(contentTabs[0]);

  return (
    <main className="public-home public-reels-home">
      <header className="public-reels-header">
        <button className="public-brand" type="button" onClick={onOpenStudio} aria-label="AdultGen home">
          <span className="public-brand-mark">∞</span>
          <strong>AdultGen</strong>
        </button>

        <label className="public-search">
          <span hidden>Поиск AI-контента</span>
          <input placeholder="Поиск AI-контента" />
          <button type="button" aria-label="Искать">
            ⌕
          </button>
        </label>

        <nav className="public-tabs" aria-label="Тип контента">
          {contentTabs.map((tab) => (
            <button
              key={tab}
              type="button"
              className={tab === selectedTab ? 'public-tab active' : 'public-tab'}
              onClick={() => setSelectedTab(tab)}
            >
              {tab}
            </button>
          ))}
        </nav>

        <div className="public-header-actions">
          <button className="public-link-button" type="button" onClick={onOpenStudio}>
            Создать
          </button>
          <button className="public-login-button" type="button" onClick={onOpenStudio}>
            Войти
          </button>
        </div>
      </header>

      {blockedRouteTitle && (
        <section className="public-notice" aria-live="polite">
          Раздел “{blockedRouteTitle}” откроется после старта сессии и подтверждения 18+. Пока можно смотреть ленту и описать сцену.
        </section>
      )}

      <section className="public-reels-stage" aria-label="Главная лента AdultGen">
        <section className="public-reels-scroll" aria-label="TikTok-style лента AI-превью">
          {feedItems.map((item, index) => (
            <article key={item.title} className={`public-reel-card ${item.tone}`}>
              <div className="public-reel-media" aria-hidden="true">
                <span className="public-reel-index">{String(index + 1).padStart(2, '0')}</span>
                <span className="public-reel-play">▶</span>
              </div>

              <div className="public-reel-overlay">
                <div className="public-reel-badges">
                  <span>{item.mode}</span>
                  <span>Private preview</span>
                </div>
                <h1>{item.title}</h1>
                <p>{item.prompt}</p>
                <strong>{item.creator}</strong>
              </div>

              <aside className="public-action-rail" aria-label={`Действия для ${item.title}`}>
                <button type="button" aria-label={`Создать в стиле ${item.title}`} onClick={() => setPrompt(item.prompt)}>
                  ✦
                  <small>Создать</small>
                </button>
                <button type="button" aria-label={`Сохранить ${item.title}`}>
                  ♡
                  <small>{item.stats}</small>
                </button>
                <button type="button" aria-label={`Открыть ${item.title}`}>
                  ↗
                  <small>Открыть</small>
                </button>
                <button type="button" aria-label={`Пожаловаться на ${item.title}`}>
                  ⚑
                  <small>Report</small>
                </button>
              </aside>
            </article>
          ))}
        </section>

        <aside className="public-compose-dock" aria-label="Быстрое создание AI-контента">
          <div className="public-compose-head">
            <div>
              <p className="eyebrow">Prompt</p>
              <h2>Создать из ленты</h2>
            </div>
            <span>{selectedMode}</span>
          </div>

          <textarea
            aria-label="Описание сцены"
            rows={4}
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Опиши сцену, стиль, ракурс, свет, настроение…"
          />

          <div className="public-mode-row" aria-label="Быстрые режимы генерации">
            {quickModes.map((mode) => (
              <button
                key={mode}
                type="button"
                className={mode === selectedMode ? 'public-chip active' : 'public-chip'}
                onClick={() => setSelectedMode(mode)}
              >
                {mode}
              </button>
            ))}
          </div>

          <div className="public-privacy-row" aria-label="Безопасность и приватность">
            {privacyModes.map((mode) => (
              <span key={mode}>{mode}</span>
            ))}
          </div>

          <div className="public-generator-actions">
            <button className="public-create-button" type="button" disabled={isStarting} onClick={() => void onStart(prompt)}>
              {isStarting ? 'Запускаем…' : 'Создать AI-контент'}
            </button>
            <button className="public-outline-button" type="button" onClick={onOpenStudio}>
              Studio
            </button>
          </div>

          <p className="public-create-note">
            Главная — лента превью. Создание откроет сессию и 18+ policy gate только после действия пользователя.
          </p>
        </aside>
      </section>
    </main>
  );
}
