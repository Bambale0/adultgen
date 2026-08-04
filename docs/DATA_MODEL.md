# AdultGen Data Model

This document describes the first MVP database shape. Use PostgreSQL with UUID primary keys, explicit timestamps, and immutable ledger/audit tables.

## Naming rules

- Primary keys: `id UUID`.
- Timestamps: `created_at`, `updated_at`, `deleted_at` when needed.
- Money: store minor units as integers (`amount_minor`) or `NUMERIC(18, 2)` consistently; do not use floats.
- Credits: integer amounts only.
- External provider IDs must be unique per provider.
- High-risk actions require append-only audit entries.

## Users and channels

### users

Canonical platform user. Do not scope by bot.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    language_code TEXT,
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
    can_generate BOOLEAN NOT NULL DEFAULT TRUE,
    can_publish_profile BOOLEAN NOT NULL DEFAULT TRUE,
    can_publish_feed BOOLEAN NOT NULL DEFAULT TRUE,
    can_use_payments BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

### telegram_channels

One connected Telegram bot mirror/channel.

```sql
CREATE TABLE telegram_channels (
    id UUID PRIMARY KEY,
    bot_username TEXT NOT NULL UNIQUE,
    secret_ref TEXT NOT NULL,
    webhook_secret_hash TEXT NOT NULL,
    mini_app_url TEXT,
    status TEXT NOT NULL, -- active, disabled, archived
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

### user_channel_activity

Tracks where the user interacted, without making that channel the user owner.

```sql
CREATE TABLE user_channel_activity (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    telegram_channel_id UUID NOT NULL REFERENCES telegram_channels(id),
    telegram_chat_id BIGINT,
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    start_payload TEXT,
    UNIQUE(user_id, telegram_channel_id)
);
```

## Adult gate

```sql
CREATE TABLE adult_consents (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    policy_version TEXT NOT NULL,
    source_channel_id UUID REFERENCES telegram_channels(id),
    accepted_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ
);
```

## Wallet ledger

### wallets

```sql
CREATE TABLE wallets (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id),
    currency TEXT NOT NULL DEFAULT 'credits',
    cached_available_balance INTEGER NOT NULL DEFAULT 0,
    cached_reserved_balance INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

### wallet_entries

Append-only source of truth.

```sql
CREATE TABLE wallet_entries (
    id UUID PRIMARY KEY,
    wallet_id UUID NOT NULL REFERENCES wallets(id),
    operation_id UUID NOT NULL,
    entry_type TEXT NOT NULL,
    bucket TEXT NOT NULL, -- purchased, subscription, bonus
    amount INTEGER NOT NULL,
    generation_task_id UUID,
    payment_order_id UUID,
    admin_user_id UUID,
    reason TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE(operation_id, entry_type, bucket)
);
```

Entry types:

```text
payment_credit
subscription_credit
bonus_credit
generation_reserve
generation_charge
generation_release
refund
admin_adjustment
chargeback
```

## Payments

### payment_orders

```sql
CREATE TABLE payment_orders (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    provider TEXT NOT NULL, -- sharpay, crocopay
    external_payment_id TEXT,
    checkout_token_hash TEXT NOT NULL UNIQUE,
    package_code TEXT NOT NULL,
    amount_minor BIGINT NOT NULL,
    currency TEXT NOT NULL,
    credits_amount INTEGER NOT NULL,
    status TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE(provider, external_payment_id)
);
```

Statuses:

```text
created
redirected
pending
paid
failed
expired
refunded
chargeback
cancelled
```

### payment_webhook_raw

Must be append-only. Store raw bytes before business processing.

```sql
CREATE TABLE payment_webhook_raw (
    id UUID PRIMARY KEY,
    provider TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    request_method TEXT NOT NULL,
    request_path TEXT NOT NULL,
    query_string TEXT,
    headers JSONB NOT NULL,
    raw_body BYTEA NOT NULL,
    source_ip INET,
    body_sha256 TEXT NOT NULL,
    signature_valid BOOLEAN,
    previous_event_hash TEXT,
    event_hash TEXT NOT NULL UNIQUE
);
```

### payment_webhook_processing

Mutable processing state lives separately from raw webhook.

```sql
CREATE TABLE payment_webhook_processing (
    id UUID PRIMARY KEY,
    webhook_raw_id UUID NOT NULL UNIQUE REFERENCES payment_webhook_raw(id),
    status TEXT NOT NULL, -- queued, processed, ignored, failed, retrying
    attempt_count INTEGER NOT NULL DEFAULT 0,
    payment_order_id UUID REFERENCES payment_orders(id),
    last_error TEXT,
    processed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL
);
```

## Subscriptions and pricing

```sql
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    monthly_credits INTEGER NOT NULL,
    video_second_price INTEGER NOT NULL,
    image_text_price INTEGER NOT NULL,
    image_edit_price INTEGER NOT NULL,
    max_parallel_generations INTEGER NOT NULL,
    max_avatar_profiles INTEGER NOT NULL,
    is_multiscene_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    cancelled_at TIMESTAMPTZ
);

CREATE TABLE model_pricing (
    id UUID PRIMARY KEY,
    model_code TEXT NOT NULL,
    operation TEXT NOT NULL,
    billing_unit TEXT NOT NULL, -- generation, second
    price_per_unit INTEGER NOT NULL,
    plan_id UUID REFERENCES subscription_plans(id),
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ
);
```

