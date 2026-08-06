import { useState } from 'react';

import './PublicGeneratorLanding.css';

type PublicGeneratorLandingProps = {
  blockedRouteTitle?: string | null;
  isStarting?: boolean;
  onStart: (prompt: string) => void | Promise<void>;
  onOpenStudio: () => void;
};

type FeedItem = {
  title: string;
  prompt: string;
  creator: string;
  tone: string;
  mode: string;
  stats: string;
  seed: string;
  telemetry: {
    sync: string;
    latency: string;
    status: string;
  };
};

const contentTabs = ['Для вас', 'Изображения', 'Видео', 'GIF'];
const quickModes = ['Text to image', 'Image to video', 'Reference style', 'Cinematic scene'];
const privacyModes = ['Private by default', 'Blur previews', '18+ gate'];

const feedItems: FeedItem[] = [
  {
    title: 'Neon portrait',
    prompt: 'cinematic neon portrait, soft shadows, premium lighting',
    creator: '@adultgen.studio',
    tone: 'violet',
    mode: 'Text to image',
    stats: '18.4K',
    seed: 'AG-NEON-01',
    telemetry: { sync: '98.4%', latency: '12ms', status: 'READY' },
  },
  {
    title: 'Editorial studio',
    prompt: 'premium editorial studio lighting, controlled composition',
    creator: '@creator.lab',
    tone: 'rose',
    mode: 'Reference style',
    stats: '12.8K',
    seed: 'AG-EDIT-22',
    telemetry: { sync: '94.1%', latency: '18ms', status: 'READY' },
  },
  {
    title: 'Anime night',
    prompt: 'anime scene, blue moonlight, detailed frame, cinematic camera',
    creator: '@animeflow',
    tone: 'blue',
    mode: 'Image to video',
    stats: '9.6K',
    seed: 'AG-ANIME-09',
    telemetry: { sync: '91.7%', latency: '23ms', status: 'VIDEO' },
  },
  {
    title: 'Private concept',
    prompt: 'private character concept, controlled pose, soft cinematic light',
    creator: '@private.render',
    tone: 'amber',
    mode: 'Cinematic scene',
    stats: '7.1K',
    seed: 'AG-PRIV-14',
    telemetry: { sync: '89.3%', latency: '19ms', status: 'PRIVATE' },
  },
  {
    title: 'Creator feed',
    prompt: 'published previews with save, report, remix and privacy controls',
    creator: '@feed.ops',
    tone: 'magenta',
    mode: 'Gallery preview',
    stats: '6.3K',
    seed: 'AG-FEED-31',
    telemetry: { sync: '96.0%', latency: '15ms', status: 'PUBLIC' },
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
  const [selectedItem, setSelectedItem] = useState<FeedItem>(feedItems[0]);
  const [savedTitles, setSavedTitles] = useState<Set<string>>(() => new Set());
  const [reportedTitles, setReportedTitles] = useState<Set<string>>(() => new Set());
  const [feedback, setFeedback] = useState('Лента готова. Выбери стиль, открой превью или начни генерацию.');

  const createFromItem = (item: FeedItem) => {
    setSelectedItem(item);
    setPrompt(item.prompt);
    setSelectedMode(quickModes.includes(item.mode) ? item.mode : quickModes[0]);
    setFeedback(`Prompt из “${item.title}” перенесён в создание.`);
  };

  const openItem = (item: FeedItem) => {
    setSelectedItem(item);
    setFeedback(`Открыты детали “${item.title}”.`);
  };

  const toggleSave = (item: FeedItem) => {
    setSavedTitles((current) => {
      const next = new Set(current);
      if (next.has(item.title)) {
        next.delete(item.title);
        setFeedback(`“${item.title}” удалён из сохранённых.`);
      } else {
        next.add(item.title);
        setFeedback(`“${item.title}” сохранён в коллекцию.`);
      }
      return next;
    });
  };

  const toggleReport = (item: FeedItem) => {
    setReportedTitles((current) => {
      const next = new Set(current);
      if (next.has(item.title)) {
        next.delete(item.title);
        setFeedback(`Жалоба по “${item.title}” отменена.`);
      } else {
        next.add(item.title);
        setFeedback(`Жалоба по “${item.title}” добавлена в очередь модерации.`);
      }
      return next;
    });
  };

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

      <p className="public-feedback" aria-live="polite">
        {feedback}
      </p>

      <section className="public-reels-stage" aria-label="Главная лента AdultGen">
        <section className="public-reels-scroll" aria-label="TikTok-style лента AI-превью">
          {feedItems.map((item, index) => {
            const isSaved = savedTitles.has(item.title);
            const isReported = reportedTitles.has(item.title);

            return (
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
                  <button type="button" aria-label={`Создать в стиле ${item.title}`} onClick={() => createFromItem(item)}>
                    ✦
                    <small>Создать</small>
                  </button>
                  <button
                    type="button"
                    className={isSaved ? 'active' : undefined}
                    aria-label={`${isSaved ? 'Убрать из сохранённых' : 'Сохранить'} ${item.title}`}
                    onClick={() => toggleSave(item)}
                  >
                    {isSaved ? '♥' : '♡'}
                    <small>{item.stats}</small>
                  </button>
                  <button type="button" aria-label={`Открыть ${item.title}`} onClick={() => openItem(item)}>
                    ↗
                    <small>Открыть</small>
                  </button>
                  <button
                    type="button"
                    className={isReported ? 'active danger' : undefined}
                    aria-label={`${isReported ? 'Отменить жалобу на' : 'Пожаловаться на'} ${item.title}`}
                    onClick={() => toggleReport(item)}
                  >
                    ⚑
                    <small>{isReported ? 'Sent' : 'Report'}</small>
                  </button>
                </aside>
              </article>
            );
          })}
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

          <section className="public-detail-panel" aria-label="Детали AI-превью">
            <div className="public-detail-head">
              <div>
                <p className="eyebrow">Preview details</p>
                <h3>{selectedItem.title}</h3>
              </div>
              <span>{selectedItem.telemetry.status}</span>
            </div>

            <dl className="public-telemetry-grid">
              <div>
                <dt>Sync</dt>
                <dd>{selectedItem.telemetry.sync}</dd>
              </div>
              <div>
                <dt>Latency</dt>
                <dd>{selectedItem.telemetry.latency}</dd>
              </div>
              <div>
                <dt>Seed</dt>
                <dd>{selectedItem.seed}</dd>
              </div>
            </dl>

            <p>{selectedItem.prompt}</p>
            <button type="button" onClick={() => createFromItem(selectedItem)}>
              Использовать этот стиль
            </button>
          </section>

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
