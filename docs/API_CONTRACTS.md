# AdultGen API Contracts

This document defines the first API surface. Exact schemas can later be generated with OpenAPI from FastAPI/Pydantic models.

## Auth principles

### Telegram Mini App auth

Client sends Telegram `initData` plus current bot channel identifier.

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

Server behavior:

1. Load `telegram_channel.secret_ref`.
2. Verify Telegram initData signature with the matching bot token.
3. Check `auth_date` age.
4. Upsert canonical user by `telegram_user_id`.
5. Record `user_channel_activity`.
6. Return short-lived Core JWT.

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

### Telegram bot gateway auth

Telegram webhook URLs must include an unpredictable path and validate Telegram's webhook secret header. The gateway maps the webhook to a configured `telegram_channel`.

## Users and settings

```http
GET /api/me
PATCH /api/me/profile
POST /api/me/adult-consent
DELETE /api/me/adult-consent
```

`POST /api/me/adult-consent` records the current policy version.

## Avatar profiles

```http
GET /api/avatar-profiles
POST /api/avatar-profiles
GET /api/avatar-profiles/{id}
DELETE /api/avatar-profiles/{id}
POST /api/avatar-profiles/{id}/references
DELETE /api/avatar-profiles/{id}/references/{reference_id}
```

Create avatar:

```json
{
  "name": "Alice"
}
```

Add reference:

```json
{
  "asset_id": "uuid",
  "reference_type": "portrait",
  "sort_order": 10
}
```

## Media uploads

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

Response:

```json
{
  "asset_id": "uuid",
  "upload_url": "https://s3-presigned-url",
  "expires_in": 900
}
```

## Projects and scenes

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

Create project:

```json
{
  "title": "Night neon scene",
  "description": "Short cinematic clip",
  "output_format": "9:16"
}
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

## Scene references

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

## Cost estimation and generation

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
  "operation": "video",
  "model_code": "seedance-2.0",
  "duration_seconds": 10
}
```

Estimate response:

```json
{
  "operation": "video",
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
  "operation": "video",
  "model_code": "seedance-2.0",
  "confirm_cost_credits": 80,
  "provider_options": {
    "return_last_frame": true
  }
}
```

Start response:

```json
{
  "task_id": "uuid",
  "status": "queued",
  "reserved_credits": 80
}
```

Status values:

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

Retry rules:

- user-requested retry: full price;
- provider/system failure: release reservation or free retry;
- detected technical defect: admin/system-configurable refund or free retry.

## Provider callbacks

Kie-compatible callback endpoint:

```http
POST /api/provider-callbacks/kie/{callback_token}
```

Behavior:

1. Store raw callback in provider callback log.
2. Resolve task by random callback token.
3. Verify provider status by API when needed.
4. Download/store result metadata.
5. Charge or release reserved credits.
6. Enqueue Telegram delivery.

## Publications

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

Rules:

- Nothing is published automatically.
- Publication copies the media asset from temporary bucket to permanent bucket.
- Feed publication requires adult consent.
- Admin can force blur, hide, restore, delete, or boost.

## Feed

```http
GET /api/feed
POST /api/feed/{publication_id}/events
POST /api/feed/{publication_id}/like
DELETE /api/feed/{publication_id}/like
POST /api/feed/{publication_id}/save
DELETE /api/feed/{publication_id}/save
```

Feed query:

```http
GET /api/feed?cursor=...&limit=20&explicit=allowed
```

Feed item response:

```json
{
  "id": "uuid",
  "asset_url": "signed-url-or-cdn-url",
  "preview_url": "signed-url-or-cdn-url",
  "media_type": "video",
  "author": {
    "public_id": "a8Pk3mQ",
    "display_name": "Creator"
  },
  "is_explicit": true,
  "blur_required": true,
  "liked": false,
  "saved": false,
  "allow_remix": true,
  "stats": {
    "likes": 120,
    "saves": 18
  }
}
```

## Wallet and billing

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

## Payment webhooks

Provider endpoints:

```http
POST /api/payment-webhooks/sharpay/{callback_token}
POST /api/payment-webhooks/crocopay/{callback_token}
```

Hard rule: raw webhook bytes must be saved before any provider-specific parsing or business updates.

## Partner cabinet

```http
GET /api/partner/summary
GET /api/partner/commissions
POST /api/partner/payout-requests
GET /api/partner/payout-requests
```

Summary:

```json
{
  "referral_link": "https://t.me/active_bot?start=ref_xxx",
  "invited_users": 24,
  "paying_users": 5,
  "pending_amount_minor": 120000,
  "available_amount_minor": 45000,
  "frozen_amount_minor": 0,
  "paid_amount_minor": 150000,
  "currency": "RUB"
}
```

Commission rules:

- 20% from first successful payment;
- 5% from next payments within 90 days;
- manual payout request;
- partner money moves from `available` to `frozen` at request creation.

## Broadcasts

Admin endpoints:

```http
POST /api/admin/broadcasts
GET /api/admin/broadcasts
GET /api/admin/broadcasts/{id}
POST /api/admin/broadcasts/{id}/start
POST /api/admin/broadcasts/{id}/cancel
```

Create request:

```json
{
  "title": "New model launch",
  "content_type": "photo",
  "text": "Новая модель доступна",
  "media_asset_id": "uuid",
  "buttons": [
    {"text": "Открыть", "url": "https://t.me/bot/app"}
  ],
  "audience_filter": {
    "paid": true,
    "has_active_subscription": null,
    "min_balance": 0,
    "last_active_after": "2026-07-01T00:00:00Z",
    "channel_id": null,
    "feed_users": null,
    "partners": null
  }
}
```

## Admin moderation

```http
GET /api/admin/publications
PATCH /api/admin/publications/{id}
POST /api/admin/publications/{id}/hide
POST /api/admin/publications/{id}/restore
POST /api/admin/publications/{id}/force-blur
POST /api/admin/publications/{id}/boost
POST /api/admin/publications/{id}/delete

GET /api/admin/moderation-cases
PATCH /api/admin/moderation-cases/{id}
```

Every admin mutation must require a reason and write `admin_audit_events`.

## Telegram gateway internal API

```http
POST /internal/telegram/send-generation-result
POST /internal/telegram/send-broadcast-message
POST /internal/telegram/send-payment-notification
```

Generation result payload:

```json
{
  "user_id": "uuid",
  "preferred_channel_id": "uuid",
  "media_asset_id": "uuid",
  "caption": "✅ Генерация завершена",
  "buttons": [
    {"text": "Опубликовать", "callback_data": "publish:..."},
    {"text": "Повторить", "callback_data": "retry:..."},
    {"text": "Открыть проект", "web_app_url": "https://app.example.com/projects/..."}
  ]
}
```