## Projects and scenes

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL, -- draft, active, completed, deleted
    output_format TEXT NOT NULL DEFAULT '9:16',
    total_duration_seconds INTEGER,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    deleted_at TIMESTAMPTZ
);

CREATE TABLE scenes (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id),
    order_index INTEGER NOT NULL,
    title TEXT,
    prompt TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    aspect_ratio TEXT NOT NULL,
    camera_notes TEXT,
    action_notes TEXT,
    audio_notes TEXT,
    continuity_notes TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE(project_id, order_index)
);
```

## Avatar profiles

Saved visual avatar is not `AICharacter`.

```sql
CREATE TABLE avatar_profiles (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    cover_asset_id UUID,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    deleted_at TIMESTAMPTZ
);

CREATE TABLE avatar_references (
    id UUID PRIMARY KEY,
    avatar_profile_id UUID NOT NULL REFERENCES avatar_profiles(id),
    asset_id UUID NOT NULL,
    reference_type TEXT NOT NULL, -- portrait, angle, profile, full_body, expression, extra
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL
);
```

## AI Characters

```sql
CREATE TABLE ai_characters (
    id UUID PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    avatar_asset_id UUID,
    system_prompt TEXT NOT NULL,
    model TEXT NOT NULL,
    tools JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE ai_conversations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    ai_character_id UUID NOT NULL REFERENCES ai_characters(id),
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE ai_conversation_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES ai_conversations(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL
);
```

## Media

```sql
CREATE TABLE media_assets (
    id UUID PRIMARY KEY,
    owner_user_id UUID REFERENCES users(id),
    storage_bucket TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    media_type TEXT NOT NULL, -- image, video, audio
    mime_type TEXT NOT NULL,
    size_bytes BIGINT,
    width INTEGER,
    height INTEGER,
    duration_seconds NUMERIC(8, 2),
    checksum_sha256 TEXT,
    telegram_file_id TEXT,
    is_temporary BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE(storage_bucket, storage_key)
);
```

## References and generation

```sql
CREATE TABLE scene_references (
    id UUID PRIMARY KEY,
    scene_id UUID NOT NULL REFERENCES scenes(id),
    asset_id UUID NOT NULL REFERENCES media_assets(id),
    role TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL
);
```

Reference roles:

```text
avatar_identity
main_frame
location
visual_style
lighting
composition
camera_motion
subject_motion
audio_atmosphere
voice
music
first_frame
last_frame
extra
```

```sql
CREATE TABLE generation_tasks (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    scene_id UUID REFERENCES scenes(id),
    provider TEXT NOT NULL,
    model_code TEXT NOT NULL,
    operation TEXT NOT NULL,
    status TEXT NOT NULL,
    request_payload JSONB NOT NULL,
    provider_task_id TEXT,
    reserved_credits INTEGER NOT NULL DEFAULT 0,
    charged_credits INTEGER NOT NULL DEFAULT 0,
    technical_defect_detected BOOLEAN NOT NULL DEFAULT FALSE,
    error_code TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    submitted_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    UNIQUE(provider, provider_task_id)
);

CREATE TABLE scene_takes (
    id UUID PRIMARY KEY,
    generation_task_id UUID NOT NULL REFERENCES generation_tasks(id),
    scene_id UUID NOT NULL REFERENCES scenes(id),
    video_asset_id UUID REFERENCES media_assets(id),
    image_asset_id UUID REFERENCES media_assets(id),
    last_frame_asset_id UUID REFERENCES media_assets(id),
    preview_asset_id UUID REFERENCES media_assets(id),
    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
    quality_score NUMERIC(5, 2),
    continuity_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL
);
```

## Publications and feed

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id),
    public_id TEXT NOT NULL UNIQUE,
    display_name TEXT,
    bio TEXT,
    avatar_asset_id UUID,
    visibility TEXT NOT NULL DEFAULT 'private', -- private, public
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE publications (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    scene_take_id UUID REFERENCES scene_takes(id),
    asset_id UUID NOT NULL REFERENCES media_assets(id),
    title TEXT,
    description TEXT,
    visibility TEXT NOT NULL, -- profile, feed
    is_explicit BOOLEAN NOT NULL DEFAULT TRUE,
    blur_required BOOLEAN NOT NULL DEFAULT TRUE,
    allow_remix BOOLEAN NOT NULL DEFAULT TRUE,
    prompt_public BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL, -- active, hidden, deleted, moderation_hold
    published_at TIMESTAMPTZ NOT NULL,
    deleted_at TIMESTAMPTZ
);

CREATE TABLE feed_events (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    publication_id UUID NOT NULL REFERENCES publications(id),
    event_type TEXT NOT NULL, -- impression, reveal_blur, view_complete, skip, remix_click
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE publication_likes (
    user_id UUID NOT NULL REFERENCES users(id),
    publication_id UUID NOT NULL REFERENCES publications(id),
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (user_id, publication_id)
);

CREATE TABLE saved_publications (
    user_id UUID NOT NULL REFERENCES users(id),
    publication_id UUID NOT NULL REFERENCES publications(id),
    saved_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (user_id, publication_id)
);

CREATE TABLE remix_sources (
    id UUID PRIMARY KEY,
    source_publication_id UUID NOT NULL REFERENCES publications(id),
    new_project_id UUID NOT NULL REFERENCES projects(id),
    remixed_by_user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL
);
```

## Moderation

```sql
CREATE TABLE moderation_cases (
    id UUID PRIMARY KEY,
    publication_id UUID REFERENCES publications(id),
    reported_user_id UUID REFERENCES users(id),
    reporter_user_id UUID REFERENCES users(id),
    category TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    resolution TEXT,
    resolved_by_admin_id UUID,
    created_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ
);
```

Categories:

```text
minor_or_young_looking
non_consensual_identity
public_figure
prohibited_content
violence_or_coercion
spam
wrong_18_marking
copyright
other
```

## Referrals and partner payouts

```sql
CREATE TABLE referral_relations (
    id UUID PRIMARY KEY,
    referrer_user_id UUID NOT NULL REFERENCES users(id),
    referred_user_id UUID NOT NULL UNIQUE REFERENCES users(id),
    attributed_at TIMESTAMPTZ NOT NULL,
    attribution_source TEXT,
    first_payment_at TIMESTAMPTZ,
    commission_until TIMESTAMPTZ
);

CREATE TABLE partner_wallets (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id),
    pending_amount_minor BIGINT NOT NULL DEFAULT 0,
    available_amount_minor BIGINT NOT NULL DEFAULT 0,
    frozen_amount_minor BIGINT NOT NULL DEFAULT 0,
    paid_amount_minor BIGINT NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'RUB'
);

CREATE TABLE partner_commissions (
    id UUID PRIMARY KEY,
    referrer_user_id UUID NOT NULL REFERENCES users(id),
    referred_user_id UUID NOT NULL REFERENCES users(id),
    payment_order_id UUID NOT NULL REFERENCES payment_orders(id),
    percent NUMERIC(5, 2) NOT NULL,
    amount_minor BIGINT NOT NULL,
    status TEXT NOT NULL, -- pending, available, frozen, reversed, paid
    created_at TIMESTAMPTZ NOT NULL,
    available_at TIMESTAMPTZ
);

CREATE TABLE partner_payout_requests (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    amount_minor BIGINT NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL, -- pending, approved, rejected, processing, paid, cancelled
    payout_method TEXT,
    payout_details_encrypted TEXT,
    admin_comment TEXT,
    external_transfer_id TEXT,
    requested_at TIMESTAMPTZ NOT NULL,
    paid_at TIMESTAMPTZ
);
```

## Broadcasts

```sql
CREATE TABLE broadcasts (
    id UUID PRIMARY KEY,
    admin_user_id UUID NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    content_type TEXT NOT NULL, -- text, photo, video
    text TEXT,
    media_asset_id UUID,
    buttons JSONB NOT NULL DEFAULT '[]',
    audience_filter JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE TABLE broadcast_recipients (
    id UUID PRIMARY KEY,
    broadcast_id UUID NOT NULL REFERENCES broadcasts(id),
    user_id UUID NOT NULL REFERENCES users(id),
    telegram_channel_id UUID REFERENCES telegram_channels(id),
    status TEXT NOT NULL,
    telegram_message_id BIGINT,
    error_code TEXT,
    sent_at TIMESTAMPTZ,
    UNIQUE(broadcast_id, user_id)
);
```

## Audit

```sql
CREATE TABLE admin_audit_events (
    id UUID PRIMARY KEY,
    admin_user_id UUID NOT NULL REFERENCES users(id),
    target_type TEXT NOT NULL,
    target_id UUID,
    action TEXT NOT NULL,
    reason TEXT,
    before_state JSONB,
    after_state JSONB,
    created_at TIMESTAMPTZ NOT NULL
);
```

## Essential indexes

```sql
CREATE INDEX idx_users_telegram_user_id ON users(telegram_user_id);
CREATE INDEX idx_generation_tasks_user_status ON generation_tasks(user_id, status);
CREATE INDEX idx_generation_tasks_provider_task ON generation_tasks(provider, provider_task_id);
CREATE INDEX idx_publications_feed_status ON publications(visibility, status, published_at DESC);
CREATE INDEX idx_feed_events_publication_type ON feed_events(publication_id, event_type);
CREATE INDEX idx_payment_orders_user_status ON payment_orders(user_id, status);
CREATE INDEX idx_wallet_entries_wallet_created ON wallet_entries(wallet_id, created_at);
CREATE INDEX idx_webhook_raw_provider_received ON payment_webhook_raw(provider, received_at DESC);
CREATE INDEX idx_user_channel_activity_last_seen ON user_channel_activity(user_id, last_seen_at DESC);
```
