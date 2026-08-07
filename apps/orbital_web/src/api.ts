export type Capabilities = {
  can_generate: boolean;
  can_publish_profile: boolean;
  can_publish_feed: boolean;
  can_use_payments: boolean;
};

export type WebSession = {
  access_token: string;
  token_type: 'bearer';
  user_id: string;
  telegram_user_id: number;
  email: string;
  display_name: string;
  is_blocked: boolean;
  capabilities: Capabilities;
};

export type AdultConsentStatus = {
  accepted: boolean;
  policy_version: string;
  accepted_at: string | null;
};

export type Publication = {
  id: string;
  user_id: string;
  project_id: string | null;
  scene_take_id: string | null;
  asset_id: string;
  title: string | null;
  description: string | null;
  visibility: 'profile' | 'feed';
  is_explicit: boolean;
  blur_required: boolean;
  allow_remix: boolean;
  prompt_public: boolean;
  status: string;
  published_at: string;
  media_url: string;
  preview_url: string;
  blur_preview_url: string | null;
};

export type GenerationMode =
  | 'image_text_to_image'
  | 'image_to_image'
  | 'video_text_to_video'
  | 'video_image_to_video_first_frame'
  | 'video_image_to_video_first_last_frames'
  | 'video_multimodal_reference_to_video';

export type GenerationResult = {
  asset_id: string;
  role: string;
  media_url: string;
  is_external: boolean;
};

export type GenerationTask = {
  id: string;
  status: string;
  provider: string;
  model_code: string;
  operation: string;
  reserved_credits: number;
  charged_credits: number;
  provider_task_id: string | null;
  error_code: string | null;
  error_message: string | null;
  results: GenerationResult[];
};

export type Profile = {
  id: string;
  public_id: string;
  display_name: string | null;
  bio: string | null;
  visibility: 'public' | 'private';
};

export type CreditPackage = {
  code: string;
  title: string;
  credits: number;
  amount_minor: number;
  amount_major: string;
  currency: string;
  description: string;
  is_popular: boolean;
};

export type WalletBalance = {
  currency: string;
  total_available: number;
  total_reserved: number;
  total_balance: number;
  buckets: { bucket: string; available: number; reserved: number }[];
};

export type PaymentOrder = {
  id: string;
  provider: string;
  package_code: string;
  amount_minor: number;
  currency: string;
  credits_amount: number;
  status: string;
  expires_at: string;
  paid_at: string | null;
  checkout_url: string | null;
  callback_url: string | null;
  provider_checkout_url: string | null;
  external_payment_id: string | null;
};

export type Checkout = { order: PaymentOrder; redirect_url: string };
export type MediaAsset = { id: string; media_type: string; mime_type: string; is_temporary: boolean };

const API = import.meta.env.VITE_CORE_API_URL || '/api';

