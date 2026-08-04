# Model Capabilities and Provider Payloads

This file is the source of truth for how AdultGen uses Kie Market models. Product UX, cost estimation, validation, provider payload building, retries, and continuation flows must be driven by these capabilities instead of hardcoded assumptions in Telegram handlers or Mini App screens.

## Primary model ids

```text
Image generation:
- seedream/5-pro-text-to-image

Image editing:
- seedream/5-pro-image-to-image

Video generation:
- bytedance/seedance-2
```

All three models use the Kie Market task interface:

```http
POST /api/v1/jobs/createTask
```

Production jobs must prefer `callBackUrl` over polling. Polling through the unified task endpoint remains a fallback for admin/debug tools and callback recovery.

## Common Kie task lifecycle

AdultGen maps Kie task states to internal `generation_tasks.status`.

```text
Kie waiting/generating/queuing -> provider_processing
Kie success                    -> completed
Kie fail                       -> failed
```

Kie task details are available through the unified endpoint:

```http
GET /api/v1/jobs/recordInfo?taskId=<provider_task_id>
```

Operational rules:

- Always store the original provider request in `generation_tasks.request_payload`.
- Always store `provider_task_id` with `UNIQUE(provider, provider_task_id)`.
- Always download provider result URLs immediately because generated URLs may expire.
- Always record `creditsConsumed`, `costTime`, `failCode`, `failMsg`, and provider `state` when available.
- If callback is missed, a recovery worker can query the task endpoint by `provider_task_id`.

## Seedream 5 Pro: Text to Image

Provider model:

```text
seedream/5-pro-text-to-image
```

Purpose in AdultGen:

- Create a main frame from text.
- Generate initial cinematic stills.
- Generate storyboard/keyframe candidates.
- Create feed/profile cover frames.
- Create base visual references before video.

Required core input:

```json
{
  "prompt": "...",
  "aspect_ratio": "1:1",
  "quality": "basic",
  "output_format": "png",
  "nsfw_checker": false
}
```

AdultGen rules:

- `prompt` is built from the scene description plus structured fields: camera, action, lighting, style, and continuity notes.
- `aspect_ratio` must be selected from provider-supported options configured in `model_capabilities`.
- `quality` must be exposed as a provider capability, not hardcoded to one value.
- `output_format` must be configurable; default to `png` for maximum downstream editing quality.
- `nsfw_checker` must be explicit in every payload. Do not rely on provider defaults.
- Billing unit: fixed price per image generation.

Example payload:

```json
{
  "model": "seedream/5-pro-text-to-image",
  "callBackUrl": "https://api.example.com/webhooks/kie/generation",
  "input": {
    "prompt": "cinematic vertical scene...",
    "aspect_ratio": "9:16",
    "quality": "basic",
    "output_format": "png",
    "nsfw_checker": false
  }
}
```

## Seedream 5 Pro: Image to Image

Provider model:

```text
seedream/5-pro-image-to-image
```

Purpose in AdultGen:

- Edit a user-provided main frame.
- Prepare first frame for Seedance.
- Normalize avatar references into a usable cinematic still.
- Adjust lighting, composition, style, outfit, background, or scene mood.
- Generate an improved/consistent still before spending video credits.

Required core input:

```json
{
  "prompt": "...",
  "image_urls": ["https://..."],
  "aspect_ratio": "1:1",
  "quality": "basic",
  "output_format": "png",
  "nsfw_checker": true
}
```

AdultGen rules:

- `image_urls` can include the main frame, avatar references, and scene references. The exact maximum must live in provider capability config.
- Reference order matters. Put main frame first, then avatar identity images, then style/location extras.
- Every uploaded reference must have a `ReferenceRole`; do not send unlabeled blobs blindly.
- If the user wants identity consistency, use the strongest portrait/avatar references and write explicit prompt constraints.
- Billing unit: fixed price per image edit.

Example payload:

```json
{
  "model": "seedream/5-pro-image-to-image",
  "callBackUrl": "https://api.example.com/webhooks/kie/generation",
  "input": {
    "prompt": "keep the face identity and pose, adjust cinematic lighting...",
    "image_urls": [
      "https://cdn.example.com/main-frame.png",
      "https://cdn.example.com/avatar-portrait.png"
    ],
    "aspect_ratio": "9:16",
    "quality": "basic",
    "output_format": "png",
    "nsfw_checker": true
  }
}
```

## Seedance 2.0: Video

Provider model:

```text
bytedance/seedance-2
```

Seedance 2.0 must not be represented internally as one generic `video` mode. It has distinct scenarios with different validation rules and payload shapes.

### Scenario 1: Text to Video

Use when the user provides only a prompt and no strict visual frame.

```json
{
  "prompt": "...",
  "duration": 15,
  "resolution": "720p",
  "aspect_ratio": "9:16",
  "generate_audio": false,
  "web_search": false,
  "return_last_frame": true
}
```

