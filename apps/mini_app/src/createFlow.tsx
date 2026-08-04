import { useState } from 'react';

import { createAvatarProfile, createProject, createScene, type Scene } from './workspace';

export function CreateFlowStarter({ accessToken }: { accessToken: string }) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle');
  const [createdScene, setCreatedScene] = useState<Scene | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCreateDraft() {
    setStatus('loading');
    setError(null);
    try {
      await createAvatarProfile(accessToken, 'Новый аватар');
      const project = await createProject(accessToken, {
        title: 'Новый проект',
        description: 'Черновик проекта из Mini App',
        output_format: '9:16',
      });
      const scene = await createScene(accessToken, project.id, {
        title: 'Сцена 1',
        prompt: 'Опишите действие, движение камеры, атмосферу и звук.',
        duration_seconds: 5,
        aspect_ratio: '9:16',
      });
      setCreatedScene(scene);
      setStatus('done');
    } catch (caughtError) {
      setStatus('error');
      setError(caughtError instanceof Error ? caughtError.message : 'Create flow failed.');
    }
  }

  return (
    <section className="page-card create-flow-card">
      <p className="eyebrow">Generation flow</p>
      <h1>Создать</h1>
      <p>
        Быстрый старт создаёт приватный аватар, проект и первую сцену. Следующий шаг —
        привязка референсов и запуск генерации.
      </p>
      <button
        className="primary-button"
        type="button"
        disabled={status === 'loading'}
        onClick={() => void handleCreateDraft()}
      >
        {status === 'loading' ? 'Создаём...' : 'Создать черновик'}
      </button>
      {status === 'done' && createdScene && (
        <p className="success-text">Сцена #{createdScene.order_index} создана.</p>
      )}
      {status === 'error' && error && <p className="error-text">{error}</p>}
    </section>
  );
}