async function request<T>(
  path: string,
  options: RequestInit & { token?: string; form?: boolean; json?: boolean } = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!options.form) headers.set('Content-Type', 'application/json');
  if (options.token) headers.set('Authorization', `Bearer ${options.token}`);
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Keep HTTP fallback.
    }
    throw new Error(detail);
  }
  if (response.status === 204 || options.json === false) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  mediaUrl(path: string) {
    return path.startsWith('http') ? path : `${API}${path}`;
  },
  createSession(email: string, displayName: string) {
    return request<WebSession>('/auth/web-session', {
      method: 'POST',
      body: JSON.stringify({ email, display_name: displayName }),
    });
  },
  getConsent(token: string) {
    return request<AdultConsentStatus>('/adult-consent', { token });
  },
  acceptConsent(token: string) {
    return request<AdultConsentStatus>('/adult-consent/accept', { method: 'POST', token });
  },
  feed(limit = 30) {
    return request<{ items: Publication[] }>(`/feed?limit=${limit}`);
  },
  savePublication(token: string, publicationId: string) {
    return request<void>(`/collections/saved/${publicationId}`, { method: 'PUT', token, json: false });
  },
  reportPublication(token: string, publicationId: string, category = 'other') {
    return request(`/publications/${publicationId}/reports`, {
      method: 'POST', token, body: JSON.stringify({ category, description: 'Reported from Orbital Web' }),
    });
  },
  async createWorkspace(token: string) {
    const avatar = await request<{ id: string }>('/workspace/avatars', {
      method: 'POST', token, body: JSON.stringify({ name: 'Orbital Operator' }),
    });
    const project = await request<{ id: string }>('/workspace/projects', {
      method: 'POST', token, body: JSON.stringify({ title: 'Orbital Mission', description: 'Created from Orbital Web.' }),
    });
    const scene = await request<{ id: string }>(`/workspace/projects/${project.id}/scenes`, {
      method: 'POST', token, body: JSON.stringify({ title: 'Scene 01', prompt: 'Orbital mission draft', duration: 5 }),
    });
    return { avatar_id: avatar.id, project_id: project.id, scene_id: scene.id };
  },
  generation(token: string, payload: {
    mode: GenerationMode;
    prompt: string;
    negativePrompt: string;
    aspectRatio: string;
    duration: number;
    resolution: string;
    audio: boolean;
    referenceUrls: string[];
    projectId?: string;
    sceneId?: string;
  }) {
    const image = payload.mode.startsWith('image_');
    const modelCode = payload.mode === 'image_text_to_image'
      ? 'seedream-5-pro-text-to-image'
      : payload.mode === 'image_to_image'
        ? 'seedream-5-pro-image-to-image'
        : 'seedance-2.0';
    const requestPayload = image ? {
      prompt: payload.prompt,
      negative_prompt: payload.negativePrompt,
      aspect_ratio: payload.aspectRatio,
      quality: 'high',
      output_format: 'png',
      nsfw_checker: true,
      reference_image_urls: payload.referenceUrls,
    } : {
      prompt: payload.prompt,
      negative_prompt: payload.negativePrompt,
      aspect_ratio: payload.aspectRatio,
      duration: payload.duration,
      resolution: payload.resolution,
      generate_audio: payload.audio,
      return_last_frame: true,
      reference_image_urls: payload.referenceUrls,
    };
    return request<GenerationTask>('/generations', {
      method: 'POST',
      token,
      body: JSON.stringify({
        model_code: modelCode,
        operation: payload.mode,
        project_id: payload.projectId ?? null,
        scene_id: payload.sceneId ?? null,
        request_payload: requestPayload,
      }),
    });
  },
  generations(token: string, limit = 30) {
    return request<{ items: GenerationTask[] }>(`/generations?limit=${limit}`, { token });
  },
  generationById(token: string, id: string) {
    return request<GenerationTask>(`/generations/${id}`, { token });
  },
  uploadReference(token: string, file: File) {
    const body = new FormData();
    body.append('file', file);
    return request<{ asset: MediaAsset }>('/media/uploads/references', { method: 'POST', token, body, form: true });
  },
  profile(token: string) {
    return request<Profile>('/profiles/me', { token });
  },
  updateProfile(token: string, payload: Partial<Pick<Profile, 'display_name' | 'bio' | 'visibility'>>) {
    return request<Profile>('/profiles/me', { method: 'PATCH', token, body: JSON.stringify(payload) });
  },
  myPublications(token: string) {
    return request<{ items: Publication[] }>('/profiles/me/publications', { token });
  },
  packages() {
    return request<{ items: CreditPackage[] }>('/billing/packages');
  },
  wallet(token: string) {
    return request<WalletBalance>('/wallet/me', { token });
  },
  createPaymentOrder(token: string, packageCode: string) {
    return request<PaymentOrder>('/billing/orders', {
      method: 'POST', token, body: JSON.stringify({ package_code: packageCode, provider: 'crocopay' }),
    });
  },
  checkout(token: string, orderId: string) {
    return request<Checkout>(`/billing/orders/${orderId}/crocopay`, { method: 'POST', token });
  },
};
