export function getCoreApiBaseUrl(): string {
  const value = import.meta.env.VITE_CORE_API_BASE_URL;
  if (typeof value === 'string' && value.trim()) {
    return value.trim().replace(/\/$/, '');
  }
  return 'http://localhost:8000';
}

export function getBotUsername(): string {
  const value = import.meta.env.VITE_TELEGRAM_BOT_USERNAME;
  if (typeof value === 'string' && value.trim()) {
    return value.trim().replace(/^@/, '').toLowerCase();
  }
  return 'adultgen_bot';
}
