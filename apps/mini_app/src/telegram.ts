type TelegramWebApp = {
  initData?: string;
  initDataUnsafe?: {
    start_param?: string;
  };
  ready?: () => void;
  expand?: () => void;
};

type TelegramWindow = Window & {
  Telegram?: {
    WebApp?: TelegramWebApp;
  };
};

export type TelegramLaunchData = {
  initData: string;
  startParam: string | null;
  isTelegramEnvironment: boolean;
};

export function getTelegramLaunchData(): TelegramLaunchData {
  const webApp = (window as TelegramWindow).Telegram?.WebApp;
  const initData = webApp?.initData ?? '';

  return {
    initData,
    startParam: webApp?.initDataUnsafe?.start_param ?? null,
    isTelegramEnvironment: Boolean(initData),
  };
}

export function prepareTelegramViewport(): void {
  const webApp = (window as TelegramWindow).Telegram?.WebApp;
  webApp?.ready?.();
  webApp?.expand?.();
}
