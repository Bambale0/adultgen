import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { PublicGeneratorLanding } from './PublicGeneratorLanding';

afterEach(() => {
  cleanup();
});

describe('PublicGeneratorLanding', () => {
  it('renders a clean gallery-first public home instead of an auth wall', () => {
    render(<PublicGeneratorLanding onStart={vi.fn()} onOpenStudio={vi.fn()} />);

    expect(screen.getByRole('button', { name: 'AdultGen home' })).toBeTruthy();
    expect(screen.getByPlaceholderText('Поиск AI-контента')).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Тренды и генерация AI-контента' })).toBeTruthy();
    expect(screen.getByLabelText('Главный экран AdultGen')).toBeTruthy();
    expect(screen.getByLabelText('Примеры AI-превью')).toBeTruthy();
    expect(screen.getByLabelText('Быстрое создание AI-контента')).toBeTruthy();
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

  it('calls start action from the primary CTA', () => {
    const onStart = vi.fn();
    render(<PublicGeneratorLanding onStart={onStart} onOpenStudio={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Создать AI-контент' }));

    expect(onStart).toHaveBeenCalledWith(expect.stringContaining('Cinematic AI scene'));
  });
});
