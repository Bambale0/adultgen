import { ShieldCheck, Sparkles, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import {
  acceptAdultConsent,
  authenticateGoogle,
  authenticateTelegramLogin,
  authenticateTelegramMiniApp,
  type TelegramLoginPayload,
  type WebSession,
} from './api';
import { saveAdultConsentStatus, saveWebSession } from './session';

declare global {
  interface Window {
    google?: { accounts: { id: { initialize(config: object): void; renderButton(target: HTMLElement, config: object): void } } };
    Telegram?: { WebApp?: { initData?: string; ready?(): void; expand?(): void } };
    onAdultGenTelegramAuth?: (user: TelegramLoginPayload) => void;
  }
}

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
const telegramBotUsername = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || '';

export function useTelegramMiniAppBootstrap(onAuthenticated: (session: WebSession) => void) {
  useEffect(() => {
    const initData = window.Telegram?.WebApp?.initData;
    if (!initData || !telegramBotUsername) return;
    window.Telegram?.WebApp?.ready?.();
    window.Telegram?.WebApp?.expand?.();
    authenticateTelegramMiniApp(telegramBotUsername, initData)
      .then((session) => { saveWebSession(session); onAuthenticated(session); })
      .catch(() => undefined);
  }, [onAuthenticated]);
}

export function AuthDialog({ onClose, onAuthenticated }: { onClose: () => void; onAuthenticated: (session: WebSession) => void }) {
  const googleButton = useRef<HTMLDivElement>(null);
  const telegramButton = useRef<HTMLDivElement>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!googleClientId) return;
    const renderGoogle = () => {
      if (!window.google || !googleButton.current) return;
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async ({ credential }: { credential: string }) => {
          try {
            const session = await authenticateGoogle(credential);
            saveWebSession(session);
            onAuthenticated(session);
          } catch (reason) { setError(reason instanceof Error ? reason.message : 'Google sign-in failed'); }
        },
      });
      window.google.accounts.id.renderButton(googleButton.current, { theme: 'filled_black', size: 'large', width: 320, shape: 'pill', text: 'continue_with' });
    };
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.onload = renderGoogle;
    document.head.appendChild(script);
    return () => script.remove();
  }, [onAuthenticated]);

  useEffect(() => {
    if (!telegramBotUsername || !telegramButton.current) return;
    window.onAdultGenTelegramAuth = async (payload) => {
      try {
        const session = await authenticateTelegramLogin(payload);
        saveWebSession(session);
        onAuthenticated(session);
      } catch (reason) { setError(reason instanceof Error ? reason.message : 'Telegram sign-in failed'); }
    };
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.async = true;
    script.dataset.telegramLogin = telegramBotUsername.replace(/^@/, '');
    script.dataset.size = 'large';
    script.dataset.radius = '12';
    script.dataset.userpic = 'false';
    script.dataset.onauth = 'onAdultGenTelegramAuth(user)';
    telegramButton.current.appendChild(script);
    return () => { delete window.onAdultGenTelegramAuth; script.remove(); };
  }, [onAuthenticated]);

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="auth-dialog" role="dialog" aria-modal="true" aria-labelledby="auth-title">
        <button className="dialog-close" aria-label="Закрыть" onClick={onClose}><X size={19} /></button>
        <div className="auth-brand"><span><Sparkles /></span><strong>ADULTGEN</strong></div>
        <p className="eyebrow">SECURE ACCESS</p>
        <h2 id="auth-title">Enter the creator studio</h2>
        <p className="muted">One identity across web and Telegram. Provider credentials are verified by the backend.</p>
        <div className="provider-stack">
          {googleClientId ? <div className="provider-slot" ref={googleButton} /> : <div className="provider-unconfigured">Google sign-in needs VITE_GOOGLE_CLIENT_ID</div>}
          <div className="auth-divider"><span>or</span></div>
          {telegramBotUsername ? <div className="provider-slot telegram-slot" ref={telegramButton} /> : <div className="provider-unconfigured">Telegram sign-in needs VITE_TELEGRAM_BOT_USERNAME</div>}
        </div>
        {error && <p className="error-banner" role="alert">{error}</p>}
        <p className="legal-note">By continuing you confirm you are 18+. Content safety acceptance follows after sign-in.</p>
      </section>
    </div>
  );
}

export function AdultGate({ session, onAccepted }: { session: WebSession; onAccepted: () => void }) {
  const [busy, setBusy] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState('');

  const accept = async () => {
    if (!confirmed) return;
    setBusy(true);
    try {
      const status = await acceptAdultConsent(session.access_token);
      saveAdultConsentStatus(status);
      onAccepted();
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Consent update failed'); setBusy(false); }
  };

  return (
    <div className="modal-backdrop adult-backdrop">
      <section className="adult-gate" role="dialog" aria-modal="true" aria-labelledby="adult-title">
        <div className="gate-icon"><ShieldCheck size={28} /></div>
        <p className="eyebrow">ADULT ACCESS PROTOCOL</p>
        <h2 id="adult-title">Adults only. Consent matters.</h2>
        <p>AdultGen blocks minors, coercion, public-figure sexualization and non-consensual real-person imagery. Every request is subject to moderation.</p>
        <label className="consent-check"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} /><span>I am at least 18 years old and accept the content and safety policy.</span></label>
        {error && <p className="error-banner" role="alert">{error}</p>}
        <button className="primary-action full" disabled={!confirmed || busy} onClick={accept}>{busy ? 'Recording consent…' : 'Accept & enter studio'}</button>
      </section>
    </div>
  );
}
