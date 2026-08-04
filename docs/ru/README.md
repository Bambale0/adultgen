# AdultGen — документация на русском

Этот раздел — русскоязычная точка входа в архитектуру AdultGen.

AdultGen — Telegram-first платформа для AI-генерации медиа с Mini App, сохранёнными аватарами, мульти-референсным cinematic workflow, внутренними кредитами, партнёрскими выплатами, общей adult-лентой, модерацией и сменяемыми Telegram-ботами-зеркалами.

## Для заказчика

- [`CUSTOMER_BRIEF.md`](CUSTOMER_BRIEF.md) — подробное описание утверждённого проекта для заказчика: продукт, MVP, архитектура, модели, платежи, лента, модерация, админка, риски и следующий этап разработки.

## Главные технические документы

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — архитектура платформы, границы backend/Mini App/ботов, зеркала, генерация, биллинг, лента и админка.
- [`MODEL_CAPABILITIES.md`](MODEL_CAPABILITIES.md) — возможности Seedream 5 Pro и Seedance 2.0 через Kie, режимы payload, ограничения, роли референсов и правила валидации.
- [`API_CONTRACTS.md`](API_CONTRACTS.md) — русская версия основных API-контрактов для Mini App, генерации, биллинга, ленты, партнёров, админки и Telegram gateway.
- [`OPERATIONAL_FLOWS.md`](OPERATIONAL_FLOWS.md) — основные runtime-flow: старт, генерация, callback, оплата, публикация, ремикс, рассылки, выплаты и failover зеркал.
- [`SAFETY_COMPLIANCE.md`](SAFETY_COMPLIANCE.md) — adult gate, модерация, запреты, аудит платежей, immutable webhook logging и правила для high-risk сегмента.

Английская документация: [`../en/README.md`](../en/README.md). Канонические подробные документы также лежат в корневом [`../`](../) каталоге `docs/`.

## Архитектурные принципы

1. Telegram-боты — сменяемые gateway-клиенты, а не владельцы данных.
2. Пользователь определяется по `telegram_user_id`, не по конкретному боту.
3. Баланс строится на append-only ledger, а не на изменяемом поле `users.balance`.
4. Платёжные webhook сначала сохраняются как raw immutable records, только потом обрабатываются бизнес-логикой.
5. Генерация асинхронная: handler ставит задачу в очередь и быстро отвечает.
6. Неопубликованные результаты хранятся на сервере 24 часа, потому что оригинал отправляется пользователю в Telegram-чат.
7. В профиле и общей ленте хранятся только опубликованные пользователем работы.
8. Adult-лента доступна только после 18+ gate и управляется админской модерацией.
9. AI-режиссёр и другие AI Character — опциональные помощники, а не обязательная часть flow.
10. Возможности моделей нельзя хардкодить в Telegram handlers — они должны идти через capability config и provider payload builder.

## Внешние источники, которые нужно проверять при изменениях

- Kie Seedance 2.0: `https://docs.kie.ai/market/bytedance/seedance-2`
- Kie Seedream 5 Pro Text-to-Image: `https://docs.kie.ai/market/seedream/5-pro-text-to-image`
- Kie Seedream 5 Pro Image-to-Image: `https://docs.kie.ai/market/seedream/5-pro-image-to-image`
- Telegram Mini Apps: `https://core.telegram.org/bots/webapps`
- Telegram Stars для цифровых товаров: `https://core.telegram.org/bots/payments-stars`
- CrocoPay developer docs: `https://crocopay.tech/developer?type=express`

## Правило поддержки двух языков

Если меняется архитектура, биллинг, модели, модерация, API-контракты или публичные product flow — обновляй русскую и английскую документацию в одном PR.
