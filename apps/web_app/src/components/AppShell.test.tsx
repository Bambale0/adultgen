import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AppShell, Sidebar, TopBar } from './AppShell';
import { webAppRoutes } from '../routes';

describe('AppShell', () => {
  it('renders shell regions and children', () => {
    render(<AppShell sidebar={<div>Side</div>} topbar={<div>Top</div>}><div>Content</div></AppShell>);
    expect(screen.getByText('Side')).toBeTruthy();
    expect(screen.getByText('Top')).toBeTruthy();
    expect(screen.getByText('Content')).toBeTruthy();
  });

  it('renders sidebar routes from route metadata', () => {
    render(<Sidebar routes={webAppRoutes} activeRoute={webAppRoutes[0]} routeResolver={(id) => webAppRoutes.find((r) => r.id === id)!} onNavigate={vi.fn()} onCreate={vi.fn()} />);
    expect(screen.getByLabelText('Основная навигация сайта')).toBeTruthy();
  });

  it('renders topbar status and route selector', () => {
    render(<TopBar activeRoute={webAppRoutes[0]} routes={webAppRoutes} session={null} balance={null} onNavigate={vi.fn()} onSignIn={vi.fn()} onSignOut={vi.fn()} />);
    expect(screen.getByLabelText('Route selector')).toBeTruthy();
  });
});
