# API-контракты AdultGen

Это русскоязычное описание первого API-surface. Точные схемы позже должны генерироваться из FastAPI/Pydantic через OpenAPI.

## Auth

### Telegram Mini App auth

Mini App отправляет `initData` и идентификатор текущего Telegram channel/bot.

```http
POST /api/auth/telegram-mini-app
```

Request:

```json
{
  "telegram_channel_id": "uuid",
  "init_data": "query-string-from-telegram"
}
```

Сервер:

1. Загружает `telegram_channel.secret_ref`.
2. Валидирует Telegram initData подписью соответствующего bot token.
3. Проверяет свежесть `auth_date`.
4. Upsert canonical user по `telegram_user_id`.
5. Пишет `user_channel_activity`.
6. Возвращает короткоживущий Core JWT.

Response:

```json
{
  "access_token": "jwt",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "telegram_user_id": 123456789,
    "profile_visibility": "public",
    "adult_gate_required": true
  }
}
```

## Пользователь и настройки

```http
GET /api/me
PATCH /api/me/profile
POST /api/me/adult-consent
DELETE /api/me/adult-consent
```

`POST /api/me/adult-consent` фиксирует текущую версию adult-policy.

## Аватары

```http
GET /api/avatar-profiles
POST /api/avatar-profiles
GET /api/avatar-profiles/{id}
DELETE /api/avatar-profiles/{id}
POST /api/avatar-profiles/{id}/references
DELETE /api/avatar-profiles/{id}/references/{reference_id}
```

Создание:

```json
{
  "name": "Alice"
}
```

Добавление reference:

```json
{
  "asset_id": "uuid",
  "reference_type": "portrait",
  "sort_order": 10
}
```

## Media

```http
POST /api/media/upload-url
POST /api/media/telegram-file
GET /api/media/{id}
DELETE /api/media/{id}
```

Upload URL request:

```json
{
  "media_type": "image",
  "mime_type": "image/jpeg",
  "usage": "avatar_reference"
}
```

## Проекты и сцены

```http
GET /api/projects
POST /api/projects
GET /api/projects/{project_id}
PATCH /api/projects/{project_id}
DELETE /api/projects/{project_id}

POST /api/projects/{project_id}/scenes
PATCH /api/scenes/{scene_id}
DELETE /api/scenes/{scene_id}
POST /api/scenes/{scene_id}/reorder
```

Create scene:

```json
{
  "title": "Opening shot",
  "prompt": "A cinematic rainy neon street scene...",
  "duration_seconds": 10,
  "aspect_ratio": "9:16",
  "camera_notes": "slow dolly-in",
  "action_notes": "character walks toward camera",
  "audio_notes": "rain and city ambience"
}
```

## Референсы сцены

```http
POST /api/scenes/{scene_id}/references
PATCH /api/scenes/{scene_id}/references/{reference_id}
DELETE /api/scenes/{scene_id}/references/{reference_id}
```

Request:

```json
{
  "asset_id": "uuid",
  "role": "main_frame",
  "priority": 100,
  "notes": "Use only as the first visual frame"
}
```

Роли должны совпадать с `ReferenceRole` из domain enums и model capabilities.

## Расчёт стоимости и старт генерации

```http
POST /api/generations/estimate
POST /api/generations/start
GET /api/generations/{task_id}
POST /api/generations/{task_id}/retry
```

Estimate request:

```json
{
  "project_id": "uuid",
  "scene_id": "uuid",
  "operation": "video_image_to_video_first_frame",
  "model_code": "seedance-2.0",
  "duration_seconds": 10
}
```

Estimate response:

```json
{
  "operation": "video_image_to_video_first_frame",
  "model_code": "seedance-2.0",
  "billing_unit": "second",
  "price_per_unit": 8,
  "quantity": 10,
  "total_credits": 80,
  "available_balance": 400,
  "balance_after_reserve": 320
}
```

Start request:

