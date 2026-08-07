const ROUTES = new Set(["feed", "create", "projects", "profile", "billing"]);

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function parseRoute(pathname) {
  const segments = String(pathname || "/")
    .split("/")
    .filter(Boolean)
    .map((segment) => decodeURIComponent(segment));

  if (segments.length === 0) return { name: "feed", params: {} };
  if (segments[0] === "publication" && segments[1]) {
    return { name: "publication", params: { id: segments[1] } };
  }
  if (segments[0] === "profile" && segments[1]) {
    return { name: "profile", params: { publicId: segments[1] } };
  }
  if (ROUTES.has(segments[0])) return { name: segments[0], params: {} };
  return { name: "not-found", params: {} };
}

export function apiPath(path) {
  const normalized = String(path || "").startsWith("/") ? String(path) : `/${path}`;
  return normalized.startsWith("/api/") ? normalized : `/api${normalized}`;
}

export function buildGenerationPayload(form) {
  const mode = form.mode === "video" ? "video" : "image";
  const hasReference = Boolean(form.referenceDataUrl || form.referenceAssetId);
  const requestPayload = {
    prompt: String(form.prompt || "").trim(),
    aspect_ratio: form.aspectRatio || "9:16",
  };

  if (mode === "video") {
    requestPayload.duration = Number(form.duration || 5);
    requestPayload.resolution = form.resolution || "720p";
    requestPayload.return_last_frame = Boolean(form.returnLastFrame);
    if (hasReference) requestPayload.first_frame_url = form.referenceAssetUrl || "demo://local-reference";
    return {
      model_code: "seedance-2.0",
      operation: hasReference
        ? "video_image_to_video_first_frame"
        : "video_text_to_video",
      request_payload: requestPayload,
      project_id: form.projectId || null,
      scene_id: form.sceneId || null,
    };
  }

  if (hasReference) {
    requestPayload.image_urls = [form.referenceAssetUrl || "demo://local-reference"];
  }
  return {
    model_code: hasReference
      ? "seedream-5-pro-image-to-image"
      : "seedream-5-pro-text-to-image",
    operation: hasReference ? "image_to_image" : "image_text_to_image",
    request_payload: requestPayload,
    project_id: form.projectId || null,
    scene_id: form.sceneId || null,
  };
}

export function estimateCredits(form) {
  if (form.mode === "video") return Math.max(5, Number(form.duration || 5)) * 10;
  return form.referenceDataUrl || form.referenceAssetId ? 24 : 20;
}

export function filterFeed(items, query, tab = "live") {
  const needle = String(query || "").trim().toLocaleLowerCase("ru");
  let filtered = Array.from(items || []);
  if (tab === "trending") filtered = filtered.filter((item) => item.trending);
  if (tab === "following") filtered = filtered.filter((item) => item.following);
  if (!needle) return filtered;
  return filtered.filter((item) => {
    const haystack = [item.title, item.author, ...(item.tags || [])].join(" ").toLocaleLowerCase("ru");
    return haystack.includes(needle);
  });
}

export function formatCompactNumber(value) {
  const number = Number(value || 0);
  if (number >= 1_000_000) return `${(number / 1_000_000).toFixed(number >= 10_000_000 ? 0 : 1)}M`;
  if (number >= 1_000) return `${(number / 1_000).toFixed(number >= 10_000 ? 0 : 1)}K`;
  return String(number);
}

export function readBoolean(storage, key, fallback = false) {
  const value = storage?.getItem?.(key);
  if (value === null || value === undefined) return fallback;
  return value === "1" || value === "true";
}
