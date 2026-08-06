import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { PublicGeneratorLanding } from './PublicGeneratorLanding';

afterEach(() => {
  cleanup();
});

describe('PublicGeneratorLanding', () => {
  it('renders a TikTok-style reels feed instead of an auth wall', () => {
    render(<PublicGeneratorLanding onStart={vi.fn()} onOpenStudio={vi.fn()} />);

    expect(screen.getByRole('button', { name: 'AdultGen home' })).toBeTruthy();
    expect(screen.getByPlaceholderText('Поиск AI-контента')).toBeTruthy();
    expect(screen.getByLabelText('Главная лента AdultGen')).toBeTruthy();
    expect(screen.getByLabelText('TikTok-style лента AI-превью')).toBeTruthy();
    expect(screen.getByLabelText('Быстрое создание AI-контента')).toBeTruthy();
    expect(screen.getByLabelText('Детали AI-превью')).toBeTruthy();
    expect(screen.getByText('AG-NEON-01')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Создать AI-контент' })).toBeTruthy();
    expect(screen.queryByText('AI Photo')).toBeNull();
    expect(screen.queryByText('AdultGen AI')).toBeNull();
    expect(screen.queryByText('Вход в сайт-приложение')).toBeNull();
  });

  it('shows a soft protected-route notice without replacing the landing with login', () => {
    render(<PublicGeneratorLanding blockedRouteTitle="Лента" onStart={vi.fn()} onOpenStudio={vi.fn()} />);

    expect(screen.getByText(/Раздел “Лента” откроется/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Создать AI-контент' })).toBeTruthy();
    expect(screen.queryByText('Войти и получить Core token')).toBeNull();
  });

  it('copies a feed item prompt into the compose dock', () => {
    render(<PublicGeneratorLanding onStart={vi.fn()} onOpenStudio={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Создать в стиле Anime night' }));

    const textarea = screen.getByLabelText('Описание сцены') as HTMLTextAreaElement;
    expect(textarea.value).toContain('anime scene, blue moonlight');
    expect(screen.getByText('Prompt из “Anime night” перенесён в создание.')).toBeTruthy();
  });

  it('opens a reel detail panel from the action rail', () => {
    render(<PublicGeneratorLanding onStart={vi.fn()} onOpenStudio={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Открыть Private concept' }));

    const detailPanel = screen.getByLabelText('Детали AI-превью');
    expect(within(detailPanel).getByRole('heading', { name: 'Private concept' })).toBeTruthy();
    expect(within(detailPanel).getByText('AG-PRIV-14')).toBeTruthy();
    expect(screen.getByText('Открыты детали “Private concept”.')).toBeTruthy();
  });

  it('toggles save and report states without leaving the landing', () => {
    render(<PublicGeneratorLanding onStart={vi.fn()} onOpenStudio={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Сохранить Editorial studio' }));
    expect(screen.getByText('“Editorial studio” сохранён в коллекцию.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Убрать из сохранённых Editorial studio' })).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Пожаловаться на Editorial studio' }));
    expect(screen.getByText('Жалоба по “Editorial studio” добавлена в очередь модерации.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Отменить жалобу на Editorial studio' })).toBeTruthy();
  });

  it('calls start action from the primary CTA', () => {
    const onStart = vi.fn();
    render(<PublicGeneratorLanding onStart={onStart} onOpenStudio={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Создать AI-контент' }));

    expect(onStart).toHaveBeenCalledWith(expect.stringContaining('Cinematic AI scene'));
  });
});
