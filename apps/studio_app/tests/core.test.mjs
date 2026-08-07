import test from "node:test";
import assert from "node:assert/strict";
import {
  apiPath,
  buildGenerationPayload,
  escapeHtml,
  estimateCredits,
  filterFeed,
  parseRoute,
} from "../src/core.js";

const baseForm = {
  mode: "image",
  prompt: " neon portrait ",
  aspectRatio: "9:16",
  duration: 5,
  returnLastFrame: true,
};

test("routes feed, publication and profile paths", () => {
  assert.deepEqual(parseRoute("/"), { name: "feed", params: {} });
  assert.deepEqual(parseRoute("/publication/abc"), { name: "publication", params: { id: "abc" } });
  assert.deepEqual(parseRoute("/profile/operator-01"), { name: "profile", params: { publicId: "operator-01" } });
  assert.equal(parseRoute("/unknown").name, "not-found");
});

test("normalizes API paths behind gateway", () => {
  assert.equal(apiPath("feed"), "/api/feed");
  assert.equal(apiPath("/generations"), "/api/generations");
  assert.equal(apiPath("/api/health"), "/api/health");
});

test("builds text-to-image and image-edit generation contracts", () => {
  const text = buildGenerationPayload(baseForm);
  assert.equal(text.model_code, "seedream-5-pro-text-to-image");
  assert.equal(text.operation, "image_text_to_image");
  assert.equal(text.request_payload.prompt, "neon portrait");

  const edit = buildGenerationPayload({ ...baseForm, referenceDataUrl: "data:image/webp;base64,AA" });
  assert.equal(edit.model_code, "seedream-5-pro-image-to-image");
  assert.equal(edit.operation, "image_to_image");
  assert.equal(edit.request_payload.image_urls.length, 1);
});

test("builds Seedance first-frame payload and calculates reserve", () => {
  const video = buildGenerationPayload({ ...baseForm, mode: "video", duration: 10, referenceAssetId: "asset" });
  assert.equal(video.model_code, "seedance-2.0");
  assert.equal(video.operation, "video_image_to_video_first_frame");
  assert.equal(video.request_payload.duration, 10);
  assert.equal(estimateCredits({ mode: "video", duration: 10 }), 100);
});

test("filters feed safely and escapes injected text", () => {
  const items = [{ title: "Neon Rain", author: "@a", tags: ["portrait"], trending: true, following: false }];
  assert.equal(filterFeed(items, "portrait", "live").length, 1);
  assert.equal(filterFeed(items, "", "following").length, 0);
  assert.equal(escapeHtml('<img onerror="x">'), "&lt;img onerror=&quot;x&quot;&gt;");
});
