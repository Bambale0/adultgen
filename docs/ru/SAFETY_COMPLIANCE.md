# Safety, compliance и high-risk controls

AdultGen работает в high-risk adult-сегменте, поэтому безопасность, аудит и модерация являются частью архитектуры, а не дополнительным слоем после запуска.

## Основные риски

- жалобы на Telegram-бота и блокировки зеркал;
- диспуты по оплате;
- спорные начисления кредитов;
- публикация запрещённого контента;
- использование чужой внешности без согласия;
- материалы с несовершеннолетними или young-looking персонажами;
- утечки приватных avatar references;
- удаление финансовой истории;
- попытки обходить ограничения провайдера или платформы.

## 18+ gate

Доступ к adult-ленте только после явного подтверждения.

```text
Вам исполнилось 18 лет?
Вы подтверждаете, что хотите видеть взрослый контент?

[Мне есть 18 лет]
[Выйти]
```

Сохраняется:

```text
user_id
policy_version
source_channel_id
accepted_at
revoked_at
```

Blur по умолчанию должен быть включён для explicit-контента, пока пользователь не изменит настройку.

## Публичная лента

В общей ленте разрешён explicit-контент только после 18+ gate. Пользователь может включить blur при публикации, а админ может принудительно включить blur независимо от выбора автора.

Модераторские действия:

- hide;
- restore;
- delete;
- force blur;
- remove from feed only;
- disable remix;
- boost;
- unboost;
- lock publication;
- mark as moderation hold.

Каждое действие пишет `admin_audit_events`.

## Запрещённые категории

Блокируются на уровне генерации, публикации и жалоб:

- несовершеннолетние и young-looking персонажи в explicit context;
- публичные личности в explicit context;
- чужое лицо без подтверждённого согласия;
- сексуальное насилие, принуждение, exploitation;
- скрытая съёмка / voyeuristic сценарии;
- зоофилия;
- инцест;
- торговля людьми;
- контент, нарушающий правила провайдера, платёжки или Telegram;
- попытки выдать запрещённый контент за безопасный.

## Avatar references

Аватары — приватные. Они не копируются при ремиксе и не раскрываются другим пользователям.

При удалении аватара:

- media object удаляется физически;
- `avatar_profile` получает `deleted_at`;
- финансовая и generation metadata остаётся только в минимальном виде.

Для будущих версий можно добавить consent record для чужих лиц, но в MVP лучше считать avatar references приватными и принадлежащими пользователю.

## Immutable payment webhook logging

Любой платёжный webhook сначала сохраняется как raw record.

```text
PaymentWebhookRaw
- provider
- received_at
- request_method
- request_path
- query_string
- headers
- raw_body
- source_ip
- body_sha256
- signature_valid
- previous_event_hash
- event_hash
```

Состояние обработки хранится отдельно:

```text
PaymentWebhookProcessing
- webhook_raw_id
- status
- attempt_count
- payment_order_id
- last_error
- processed_at
```

Raw webhook нельзя редактировать или удалять. Для этого желательно использовать отдельного DB-пользователя с правами `INSERT` и `SELECT`, но без `UPDATE`/`DELETE`.

## Wallet safety

Баланс пользователя — это результат ledger-проводок.

Запрещено:

```text
users.balance += 100
```

Разрешено:

```text
wallet_entries.insert(payment_credit)
wallet_entries.insert(generation_reserve)
wallet_entries.insert(generation_charge)
wallet_entries.insert(generation_release)
wallet_entries.insert(refund)
```

Все операции должны иметь `operation_id`, чтобы повторный webhook или retry не создали двойное начисление.

## Refund rules

Бесплатный возврат или retry:

- provider failure;
- system failure;
- битый результат;
- technical defect, обнаруженный системой.

Полностью платный retry:

- пользователь хочет новый вариант;
- пользователь передумал;
- пользователь меняет идею;
- пользователь хочет улучшить результат без technical defect.

## Платёжные провайдеры

В коде есть адаптеры:

```text
SharPayProvider
CrocoPayProvider
```

Но production activation — отдельное бизнес-решение. Нужно получить подтверждение, что провайдер согласен обслуживать фактическую категорию проекта. Нельзя маскировать назначение сервиса, потому что это создаёт риск заморозки средств и блокировки merchant account.

## Telegram Stars и цифровые товары

Если продажа цифровых товаров/услуг происходит внутри Telegram Mini App или bot flow, Telegram требует использовать Stars. Внешний сайт может существовать как отдельный checkout surface, но нельзя считать его безопасным способом обхода правил Telegram.

Архитектура должна поддерживать разные payment providers, но финальный production-flow должен быть согласован с правилами платформы.

## Зеркала ботов

Зеркала нужны для continuity/disaster recovery:

- основной бот заблокирован;
- нужно подключить новый bot username;
- пользователи сохраняют баланс по `telegram_user_id`;
- backend остаётся тем же.

Зеркала не должны использоваться для автоматической ротации, сокрытия владельца или обхода модерации Telegram.

## Жалобы

Причины жалоб:

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

Жалоба создаёт `ModerationCase`, а не просто сообщение админу.

## Админский аудит

Каждое опасное действие требует reason:

- ручное изменение баланса;
- удаление публикации;
- force blur;
- hide/restore;
- payout paid/rejected;
- изменение price table;
- подключение нового зеркала;
- блокировка пользователя.

`before_state` и `after_state` сохраняются в `admin_audit_events`.

## Хранение данных

Удаляем физически:

- avatar references после удаления аватара;
- временные generation media после 24 часов;
- неопубликованные дубли;
- reference files удалённых проектов, если они больше нигде не используются.

Не удаляем:

- wallet ledger;
- payment orders;
- payment webhook raw;
- admin audit;
- partner commissions/payout history;
- минимальную generation metadata для поддержки и финансовых споров.

## Implementation checklist

Перед production:

- включить 18+ gate;
- проверить moderation categories;
- реализовать force blur;
- сделать immutable webhook raw table;
- внедрить ledger idempotency;
- добавить callback recovery worker;
- проверить provider terms и merchant approval;
- протестировать bot mirror failover;
- протестировать физическое удаление avatar references;
- протестировать публикацию и удаление из коллекций;
- включить admin audit для всех опасных действий.