```json
{
  "scene_id": "uuid",
  "operation": "video_image_to_video_first_frame",
  "model_code": "seedance-2.0",
  "confirm_cost_credits": 80,
  "provider_options": {
    "return_last_frame": true,
    "resolution": "720p",
    "aspect_ratio": "9:16",
    "generate_audio": false,
    "web_search": false
  }
}
```

Операции Seedance:

```text
video_text_to_video
video_image_to_video_first_frame
video_image_to_video_first_last_frames
video_multimodal_reference_to_video
```

Retry rules:

- пользовательский retry — полная цена;
- provider/system failure — возврат резерва или бесплатный retry;
- technical defect — refund/free retry по настройке системы или решению админа.

## Provider callbacks

```http
POST /api/provider-callbacks/kie/{callback_token}
```

Сервер:

1. Сохраняет raw callback.
2. Находит task по random callback token.
3. При необходимости запрашивает provider task details.
4. Скачивает result URLs.
5. Сохраняет last frame.
6. Charge или release reserved credits.
7. Ставит доставку результата в Telegram.

## Публикации

```http
POST /api/publications
GET /api/publications/{id}
DELETE /api/publications/{id}
POST /api/publications/{id}/report
POST /api/publications/{id}/remix
```

Publish request:

```json
{
  "scene_take_id": "uuid",
  "visibility": "feed",
  "title": "Neon walk",
  "description": "Cinematic rainy scene",
  "is_explicit": true,
  "blur_required": true,
  "allow_remix": true,
  "prompt_public": false
}
```

Правила:

- публикация только вручную;
- публикация копирует media из temporary bucket в permanent bucket;
- feed publication требует adult consent;
- админ может force blur, hide, restore, delete, boost.

## Лента

```http
GET /api/feed
POST /api/feed/{publication_id}/events
POST /api/feed/{publication_id}/like
DELETE /api/feed/{publication_id}/like
POST /api/feed/{publication_id}/save
DELETE /api/feed/{publication_id}/save
```

Feed item содержит:

- signed/cdn media URL;
- preview URL;
- author public profile;
- `is_explicit`;
- `blur_required`;
- liked/saved state;
- allow_remix;
- stats.

## Wallet и billing

```http
GET /api/wallet
GET /api/wallet/entries
GET /api/billing/packages
POST /api/billing/checkout
GET /api/billing/orders/{order_id}
```

Checkout request:

```json
{
  "package_code": "credits_1500",
  "provider": "crocopay"
}
```

Response:

```json
{
  "payment_order_id": "uuid",
  "checkout_url": "https://pay.example.com/checkout/one-time-token",
  "expires_at": "2026-08-04T18:00:00Z"
}
```

## Платёжные webhook

```http
POST /api/payment-webhooks/sharpay/{callback_token}
POST /api/payment-webhooks/crocopay/{callback_token}
```

Жёсткое правило: raw bytes webhook сохраняются до парсинга и бизнес-обновлений.

## Партнёрский кабинет

```http
GET /api/partner/summary
GET /api/partner/commissions
POST /api/partner/payout-requests
GET /api/partner/payout-requests
```

Комиссии:

- 20% с первой успешной оплаты;
- 5% со следующих платежей в течение 90 дней;
- ручная заявка на вывод;
- при заявке деньги переходят из `available` в `frozen`.

## Рассылки

Admin endpoints:

```http
POST /api/admin/broadcasts
GET /api/admin/broadcasts
GET /api/admin/broadcasts/{id}
POST /api/admin/broadcasts/{id}/start
POST /api/admin/broadcasts/{id}/cancel
```

Сегменты:

- платящие/неплатящие;
- активная подписка;
- баланс;
- последняя активность;
- использованное зеркало;
- пользователи ленты;
- партнёры.

## Админская модерация

```http
GET /api/admin/publications
POST /api/admin/publications/{id}/hide
POST /api/admin/publications/{id}/restore
POST /api/admin/publications/{id}/force-blur
POST /api/admin/publications/{id}/boost
POST /api/admin/publications/{id}/delete

GET /api/admin/moderation-cases
PATCH /api/admin/moderation-cases/{id}
```

Каждая admin mutation требует reason и запись в `admin_audit_events`.
