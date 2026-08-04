# Возможности моделей и provider payloads

Этот документ — русскоязычный source-of-truth по использованию моделей Kie Market в AdultGen. UX, расчёт стоимости, валидация, provider payload builder, retry-логика и continuation flow должны опираться на эти capabilities, а не на хардкод в Telegram handlers или Mini App.

## Основные модели

```text
Image generation:
- seedream/5-pro-text-to-image

Image editing:
- seedream/5-pro-image-to-image

Video generation:
- bytedance/seedance-2
```

Все три модели работают через Kie task interface:

```http
POST /api/v1/jobs/createTask
```

В production нужно использовать `callBackUrl` как основной способ получения результата. Polling через task endpoint допускается только как fallback для админки, debug tools и recovery worker.

## Общий lifecycle Kie-задачи

Внутренние статусы AdultGen:

```text
created
queued
submitted
provider_processing
completed
failed
refunded
cancelled
```

Правила:

- сохранять точный provider request в `generation_tasks.request_payload` до submit;
- сохранять `provider_task_id` с уникальностью `(provider, provider_task_id)`;
- скачивать provider result URLs сразу, потому что ссылки могут истекать;
- сохранять `creditsConsumed`, `costTime`, `failCode`, `failMsg` и provider `state`, если они есть;
- если callback потерян, recovery worker запрашивает task details по `provider_task_id`.

## Seedream 5 Pro Text-to-Image

Модель:

```text
seedream/5-pro-text-to-image
```

Использование в AdultGen:

- создание основного кадра по тексту;
- генерация cinematic stills;
- создание keyframe/storyboard кандидатов;
- создание обложек профиля/ленты;
- подготовка визуального референса перед видео.

Базовый input:

```json
{
  "prompt": "...",
  "aspect_ratio": "9:16",
  "quality": "basic",
  "output_format": "png",
  "nsfw_checker": false
}
```

Правила AdultGen:

- `prompt` собирается из описания сцены, камеры, действия, света, стиля и continuity notes;
- `aspect_ratio` берётся из capability config;
- `quality` нельзя хардкодить: это provider option;
- `output_format` должен быть configurable, default — `png`;
- `nsfw_checker` всегда явно передаётся в payload;
- биллинг — фиксированная цена за image generation.

## Seedream 5 Pro Image-to-Image

Модель:

```text
seedream/5-pro-image-to-image
```

Использование в AdultGen:

- редактирование пользовательского main frame;
- подготовка first frame для Seedance;
- улучшение света, композиции, фона, стиля;
- усиление сходства с avatar references;
- создание более стабильного кадра перед дорогой видео-генерацией.

Базовый input:

```json
{
  "prompt": "...",
  "image_urls": ["https://..."],
  "aspect_ratio": "9:16",
  "quality": "basic",
  "output_format": "png",
  "nsfw_checker": true
}
```

Правила AdultGen:

- `image_urls` могут включать main frame, avatar references и scene references;
- порядок важен: main frame первым, затем identity/avatar, затем style/location;
- каждый reference обязан иметь `ReferenceRole`;
- для identity consistency prompt должен явно говорить, что сохранять;
- биллинг — фиксированная цена за image edit.

## Seedance 2.0 Video

Модель:

```text
bytedance/seedance-2
```

Seedance нельзя моделировать как один generic `video`. Это четыре разных операции с разными правилами валидации.

### 1. Text-to-Video

Используется, когда нет строгого визуального кадра.

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

Подходит для быстрого теста идеи и низкоконтрольной cinematic generation.

### 2. Image-to-Video — First Frame

Используется, когда нужно оживить один основной кадр.

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

Это лучший default для MVP, если пользователь подготовил хороший main frame через Seedream.

### 3. Image-to-Video — First + Last Frames

Используется для строгого перехода или контролируемого финала.

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

Подходит для:

- переходов между сценами;
- controlled transformation;
- continuation с ожидаемым финальным кадром.

### 4. Multimodal Reference-to-Video

Используется, когда пользователь даёт несколько image/video/audio references.

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

Подходит для advanced mode:

- motion/camera reference;
- audio atmosphere reference;
- визуального стиля;
- сложных cinematic constraints.

## Взаимоисключающие режимы Seedance

Нельзя смешивать всё в один payload. Три сценария взаимоисключающие:

```text
- Image-to-Video first frame
- Image-to-Video first + last frames
- Multimodal Reference-to-Video
```

