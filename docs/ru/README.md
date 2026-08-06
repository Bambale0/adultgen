# AdultGen — документация на русском

Этот раздел — русскоязычная точка входа в архитектуру AdultGen.

AdultGen — backend-first платформа для AI-генерации медиа с Telegram-каналами, сохранёнными аватарами, мульти-референсным cinematic workflow, внутренними кредитами, партнёрскими выплатами, adult-лентой, модерацией и сменяемыми ботами-зеркалами.

Текущего production-фронтенда в репозитории нет. Предыдущие реализации Mini App и web-приложения полностью удалены. Причины и условия начала новой реализации описаны в [`FRONTEND_RESET.md`](FRONTEND_RESET.md).

## Для заказчика

- [`CUSTOMER_BRIEF.md`](CUSTOMER_BRIEF.md) — подробное описание продукта, MVP, архитектуры, моделей, платежей, ленты, модерации, админки и рисков.

## Главные технические документы

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — архитектура платформы и границы backend, будущих клиентов и Telegram-ботов.
- [`MODEL_CAPABILITIES.md`](MODEL_CAPABILITIES.md) — возможности Seedream 5 Pro и Seedance 2.0 через Kie, режимы payload, ограничения, роли референсов и правила валидации.
- [`API_CONTRACTS.md`](API_CONTRACTS.md) — основные API-контракты для будущих клиентов, генерации, биллинга, ленты, партнёров, админки и Telegram gateway.
- [`OPERATIONAL_FLOWS.md`](OPERATIONAL_FLOWS.md) — основные runtime-flow: старт, генерация, callback, оплата, публикация, ремикс, рассылки, выплаты и failover зеркал.
- [`SAFETY_COMPLIANCE.md`](SAFETY_COMPLIANCE.md) — adult gate, модерация, запреты, аудит платежей, immutable webhook logging и правила для high-risk сегмента.
- [`FRONTEND_RESET.md`](FRONTEND_RESET.md) — принятое решение об удалении старых реализаций и критерии входа в новый фронтенд.

Английская документация: [`../en/README.md`](../en/README.md). Канонические подробные документы также лежат в корневом [`../`](../) каталоге `docs/`.

## Архитектурные принципы

1. Telegram-боты и будущие web-клиенты — сменяемые gateway-клиенты, а не владельцы данных.
2. Пользователь определяется по `telegram_user_id`, не по конкретному боту.
3. Баланс строится на append-only ledger, а не на изменяемом поле `users.balance`.
4. Платёжные webhook сначала сохраняются как raw immutable records, только потом обрабатываются бизнес-логикой.
5. Генерация асинхронная: handler ставит задачу в очередь и быстро отвечает.
6. Неопубликованные результаты хранятся 24 часа, если не переведены в постоянное хранилище.
7. В профиле и общей ленте хранятся только опубликованные пользователем работы.
8. Adult-лента доступна только после 18+ gate и управляется админской модерацией.
9. AI-режиссёр и другие AI Character — опциональные помощники, а не обязательная часть flow.
10. Возможности моделей нельзя хардкодить в Telegram handlers или UI — они должны идти через capability config и provider payload builder.

## Внешние источники, которые нужно проверять при изменениях

- Kie Seedance 2.0: `https://docs.kie.ai/market/bytedance/seedance-2`
- Kie Seedream 5 Pro Text-to-Image: `https://docs.kie.ai/market/seedream/5-pro-text-to-image`
- Kie Seedream 5 Pro Image-to-Image: `https://docs.kie.ai/market/seedream/5-pro-image-to-image`
- Telegram Mini Apps: `https://core.telegram.org/bots/webapps`
- Telegram Stars для цифровых товаров: `https://core.telegram.org/bots/payments-stars`
- CrocoPay developer docs: `https://crocopay.tech/developer?type=express`

## Правило поддержки двух языков

Если меняется архитектура, биллинг, модели, модерация, API-контракты или публичные product flow — обновляй русскую и английскую документацию в одном PR.