AdultGen use:

- Fast idea testing.
- Drafting a scene without references.
- Low-control cinematic generation.

### Scenario 2: Image to Video — first frame

Use when the user wants to animate a single main frame.

```json
{
  "prompt": "...",
  "first_frame_url": "https://cdn.example.com/first.png",
  "duration": 15,
  "resolution": "720p",
  "aspect_ratio": "9:16",
  "generate_audio": false,
  "web_search": false,
  "return_last_frame": true
}
```

AdultGen use:

- Main MVP path after Seedream prepares a strong first frame.
- Best default when identity/pose must start from a known still.

### Scenario 3: Image to Video — first and last frames

Use when the user needs a strict transition or controlled ending.

```json
{
  "prompt": "...",
  "first_frame_url": "https://cdn.example.com/first.png",
  "last_frame_url": "https://cdn.example.com/last.png",
  "duration": 15,
  "resolution": "720p",
  "aspect_ratio": "9:16",
  "generate_audio": false,
  "web_search": false,
  "return_last_frame": true
}
```

AdultGen use:

- Scene-to-scene transitions.
- Controlled transformation.
- Continuation where the endpoint must be stable.

### Scenario 4: Multimodal Reference to Video

Use when the user provides multiple image/video/audio references and wants the model to infer style, motion, camera, or atmosphere.

```json
{
  "prompt": "...",
  "reference_image_urls": ["https://cdn.example.com/ref-1.png"],
  "reference_video_urls": ["https://cdn.example.com/motion.mp4"],
  "reference_audio_urls": ["https://cdn.example.com/ambience.mp3"],
  "duration": 15,
  "resolution": "720p",
  "aspect_ratio": "9:16",
  "generate_audio": true,
  "web_search": false,
  "return_last_frame": true
}
```

AdultGen use:

- Advanced user mode.
- Motion/camera reference workflows.
- Audio atmosphere reference workflows.
- Cinematic output with multiple constraints.

### Mutual exclusion rule

Do not mix these as if they were one mode. Kie documents the following Seedance scenarios as mutually exclusive:

```text
- Image-to-Video with first frame
- Image-to-Video with first and last frames
- Multimodal Reference-to-Video with reference images/videos/audio
```

If the user wants `first_frame + last_frame + many references`, the payload-builder must make a choice:

1. Strict transition: use first/last frame mode and drop multimodal reference arrays.
2. Reference-driven generation: use multimodal mode and describe which reference image should be treated as start/end in the prompt, without strict pixel guarantee.

The UI must explain this tradeoff instead of silently sending an invalid mixed payload.

## Seedance options AdultGen must expose or preserve

### `duration`

- Video is billed per second.
- MVP UI should support the provider-supported duration values through config.
- Current product target is up to 15 seconds for one generation.

### `resolution`

- Must be configurable per model/plan.
- Default can be `720p`, but the API and DB must not assume only one resolution forever.

### `aspect_ratio`

- Must support vertical feed first (`9:16`).
- Also keep `16:9`, `1:1`, and other provider-supported values configurable.

### `generate_audio`

- Must be a first-class option.
- In MVP default to false unless user explicitly wants generated audio or supplied audio reference.
- If `generate_audio=true`, store audio expectations in `scene.audio_notes` and generated result metadata.

### `reference_audio_urls`

- Supports audio reference workflows in multimodal mode.
- Store audio references as `media_assets.media_type = audio` and `ReferenceRole` = `audio_atmosphere`, `voice`, or `music`.

### `reference_video_urls`

- Supports camera/motion reference workflows in multimodal mode.
- Store video references as `ReferenceRole` = `camera_motion` or `subject_motion`.

### `return_last_frame`

- Must default to true for multi-scene and continuation workflows.
- The returned last frame should be saved as a `media_asset` and linked through `scene_takes.last_frame_asset_id`.
- Next-scene UX should offer `Use previous last frame`.

### `web_search`

- Must be explicit in provider payload.
- Default to false.
- If enabled later, treat it as a separate user-visible capability because it may change cost, privacy, prompt behavior, and compliance review.

## Reference role to provider payload mapping

AdultGen collects many semantic reference roles, but Kie payloads accept URL arrays. Mapping must be deterministic.

