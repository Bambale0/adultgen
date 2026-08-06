import { useState } from 'react';

import './PublicGeneratorLanding.css';

type PublicGeneratorLandingProps = {
  blockedRouteTitle?: string | null;
  isStarting?: boolean;
  onStart: (prompt: string) => void | Promise<void>;
  onOpenStudio: () => void;
};

const contentTabs = ['Изображения', 'Видео', 'GIF'];
const quickModes = ['Text to image', 'Image to video', 'Reference style', 'Cinematic scene'];
const privacyModes = ['Private by default', 'Blur previews', '18+ gate'];

const previewTiles = [
  { title: 'Neon portrait', prompt: 'cinematic neon portrait, soft shadows', tone: 'violet', size: 'wide' },
  { title: 'Editorial studio', prompt: 'premium editorial studio lighting', tone: 'rose', size: 'tall' },
  { title: 'Anime night', prompt: 'anime scene, blue moonlight, detailed frame', tone: 'blue', size: 'tall' },
  { title: 'Private concept', prompt: 'private character concept, controlled pose', tone: 'amber', size: 'wide' },
  { title: 'Reference style', prompt: 'style transfer from reference image', tone: 'green', size: 'standard' },
  { title: 'Video frame', prompt: 'first frame to short cinematic video', tone: 'cyan', size: 'standard' },
  { title: 'Studio setup', prompt: 'saved characters, prompt presets, draft scenes', tone: 'slate', size: 'standard' },
  { title: 'Creator feed', prompt: 'published previews with report and save actions', tone: 'magenta', size: 'wide' },
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
    <main className="public-home">
      <header className="public-header">
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

        <button className="public-outline-button" type="button">
          Категории
        </button>

        <div className="public-header-actions">
          <button className="public-link-button" type="button" onClick={onOpenStudio}>
            Создать
          </button>
          <button className="public-link-button public-accent-text" type="button">
            Обновление
          </button>
          <button className="public-login-button" type="button" onClick={onOpenStudio}>
            Войти
          </button>
        </div>
      </header>

      <section className="public-tabs" aria-label="Тип контента">
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
      </section>

      {blockedRouteTitle && (
        <section className="public-notice" aria-live="polite">
          Раздел “{blockedRouteTitle}” откроется после старта сессии и подтверждения 18+. Пока можно выбрать стиль и описать сцену.
        </section>
      )}

      <section className="public-fold" aria-label="Главный экран AdultGen">
        <div className="public-gallery-column">
          <div className="public-feed-toolbar">
            <div>
              <p className="eyebrow">AI adult media generator</p>
              <h1>Тренды и генерация AI-контента</h1>
              <p className="public-subtitle">
                Сначала витрина и превью. Создание, вход и 18+ включаются только по действию пользователя.
              </p>
            </div>
            <div className="public-hero-actions">
              <button className="public-filter-button" type="button">
                Фильтры
              </button>
              <button className="public-compact-action" type="button">
                Слайды
              </button>
              <button className="public-compact-action" type="button">
                Развернуть
              </button>
            </div>
          </div>

          <section className="public-gallery" aria-label="Примеры AI-превью">
            {previewTiles.map((tile, index) => (
              <article key={tile.title} className={`public-tile ${tile.tone} ${tile.size}`}>
                <div className="public-tile-art" aria-hidden="true">
                  <span>{String(index + 1).padStart(2, '0')}</span>
                </div>
                <footer>
                  <strong>{tile.title}</strong>
                  <small>{tile.prompt}</small>
                  <button type="button" aria-label={`Открыть ${tile.title}`}>
                    ◉
                  </button>
                </footer>
              </article>
            ))}
          </section>
        </div>

        <aside className="public-create-panel" aria-label="Быстрое создание AI-контента">
          <div className="public-create-head">
            <div>
              <p className="eyebrow">Prompt</p>
              <h2>Что создаём?</h2>
            </div>
            <span>{selectedMode}</span>
          </div>

          <textarea
            aria-label="Описание сцены"
            rows={5}
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
              Настройки Studio
            </button>
          </div>

          <p className="public-create-note">
            Генерация откроет сессию, затем покажет 18+ policy gate. До этого главная остаётся публичной витриной.
          </p>
        </aside>
      </section>
    </main>
  );
}
