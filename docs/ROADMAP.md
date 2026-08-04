# AdultGen Implementation Roadmap

## Phase 0 — Repository and architecture baseline

Goal: make the repository ready for implementation.

Deliverables:

- architecture docs;
- data model draft;
- API contracts;
- operational flows;
- safety/compliance rules;
- minimal Python package layout;
- development settings.

## Phase 1 — Core backend foundation

Goal: users, auth, channels, wallet, media metadata.

Tasks:

1. FastAPI app bootstrap.
2. PostgreSQL + SQLAlchemy/Alembic setup.
3. Redis connection.
4. Settings via Pydantic.
5. Telegram channel model.
6. Mini App initData verification.
7. Canonical user upsert by `telegram_user_id`.
8. Wallet ledger tables and service.
9. Media asset table and S3 abstraction.
10. Basic admin auth guard.

Acceptance criteria:

- same Telegram user entering through two configured bots resolves to one `users.id`;
- wallet balance can be reconstructed from ledger entries;
- temp media assets have expiration timestamps;
- no bot token or provider secret is stored in plain app logs.

## Phase 2 — Telegram Gateway

Goal: bot entry, onboarding, result delivery.

Tasks:

1. Aiogram webhook gateway.
2. Multi-channel webhook routing.
3. `/start` with referral/profile payload parsing.
4. Mini App launch buttons.
5. Result delivery API.
6. Delivery retries and `NotificationDelivery` logs.
7. Mirror channel activity tracking.

Acceptance criteria:

- gateway accepts updates from multiple bot configs;
- user/channel activity is tracked;
- generation result can be sent to the user's last active channel;
- failed delivery is retryable and auditable.

## Phase 3 — Mini App MVP

Goal: core user UI.

Pages:

- Home;
- Feed;
- Create;
- Projects;
- Profile;
- My avatars;
- Balance;
- Partner cabinet;
- Settings / 18+ gate;
- Support.

Acceptance criteria:

- Mini App authenticates through server-verified Telegram initData;
- adult gate blocks feed until accepted;
- user can create avatar, project, and scene;
- profile can be public/private;
- saved collection works.

## Phase 4 — Generation pipeline

Goal: Seedream/Seedance async generation.

Tasks:

1. Provider abstraction.
2. Kie.ai adapter.
3. Seedream 5 Pro text-to-image operation.
4. Seedream 5 Pro image-to-image operation.
5. Seedance 2.0 video operation.
6. Reference binding / prompt compiler.
7. Cost estimation.
8. Credit reservation, charge, release.
9. Provider callback ingress.
10. Send result to Telegram.
11. 24h temp media cleanup.

Acceptance criteria:

- user can generate an image and a video;
- video price is calculated per second;
- image price is fixed per operation;
- duplicate provider callbacks do not double-charge;
- provider/system failure returns or releases credits;
- result is sent to Telegram with publish/retry/open buttons.

## Phase 5 — Billing

Goal: paid credits and subscriptions with immutable webhook capture.

Tasks:

1. Billing packages.
2. Subscription plan table.
3. SharPay provider adapter.
4. CrocoPay provider adapter.
5. Billing Gateway checkout token.
6. Payment Webhook Ingress append-only storage.
7. Payment Worker idempotent credit posting.
8. Payment notification through Telegram.
9. Admin payment inspection.

Acceptance criteria:

- raw webhook bytes are saved before processing;
- payment status verification is performed where provider supports it;
- paid order posts exactly one wallet credit operation;
- duplicate callbacks are ignored;
- admin can inspect raw webhook hash chain and order processing state.

## Phase 6 — Publications and feed

Goal: profile/feed publishing and feed rotation.

Tasks:

1. Publication creation from scene take.
2. Permanent media copy on publish.
3. Public/private profile.
4. Global feed endpoint.
5. Likes.
6. Saves to collection.
7. Remix project creation.
8. Reports and moderation cases.
9. Admin feed management.
10. Basic ranking service.

Acceptance criteria:

- nothing auto-publishes;
- feed requires adult consent;
- blur state is respected;
- admin can force blur/hide/delete/boost;
- no private avatar/reference is copied in remix;
- comments are absent in MVP.

## Phase 7 — Partner program

Goal: referral commission and manual payouts.

Tasks:

1. Referral relation capture from start payload.
2. Partner wallet.
3. Commission calculation:
   - 20% first payment;
   - 5% following payments within 90 days.
4. Pending-to-available commission lifecycle.
5. Manual payout requests.
6. Admin payout approval/rejection/paid status.
7. Reversal on refund/chargeback.

Acceptance criteria:

- self-referral is blocked;
- referred user can have only one referrer;
- partner commission is not instantly withdrawable;
- payout freezes available funds;
- admin payout action is audited.

## Phase 8 — Broadcasts and admin expansion

Goal: operational control.

Tasks:

1. Broadcast creation.
2. Text/photo/video messages with buttons.
3. Audience filters:
   - paying/non-paying;
   - active subscription;
   - balance;
   - last activity;
   - bot mirror;
   - feed users;
   - partners.
4. Audience snapshot.
5. Batched sending queue.
6. Delivery report.
7. Admin audit UI.

Acceptance criteria:

- broadcast recipient set is fixed at start;
- sending uses user's reachable channel;
- delivery errors are tracked;
- admin can cancel running broadcast.

## Phase 9 — Experimental multi-scene composition

Goal: manual scenes assembled into a final clip.

Tasks:

1. Scene ordering UI.
2. Strict continuity fields.
3. Last-frame handoff.
4. Approved takes.
5. FFmpeg composition worker.
6. Export presets: 9:16, 16:9, 1:1.
7. Final video publish flow.

Acceptance criteria:

- user manually creates scenes;
- approved scene takes can be assembled;
- final output can be sent to Telegram and published.

## Technical debt intentionally deferred

- fine-grained admin roles;
- comments;
- subscriptions to authors;
- ML recommender;
- public avatar marketplace;
- automated partner payouts;
- advanced consent verification;
- full manual video timeline editor.
