# AdultGen Safety, Compliance, and Abuse Controls

AdultGen is intended for adult-oriented creative generation, but the platform must still block clearly illegal, exploitative, non-consensual, or provider-prohibited use cases. This document is a product/engineering control list, not legal advice.

## Core principles

1. Adult content is allowed only after 18+ gate.
2. Explicit feed media is blurred by default unless user settings allow reveal.
3. Admin can force blur, hide, delete, or exclude any publication.
4. Public feed is stricter than private generation.
5. Financial, webhook, and admin audit records are immutable/append-only.
6. Payment providers must approve the actual business category before production activation.
7. Bot mirrors are channel-continuity infrastructure, not a system for rule evasion.

## Hard-block categories

The product must block or route to admin review when content appears to involve:

- minors or young-looking subjects in sexual contexts;
- non-consensual sexual content;
- sexualized public figures;
- identity misuse / real-person impersonation without consent;
- coercion, blackmail, trafficking, or exploitation;
- sexual violence;
- hidden camera / voyeurism framing;
- bestiality;
- incest framing;
- instructions to bypass platform or provider enforcement;
- payment fraud, refund abuse, or chargeback abuse.

## Identity and avatar controls

MVP decision: avatar profiles are private saved photo sets.

Required controls:

- user must confirm they have rights/consent to use uploaded avatar references;
- avatar references are never copied when another user remixes a publication;
- public feed remix copies only scene structure and public metadata;
- admin can remove publications involving identity complaints;
- future face-consent verification can be added without schema rewrite.

## Adult gate

Store:

```text
AdultConsent
- user_id
- policy_version
- accepted_at
- source_channel_id
- revoked_at
```

If policy changes, force new acceptance.

## Feed visibility

Publication fields:

```text
is_explicit
blur_required
allow_remix
prompt_public
status
```

Rules:

- feed access requires adult consent;
- user can choose blur preference;
- system/admin can force blur regardless of author choice;
- no comments in MVP;
- likes/saves/remixes/reports are allowed;
- manual swipe only.

## Moderation cases

Report categories:

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

Moderation statuses:

```text
new
triaged
waiting_admin
resolved_hidden
resolved_deleted
resolved_restored
rejected
```

## Admin powers

Admin can:

- hide publication;
- restore publication;
- delete publication;
- force blur;
- disable remix;
- exclude from recommendations;
- boost temporarily;
- block user's feed publishing;
- block user's generation;
- freeze partner payouts;
- adjust wallet with mandatory reason;
- disable a bot mirror;
- inspect webhook/payment logs.

Every action must write `admin_audit_events`.

## Payment compliance

SharPay and CrocoPay adapters must be coded behind an abstraction, but production activation depends on provider approval.

Required provider checks before launch:

- adult-content category approval;
- allowed countries / merchant residency;
- refund/chargeback process;
- recurrent billing support if subscriptions are automated;
- webhook signature docs;
- invoice status verification endpoint;
- payout/settlement rules.

Do not mislabel the service or hide the actual category from payment providers.

## Payment dispute evidence

For every payment, store:

- payment order;
- checkout package and exact amount;
- raw webhook bytes;
- webhook headers;
- signature validation result;
- provider status verification result;
- wallet ledger entry;
- Telegram notification delivery status;
- admin actions if manually corrected.

## Immutable webhook chain

Each `payment_webhook_raw` record should include:

```text
body_sha256
previous_event_hash
event_hash
```

Suggested event hash:

```text
sha256(provider + received_at + body_sha256 + previous_event_hash)
```

This makes later tampering easier to detect.

## Generation abuse controls

MVP minimum:

- per-user active generation limits;
- global provider concurrency limits;
- prompt/reference pre-check before provider submission;
- provider result status validation;
- user retry is paid;
- system/provider failure releases or refunds credits;
- repeated abuse can disable `can_generate`.

## Data deletion rules

User can delete:

- avatar references;
- avatar profile;
- project;
- scene;
- publication;
- saved collection item.

Do not delete:

- wallet ledger;
- payment orders;
- raw webhooks;
- admin audit;
- partner commission records;
- minimal generation task metadata needed for disputes.

When deleting avatar/reference media, physically remove file objects from storage.

## Logging boundaries

Never log:

- bot tokens;
- provider API keys;
- raw payment credentials;
- unencrypted payout details;
- signed S3 URLs after expiry not needed;
- full JWTs.

Do log:

- request IDs;
- task IDs;
- provider task IDs;
- payment order IDs;
- webhook hashes;
- user IDs as internal UUIDs;
- admin actor IDs;
- delivery errors.

## Mirror policy

Technical goal:

- keep balances and accounts independent from a specific Telegram bot;
- allow connecting a new bot channel if the old channel is unavailable.

Forbidden product behavior:

- automatic bot rotation to evade enforcement;
- hiding source or business category from platforms/providers;
- spamming users from mirrors;
- storing separate balances per mirror.
