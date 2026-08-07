import { apiPath } from "./core.js";

const TOKEN_KEY = "adultgen.access-token";

export class ApiError extends Error {
  constructor(message, status = 0, payload = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export class ApiClient {
  constructor({ fetchImpl = globalThis.fetch, storage = globalThis.localStorage } = {}) {
    this.fetchImpl = fetchImpl;
    this.storage = storage;
  }

  get token() {
    return this.storage?.getItem?.(TOKEN_KEY) || "";
  }

  set token(value) {
    if (!this.storage) return;
    if (value) this.storage.setItem(TOKEN_KEY, value);
    else this.storage.removeItem(TOKEN_KEY);
  }

  async request(path, options = {}) {
    const headers = new Headers(options.headers || {});
    if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    if (this.token) headers.set("Authorization", `Bearer ${this.token}`);

    const response = await this.fetchImpl(apiPath(path), { ...options, headers });
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      const detail = typeof payload === "object" && payload?.detail ? payload.detail : payload;
      throw new ApiError(String(detail || `HTTP ${response.status}`), response.status, payload);
    }
    return payload;
  }

  feed(limit = 30) {
    return this.request(`/feed?limit=${limit}`);
  }

  profile(publicId) {
    return this.request(`/profiles/${encodeURIComponent(publicId)}`);
  }

  myProfile() {
    return this.request("/profiles/me");
  }

  generations(limit = 30) {
    return this.request(`/generations?limit=${limit}`);
  }

  createGeneration(payload) {
    return this.request("/generations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  acceptAdultConsent() {
    return this.request("/adult-consent/accept", { method: "POST" });
  }

  async authenticateTelegram({ botUsername, initData, startPayload = null }) {
    const session = await this.request("/auth/telegram-mini-app", {
      method: "POST",
      body: JSON.stringify({
        bot_username: botUsername,
        init_data: initData,
        start_payload: startPayload,
      }),
    });
    this.token = session.access_token;
    return session;
  }

  async authenticateWeb({ email, displayName }) {
    const session = await this.request("/auth/web-session", {
      method: "POST",
      body: JSON.stringify({ email, display_name: displayName || null }),
    });
    this.token = session.access_token;
    return session;
  }
}
