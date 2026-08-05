export type UserCapabilities = {
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
  capabilities: UserCapabilities;
};

export type AdultConsentStatus = {
  accepted: boolean;
  policy_version: string;
  accepted_at: string | null;
};

export type CreateWorkspaceResponse = {
  avatar_id: string;
  project_id: string;
  scene_id: string;
};

export type MediaAsset = {
  id: string;
  storage_bucket: string;
  storage_key: string;
  media_type: string;
  mime_type: string;
  size_bytes: number | null;
  checksum_sha256: string | null;
  is_temporary: boolean;
  expires_at: string | null;
  deleted_at: string | null;
};

export type MediaUploadResponse = {
  asset: MediaAsset;
};

export type PublicationVisibility = 'profile' | 'feed';

export type Publication = {
  id: string;
  user_id: string;
  project_id: string | null;
  scene_take_id: string | null;
  asset_id: string;
  title: string | null;
  description: string | null;
  visibility: PublicationVisibility;
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

export type FeedResponse = {
  items: Publication[];
};

export type GenerationMode =
  | 'image_text_to_image'
  | 'image_to_image'
  | 'video_text_to_video'
  | 'video_image_to_video_first_frame'
  | 'video_image_to_video_first_last_frames'
  | 'video_multimodal_reference_to_video';

export type StudioGenerationRequest = {
  mode: GenerationMode;
  prompt: string;
  negative_prompt: string;
  duration_seconds: number;
  aspect_ratio: string;
  resolution: string;
  generate_audio: boolean;
  reference_urls: string[];
  avatar_id?: string;
  project_id?: string;
  scene_id?: string;
};

export type GenerationResultAsset = {
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
  results: GenerationResultAsset[];
};

export type GenerationListResponse = {
  items: GenerationTask[];
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

export type CreditPackageListResponse = {
  items: CreditPackage[];
};

export type PaymentProvider = 'crocopay' | 'sharpay';

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

export type ProviderCheckoutResponse = {
  order: PaymentOrder;
  redirect_url: string;
};

export type WalletBucketBalance = {
  bucket: string;
  available: number;
  reserved: number;
};

export type WalletBalance = {
  currency: string;
  total_available: number;
  total_reserved: number;
  total_balance: number;
  buckets: WalletBucketBalance[];
};

const CORE_API_URL = import.meta.env.VITE_CORE_API_URL || '/api';

export function coreMediaUrl(path: string): string {
  return path.startsWith('http') ? path : `${CORE_API_URL}${path}`;
}

export async function createWebSession(email: string, displayName: string): Promise<WebSession> {
  return request<WebSession>('/auth/web-session', {
    method: 'POST',
    body: JSON.stringify({ email, display_name: displayName }),
  });
}

export async function fetchAdultConsent(accessToken: string): Promise<AdultConsentStatus> {
  return request<AdultConsentStatus>('/adult-consent', { accessToken });
}

export async function acceptAdultConsent(accessToken: string): Promise<AdultConsentStatus> {
  return request<AdultConsentStatus>('/adult-consent/accept', {
    method: 'POST',
    accessToken,
  });
}

export async function createStarterWorkspace(accessToken: string): Promise<CreateWorkspaceResponse> {
  const avatar = await request<{ id: string }>('/workspace/avatars', {
    method: 'POST',
    accessToken,
    body: JSON.stringify({ name: 'Web Studio Avatar' }),
  });
  const project = await request<{ id: string }>('/workspace/projects', {
    method: 'POST',
    accessToken,
    body: JSON.stringify({ title: 'Web Studio Project', description: 'Created from website Studio.' }),
  });
  const scene = await request<{ id: string }>(`/workspace/projects/${project.id}/scenes`, {
    method: 'POST',
    accessToken,
    body: JSON.stringify({ title: 'Scene 1', prompt: 'Draft scene from website Studio.', duration: 5 }),
  });

  return {
    avatar_id: avatar.id,
    project_id: project.id,
    scene_id: scene.id,
  };
}

export async function uploadTemporaryMedia(accessToken: string, file: File): Promise<MediaUploadResponse> {
  return uploadMedia('/media/uploads/temporary', accessToken, file);
}

export async function uploadReferenceMedia(accessToken: string, file: File): Promise<MediaUploadResponse> {
  return uploadMedia('/media/uploads/references', accessToken, file);
}

export async function importExternalMedia(accessToken: string, assetId: string): Promise<MediaAsset> {
  return request<MediaAsset>(`/media/assets/${assetId}/import-external`, {
    method: 'POST',
    accessToken,
  });
}

export async function createPublication(
  accessToken: string,
  payload: {
    asset_id: string;
    title: string;
    description: string;
    visibility: PublicationVisibility;
    is_explicit: boolean;
    blur_required: boolean;
    allow_remix: boolean;
    prompt_public: boolean;
    project_id?: string | null;
  },
): Promise<Publication> {
  return request<Publication>('/publications', {
    method: 'POST',
    accessToken,
    body: JSON.stringify(payload),
  });
}

export async function fetchFeed(limit = 30): Promise<FeedResponse> {
  return request<FeedResponse>(`/feed?limit=${limit}`);
}

export async function fetchMyPublications(accessToken: string): Promise<FeedResponse> {
  return request<FeedResponse>('/profiles/me/publications', { accessToken });
}

export async function fetchSavedCollection(accessToken: string): Promise<{ items: { publication_id: string; saved_at: string }[] }> {
  return request<{ items: { publication_id: string; saved_at: string }[] }>('/collections/saved', { accessToken });
}

export async function savePublication(accessToken: string, publicationId: string): Promise<void> {
  await request(`/collections/saved/${publicationId}`, { method: 'PUT', accessToken });
}

export async function unsavePublication(accessToken: string, publicationId: string): Promise<void> {
  await request(`/collections/saved/${publicationId}`, { method: 'DELETE', accessToken, expectJson: false });
}

export async function createGenerationTask(
  accessToken: string,
  payload: StudioGenerationRequest,
): Promise<GenerationTask> {
  const modelAndOperation = getModelAndOperation(payload.mode);
  return request<GenerationTask>('/generations', {
    method: 'POST',
    accessToken,
    body: JSON.stringify({
      model_code: modelAndOperation.model_code,
      operation: modelAndOperation.operation,
      project_id: payload.project_id || null,
      scene_id: payload.scene_id || null,
      request_payload: buildProviderPayload(payload),
    }),
  });
}

export async function fetchGenerationTask(accessToken: string, taskId: string): Promise<GenerationTask> {
  return request<GenerationTask>(`/generations/${taskId}`, { accessToken });
}

export async function fetchMyGenerations(accessToken: string, limit = 30): Promise<GenerationListResponse> {
  return request<GenerationListResponse>(`/generations?limit=${limit}`, { accessToken });
}

export async function fetchMyProfile(accessToken: string): Promise<Profile> {
  return request<Profile>('/profiles/me', { accessToken });
}

export async function updateMyProfile(
  accessToken: string,
  payload: Partial<Pick<Profile, 'display_name' | 'bio' | 'visibility'>>,
): Promise<Profile> {
  return request<Profile>('/profiles/me', {
    method: 'PATCH',
    accessToken,
    body: JSON.stringify(payload),
  });
}

export async function fetchCreditPackages(): Promise<CreditPackageListResponse> {
  return request<CreditPackageListResponse>('/billing/packages');
}

export async function createPaymentOrder(
  accessToken: string,
  packageCode: string,
  provider: PaymentProvider = 'crocopay',
): Promise<PaymentOrder> {
  return request<PaymentOrder>('/billing/orders', {
    method: 'POST',
    accessToken,
    body: JSON.stringify({ package_code: packageCode, provider }),
  });
}

export async function initiateCrocoPayCheckout(
  accessToken: string,
  orderId: string,
): Promise<ProviderCheckoutResponse> {
  return request<ProviderCheckoutResponse>(`/billing/orders/${orderId}/crocopay`, {
    method: 'POST',
    accessToken,
  });
}

export async function fetchWalletBalance(accessToken: string): Promise<WalletBalance> {
  return request<WalletBalance>('/wallet/me', { accessToken });
}

function getModelAndOperation(mode: GenerationMode): { model_code: string; operation: GenerationMode } {
  if (mode === 'image_text_to_image') {
    return { model_code: 'seedream-5-pro-text-to-image', operation: mode };
  }
  if (mode === 'image_to_image') {
    return { model_code: 'seedream-5-pro-image-to-image', operation: mode };
  }
  return { model_code: 'seedance-2.0', operation: mode };
}

function buildProviderPayload(payload: StudioGenerationRequest): Record<string, unknown> {
  const common = {
    prompt: payload.prompt,
    negative_prompt: payload.negative_prompt,
    aspect_ratio: payload.aspect_ratio,
  };

  if (payload.mode.startsWith('image_')) {
    return {
      ...common,
      quality: 'high',
      output_format: 'png',
      nsfw_checker: true,
      reference_image_urls: payload.reference_urls,
    };
  }

  return {
    ...common,
    duration: payload.duration_seconds,
    resolution: payload.resolution,
    generate_audio: payload.generate_audio,
    return_last_frame: true,
    reference_image_urls: payload.reference_urls,
  };
}

async function uploadMedia(path: string, accessToken: string, file: File): Promise<MediaUploadResponse> {
  const body = new FormData();
  body.append('file', file);
  return request<MediaUploadResponse>(path, {
    method: 'POST',
    accessToken,
    body,
    skipJsonContentType: true,
  });
}

async function request<T = unknown>(
  path: string,
  options: RequestInit & { accessToken?: string; skipJsonContentType?: boolean; expectJson?: boolean } = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!options.skipJsonContentType) headers.set('Content-Type', 'application/json');
  if (options.accessToken) headers.set('Authorization', `Bearer ${options.accessToken}`);

  const response = await fetch(`${CORE_API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const fallback = `${response.status} ${response.statusText}`;
    let detail = fallback;
    try {
      const body = await response.json();
      detail = typeof body.detail === 'string' ? body.detail : fallback;
    } catch {
      detail = fallback;
    }
    throw new Error(detail);
  }

  if (options.expectJson === false || response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}
