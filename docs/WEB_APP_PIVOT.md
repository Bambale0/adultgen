# Web-first product pivot

## Decision

AdultGen is now a website application first. Telegram remains important, but it is no longer the primary product surface.

The main product surface is:

```text
Website App -> Core API -> PostgreSQL / Redis / Media storage / Workers
```

Telegram becomes:

```text
Telegram Bot / Mini App -> Companion channel -> Core API
```

## Why this change is correct

The reference product is closer to a web SaaS generator than to a Telegram bot. The user should land on a website, pass the 18+ gate, create media in a full studio, manage credits, view projects, publish to profile/feed, and return later from any browser.

Telegram should still be used for:

- quick login or account linking;
- notifications when generation is complete;
- support;
- referral/profile deep links;
- fallback access through mirrors;
- optional Mini App entry for Telegram-native users.

## What stays valid from previous work

The existing backend-first architecture remains valid because Core API owns the data and Telegram does not own the product state.

Already useful foundations:

- users and canonical identity;
- wallet ledger;
- generation task lifecycle;
- Kie submit boundary;
- media storage abstraction;
- adult consent policy;
- workspace: avatars, projects, scenes;
- profiles;
- saved collection;
- Telegram gateway as companion channel.

## Product surface after pivot

The website app should contain these top-level routes:

```text
/
/age-gate
/studio
/projects
/avatars
/feed
/collection
/profile
/billing
/partners
/support
```

### Public landing

Purpose:

- explain the product;
- show generated examples that are safe to preview;
- lead to age gate and registration;
- avoid exposing explicit content before user consent.

### Age gate

Purpose:

- require 18+ confirmation before adult feed/studio access;
- show safety policy;
- explain forbidden content categories;
- store policy acceptance server-side.

### Studio

The studio is the main value surface.

It should support:

- prompt input;
- negative prompt;
- model/mode selection;
- image generation;
- video generation;
- avatar selection;
- reference upload;
- camera/motion/audio notes;
- cost preview;
- credit reserve before launch;
- task status;
- result preview;
- publish/save/delete actions.

### Projects and scenes

Purpose:

- organize generation work;
- manage scenes;
- reuse avatars and references;
- continue from last frame;
- keep multi-scene flow available later.

### Feed and profile

Purpose:

- show published media;
- enforce adult consent and blur settings;
- support likes, collection save, remix, profile open, report.

### Billing

Purpose:

- show current credits;
- sell credit packs;
- manage subscription later;
- keep Telegram Stars and external checkout compliance separated.

## Route responsibility

The website app must not duplicate backend business rules. It should call Core API.

Client-side responsibilities:

- layout;
- forms;
- local validation for UX;
- route guards;
- rendering task status;
- upload interactions.

Backend responsibilities:

- identity;
- age consent source of truth;
- wallet ledger;
- pricing;
- reservation and charge/release;
- generation validation;
- media storage;
- publication visibility;
- moderation constraints;
- webhook processing.

## Updated epic order

### Phase 3B — Web App Foundation

1. Create `apps/web_app`.
2. Add website route manifest.
3. Add landing shell.
4. Add web 18+ gate shell.
5. Add studio shell.
6. Add shared Core API client.
7. Add web auth placeholder for email/session and Telegram linking later.

### Phase 4 — Web Studio

1. Prompt and negative prompt form.
2. Model/mode selector using model capabilities.
3. Avatar selector.
4. Reference upload surface.
5. Cost preview.
6. Generation launch using existing `/generations` endpoint.
7. Task status and result preview.

### Phase 5 — Web Billing

1. Credits page.
2. Payment order creation.
3. External checkout page.
4. Payment webhook handling.
5. Subscription plans.
6. Partner attribution.

### Phase 6 — Feed and Profile

1. Publish result to profile.
2. Publish result to feed.
3. Feed list and blur handling.
4. Like/save/remix/report.
5. Public profile page.

### Phase 7 — Admin and Moderation

1. Publication moderation.
2. Complaint queue.
3. User sanctions.
4. Admin audit.
5. Broadcasts.

## Telegram after pivot

Telegram should not disappear. It becomes a companion channel:

- `/start` opens website/Mini App link;
- generation complete notifications;
- support entry;
- fallback mirror access;
- referral/profile deep links;
- optional Mini App for users who prefer staying inside Telegram.

## Non-goals of this pivot PR

This pivot does not implement full generation UI, billing, or feed rendering. It changes the development direction and creates the website app foundation so future work is ordered correctly.
