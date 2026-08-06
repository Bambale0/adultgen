import { useState } from 'react';

type PublicGeneratorLandingProps = {
  blockedRouteTitle?: string | null;
  isStarting?: boolean;
  onStart: (prompt: string) => void | Promise<void>;
  onOpenStudio: () => void;
};

const quickModes = [
  'Text to image',
  'Image to video',
  'Reference style',
  'Cinematic scene',
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

  return (
    <main className="web-shell public-generator-shell">
      <aside className="sidebar public-landing-sidebar">
        <div>
          <p className="eyebrow">AdultGen</p>
          <h1>AI Studio</h1>
          <p className="sidebar-copy">
            Prompt-first генератор для взрослых AI media: изображение, видео, референсы, проекты и публикация в профиль.
          </p>
        </div>
        <nav className="route-nav" aria-label="Публичные преимущества">
          <span className="guard-pill enabled">18+ policy gate</span>
          <span className="guard-pill">Prompt → media → publish</span>
          <span className="guard-pill">Kie capability layer</span>
          <span className="guard-pill">Wallet credits</span>
        </nav>
        <div className="session-panel">
          <p className="eyebrow">No login wall</p>
          <p className="muted-text">
            Сначала показываем продукт и генератор. Вход и 18+ подтверждение включаются при старте создания.
          </p>
        </div>
      </aside>

      <section className="main-panel public-generator-panel">
        <header className="topbar public-generator-topbar">
          <div>
            <p className="eyebrow">AI adult generator</p>
            <h2>Создай AI-контент за один prompt</h2>
            <p className="muted-text">
              Стартовый экран теперь вокруг генерации, а не вокруг формы входа.
            </p>
          </div>
          <div className="topbar-actions">
            <span className="guard-pill enabled">Private by default</span>
            <button className="ghost-button" type="button" onClick={onOpenStudio}>
              Открыть Studio
            </button>
          </div>
        </header>

        {blockedRouteTitle && (
          <section className="card stack-card soft-auth-notice" aria-live="polite">
            <p className="eyebrow">Protected area</p>
            <p>
              Раздел “{blockedRouteTitle}” откроется после старта сессии и подтверждения 18+. Сначала можно описать сцену.
            </p>
          </section>
        )}

        <section className="card stack-card public-prompt-card">
          <div className="section-heading-row">
            <div>
              <p className="eyebrow">Prompt</p>
              <h3>Что создаём?</h3>
            </div>
            <span className="task-status submitted">{selectedMode}</span>
          </div>

          <label>
            Описание сцены
            <textarea
              rows={5}
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Опиши сцену, стиль, ракурс, свет, настроение…"
            />
          </label>

          <div className="button-row" aria-label="Быстрые режимы генерации">
            {quickModes.map((mode) => (
              <button
                key={mode}
                type="button"
                className={mode === selectedMode ? 'primary-button small-button' : 'ghost-button small-button'}
                onClick={() => setSelectedMode(mode)}
              >
                {mode}
              </button>
            ))}
          </div>

          <div className="button-row">
            <button className="primary-button" type="button" disabled={isStarting} onClick={() => void onStart(prompt)}>
              {isStarting ? 'Запускаем…' : 'Создать'}
            </button>
            <button className="ghost-button" type="button" onClick={onOpenStudio}>
              Настройки Studio
            </button>
          </div>
        </section>

        <section className="landing-grid public-proof-grid">
          <article className="card metric-card">
            <p className="eyebrow">Flow</p>
            <strong>Generate</strong>
            <p>Prompt, negative prompt, refs, first/last frame и video modes.</p>
          </article>
          <article className="card metric-card">
            <p className="eyebrow">Safety</p>
            <strong>18+</strong>
            <p>Age gate, policy checks, blur, reports и moderation queue.</p>
          </article>
          <article className="card metric-card">
            <p className="eyebrow">Billing</p>
            <strong>Credits</strong>
            <p>Wallet ledger, packages, subscriptions и provider checkout boundary.</p>
          </article>
        </section>
      </section>
    </main>
  );
}
