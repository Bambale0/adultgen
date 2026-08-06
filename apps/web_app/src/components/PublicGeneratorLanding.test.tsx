import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { PublicGeneratorLanding } from './PublicGeneratorLanding';

afterEach(() => {
  cleanup();
});

describe('PublicGeneratorLanding', () => {
  it('renders a prompt-first public generator instead of an auth wall', () => {
    render(<PublicGeneratorLanding onStart={vi.fn()} onOpenStudio={vi.fn()} />);

    expect(screen.getByRole('heading', { name: 'Создай AI-контент за один prompt' })).toBeTruthy();
    expect(screen.getByLabelText('Описание сцены')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Создать' })).toBeTruthy();
    expect(screen.queryByText('Вход в сайт-приложение')).toBeNull();
  });

  it('shows a soft protected-route notice without replacing the landing with login', () => {
    render(<PublicGeneratorLanding blockedRouteTitle="Лента" onStart={vi.fn()} onOpenStudio={vi.fn()} />);

    expect(screen.getByText(/Раздел “Лента” откроется/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Создать' })).toBeTruthy();
    expect(screen.queryByText('Войти и получить Core token')).toBeNull();
  });

  it('calls start action from the primary CTA', () => {
    const onStart = vi.fn();
    render(<PublicGeneratorLanding onStart={onStart} onOpenStudio={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Создать' }));

    expect(onStart).toHaveBeenCalledWith(expect.stringContaining('Cinematic AI scene'));
  });
});