| ReferenceRole | Seedream T2I | Seedream I2I | Seedance first-frame | Seedance first+last | Seedance multimodal |
| --- | --- | --- | --- | --- | --- |
| `main_frame` | prompt text only | `image_urls[0]` | `first_frame_url` | `first_frame_url` | `reference_image_urls` + prompt role note |
| `first_frame` | prompt text only | image input | `first_frame_url` | `first_frame_url` | reference image + prompt role note |
| `last_frame` | prompt text only | image input | invalid | `last_frame_url` | reference image + prompt role note |
| `avatar_identity` | prompt identity notes | `image_urls` | prompt + first frame | prompt + first/last frame | `reference_image_urls` + identity note |
| `location` | prompt | `image_urls` after identity/main | prompt | prompt | `reference_image_urls` |
| `visual_style` | prompt | `image_urls` after identity/main | prompt | prompt | `reference_image_urls` |
| `lighting` | prompt | `image_urls` after identity/main | prompt | prompt | `reference_image_urls` |
| `composition` | prompt | `image_urls` after identity/main | prompt | prompt | `reference_image_urls` |
| `camera_motion` | prompt | not preferred | prompt | prompt | `reference_video_urls` |
| `subject_motion` | prompt | not preferred | prompt | prompt | `reference_video_urls` |
| `audio_atmosphere` | invalid | invalid | `generate_audio` prompt | `generate_audio` prompt | `reference_audio_urls` |
| `voice` | invalid | invalid | prompt/audio later | prompt/audio later | `reference_audio_urls` |
| `music` | invalid | invalid | prompt/audio later | prompt/audio later | `reference_audio_urls` |

## Capability config shape

Do not scatter provider limits around the codebase. Keep a DB/config object similar to this:

```json
{
  "provider": "kie",
  "model_code": "seedance-2.0",
  "provider_model": "bytedance/seedance-2",
  "operations": [
    "video_text_to_video",
    "video_image_to_video_first_frame",
    "video_image_to_video_first_last_frames",
    "video_multimodal_reference_to_video"
  ],
  "billing_unit": "second",
  "supports_callback": true,
  "supports_polling": true,
  "supports_return_last_frame": true,
  "supports_generate_audio": true,
  "supports_web_search": true,
  "duration_values": [5, 10, 15],
  "default_duration": 15,
  "resolution_values": ["720p"],
  "default_resolution": "720p",
  "aspect_ratio_values": ["9:16", "16:9", "1:1"],
  "default_aspect_ratio": "9:16",
  "mutually_exclusive_groups": [
    ["first_frame_url", "last_frame_url", "reference_image_urls", "reference_video_urls", "reference_audio_urls"]
  ]
}
```

The exact provider limits should be changed by config/migrations, not by code edits.

## Prompt compiler requirements

The prompt compiler must build different prompt sections depending on operation:

```text
[Scene intent]
[Character/avatar identity constraints]
[Action and body motion]
[Camera and lens behavior]
[Lighting and style]
[Audio expectation]
[Continuity constraints]
[Reference interpretation rules]
[Negative / avoid instructions]
```

For multimodal mode, always add interpretation rules:

```text
Use reference image 1 for character identity only.
Use reference image 2 for lighting only; do not copy people from it.
Use reference video 1 for camera movement only.
Use reference audio 1 for atmosphere only.
```

This is mandatory because otherwise the provider can mix identity, outfit, location, and style references unpredictably.

## UX consequences

The Mini App must not show one universal upload bucket. It should show:

```text
- Main frame
- Avatar references
- First frame
- Last frame
- Image references
- Video motion references
- Audio references
- Professional mapping mode
```

The UI can remain simple, but internally every reference must have a role and every generation start must select one concrete provider scenario.

## Billing consequences

```text
Seedream text-to-image     -> fixed image generation price
Seedream image-to-image    -> fixed image edit price
Seedance video             -> duration_seconds * video_second_price
```

Future surcharges can be added for:

- higher resolution;
- high quality;
- generated audio;
- advanced multimodal mode;
- priority queue.

Do not add those until provider pricing and product packaging are confirmed.

## Validation rules before provider submit

Before calling Kie:

- Check model exists and is active.
- Check selected operation is supported by model.
- Check required fields for that operation.
- Check mutually exclusive fields.
- Check media types match reference roles.
- Check temporary URLs are accessible and will not expire too early.
- Check cost was confirmed by the user.
- Reserve credits before submit.
- Store exact request payload before submit.

## Callback processing rules

On provider callback:

1. Store raw callback/request body when feasible.
2. Verify `taskId` belongs to an existing generation task.
3. Query task detail if callback payload is incomplete.
4. Download all result URLs immediately.
5. Save last frame if returned.
6. Send media to Telegram chat.
7. Charge or release reserved credits.
8. Keep provider error details for support/admin review.

## Open implementation questions

These must be verified during first real integration tests:

- Exact accepted `aspect_ratio` values for each Seedream/Seedance endpoint.
- Exact accepted `quality` values and whether they affect cost/latency.
- Exact accepted `resolution` values for Seedance 2.0.
- Exact maximum counts and duration/size limits for image/video/audio reference arrays.
- Shape of Seedance callback `resultJson`, especially last-frame URL naming.
- Behavior of `nsfw_checker` for the chosen merchant/API account.
- Whether `web_search=true` changes moderation/compliance requirements.
