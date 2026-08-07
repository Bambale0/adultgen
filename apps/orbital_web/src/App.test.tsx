import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { App } from './App';

describe('Orbital Web shell', () => {
  it('renders safe feed before an operator session exists', () => {
    render(<App />);

    expect(screen.getAllByText('ORBITAL FEED').length).toBeGreaterThan(0);
    expect(screen.getByText('18+ LOCKED')).toBeInTheDocument();
    expect(screen.getByText('NEON CONTACT')).toBeInTheDocument();
    expect(screen.getByText('○ SAFE MODE')).toBeInTheDocument();
  });

  it('opens identity handshake instead of bypassing a protected route', () => {
    render(<App />);

    fireEvent.click(screen.getAllByRole('button', { name: /deploy/i })[0]);

    expect(screen.getByText('INITIALIZE OPERATOR')).toBeInTheDocument();
    expect(screen.getByLabelText('EMAIL CHANNEL')).toBeInTheDocument();
  });

  it('renders route sectors from the product navigation', () => {
    render(<App />);

    expect(screen.getByRole('button', { name: /telemetry/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /operator/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /credits/i })).toBeInTheDocument();
  });
});