Если пользователь хочет `first_frame + last_frame + много reference`, payload-builder должен выбрать один режим:

1. **Строгий переход** — first/last frame mode, reference arrays не отправляются.
2. **Reference-driven generation** — multimodal mode, start/end описываются в prompt, но без строгой pixel guarantee.

UI обязан объяснить этот tradeoff, а не молча отправлять невалидный payload.

## Опции Seedance, которые нужно сохранить

### `duration`

Видео биллится за секунду. MVP target — до 15 секунд на одну генерацию.

### `resolution`

Не хардкодить навсегда. Default может быть `720p`, но значения должны идти из capability config.

### `aspect_ratio`

Vertical-first: `9:16`. Также поддерживать `16:9`, `1:1` и другие provider-supported значения через config.

### `generate_audio`

Первоклассная настройка. По умолчанию `false`, кроме случаев, когда пользователь явно хочет звук или добавил audio reference.

### `reference_audio_urls`

Для multimodal mode. Хранить как `media_assets.media_type = audio` и `ReferenceRole = audio_atmosphere | voice | music`.

### `reference_video_urls`

Для camera/motion reference. Роли: `camera_motion` и `subject_motion`.

### `return_last_frame`

Для multi-scene и continuation flow default — `true`. Last frame сохраняется как `media_asset` и связывается с `scene_takes.last_frame_asset_id`.

### `web_search`

Всегда явно передавать. Default — `false`. Если включать позже, это отдельная user-visible capability, потому что влияет на privacy, cost и compliance.

## ReferenceRole → provider payload mapping

| ReferenceRole | Seedream T2I | Seedream I2I | Seedance first-frame | Seedance first+last | Seedance multimodal |
| --- | --- | --- | --- | --- | --- |
| `main_frame` | prompt only | `image_urls[0]` | `first_frame_url` | `first_frame_url` | `reference_image_urls` + prompt role note |
| `first_frame` | prompt only | image input | `first_frame_url` | `first_frame_url` | reference image + prompt role note |
| `last_frame` | prompt only | image input | invalid | `last_frame_url` | reference image + prompt role note |
| `avatar_identity` | prompt notes | `image_urls` | prompt + first frame | prompt + first/last | `reference_image_urls` + identity note |
| `location` | prompt | `image_urls` | prompt | prompt | `reference_image_urls` |
| `visual_style` | prompt | `image_urls` | prompt | prompt | `reference_image_urls` |
| `lighting` | prompt | `image_urls` | prompt | prompt | `reference_image_urls` |
| `composition` | prompt | `image_urls` | prompt | prompt | `reference_image_urls` |
| `camera_motion` | prompt | not preferred | prompt | prompt | `reference_video_urls` |
| `subject_motion` | prompt | not preferred | prompt | prompt | `reference_video_urls` |
| `audio_atmosphere` | invalid | invalid | prompt/audio | prompt/audio | `reference_audio_urls` |
| `voice` | invalid | invalid | prompt/audio later | prompt/audio later | `reference_audio_urls` |
| `music` | invalid | invalid | prompt/audio later | prompt/audio later | `reference_audio_urls` |

## Capability config

Provider limits не должны быть разбросаны по коду. Нужен объект/таблица capabilities:

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
  "default_aspect_ratio": "9:16"
}
```

## Требования к prompt compiler

Prompt должен собираться секциями:

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

Для multimodal mode обязательно добавлять interpretation rules:

```text
Use reference image 1 for character identity only.
Use reference image 2 for lighting only; do not copy people from it.
Use reference video 1 for camera movement only.
Use reference audio 1 for atmosphere only.
```

## Валидация перед submit

Перед вызовом Kie:

- проверить, что модель активна;
- проверить, что операция поддерживается;
- проверить обязательные поля;
- проверить взаимоисключающие поля;
- проверить типы медиа и роли reference;
- проверить срок жизни temporary URLs;
- проверить подтверждённую стоимость;
- зарезервировать кредиты;
- сохранить точный request payload.

## Открытые вопросы для первых integration tests

- точные accepted `aspect_ratio` для каждого endpoint;
- точные `quality` values и влияние на цену/latency;
- точные `resolution` values Seedance 2.0;
- максимальные counts/size/duration для image/video/audio references;
- форма `resultJson`, особенно имя поля last frame URL;
- поведение `nsfw_checker` на конкретном Kie account;
- влияет ли `web_search=true` на compliance и moderation review.
