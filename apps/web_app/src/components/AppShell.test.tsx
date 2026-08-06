import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { AppShell, Sidebar, TopBar } from './AppShell';
import { primaryWebAppRoutes, webAppRoutes } from '../routes';

const activeRoute = webAppRoutes.find((route) => route.id === 'studio') ?? webAppRoutes[0];

describe('AppShell', () => {
  it('renders shell regions and children', () => {
    render(
      <AppShell
        activeRoute={activeRoute}
        sidebar={<span>Sidebar slot</span>}
        topbar={<span>Topbar slot</span>}
      >
        <section>Studio content</section>
      </AppShell>,
    );

    expect(screen.getByText('Sidebar slot')).toBeTruthy();
    expect(screen.getByText('Topbar slot')).toBeTruthy();
    expect(screen.getByText('Studio content')).toBeTruthy();
  });

  it('renders sidebar routes from route metadata', () => {
    const onNavigate = vi.fn();

    render(
      <Sidebar
        activeRoute={activeRoute}
        routes={primaryWebAppRoutes}
        onNavigate={onNavigate}
        routeResolver={(routeId) => webAppRoutes.find((route) => route.id === routeId) ?? null}
      />,
    );

    expect(screen.getByLabelText('Основная навигация сайта')).toBeTruthy();
    expect(screen.getByText('Студия')).toBeTruthy();
    expect(screen.getByText('Баланс')).toBeTruthy();
  });

  it('renders topbar status and route selector', () => {
    render(
      <TopBar
        activeRoute={activeRoute}
        routes={webAppRoutes}
        statusMessage="Готово."
        errorMessage={null}
        onNavigate={vi.fn()}
      />,
    );

    expect(screen.getByText('Студия')).toBeTruthy();
    expect(screen.getByText('/studio')).toBeTruthy();
    expect(screen.getByText('Готово.')).toBeTruthy();
    expect(screen.getByLabelText('Route selector')).toBeTruthy();
  });
});
