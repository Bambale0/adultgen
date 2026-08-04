# Operational flows AdultGen

Документ описывает ключевые runtime-сценарии MVP.

## 1. Первый вход через Telegram-бота

```text
/start в любом активном зеркале
        ↓
Telegram Gateway валидирует update
        ↓
Core API ищет User по telegram_user_id
        ↓
Если пользователя нет — создаёт User, Wallet, UserProfile
        ↓
Записывает user_channel_activity
        ↓
Отправляет onboarding и кнопку Mini App
```

Важно: новый бот-зеркало не создаёт нового пользователя. Он только добавляет активность в `user_channel_activity`.

## 2. Mini App auth

```text
Mini App открывается из конкретного бота
        ↓
Frontend получает Telegram.WebApp.initData
        ↓
POST /api/auth/telegram-mini-app
        ↓
Backend выбирает bot token по telegram_channel_id
        ↓
Валидирует подпись initData и auth_date
        ↓
Выдаёт Core JWT
```

Нельзя доверять данным из `initDataUnsafe` на клиенте.

## 3. Создание проекта и сцены

```text
Пользователь создаёт проект
        ↓
Добавляет сцену вручную
        ↓
Пишет описание результата
        ↓
Выбирает duration/aspect_ratio
        ↓
Выбирает avatar profile
        ↓
Добавляет main frame и references
        ↓
Система назначает ReferenceRole каждому файлу
```

AI-режиссёр может быть вызван вручную, но не обязателен.

## 4. Выбор режима модели

Payload builder выбирает один конкретный режим:

```text
Seedream text-to-image
Seedream image-to-image
Seedance text-to-video
Seedance image-to-video first frame
Seedance image-to-video first+last frames
Seedance multimodal reference-to-video
```

Нельзя смешивать mutually exclusive режимы Seedance.

## 5. Расчёт и запуск генерации

```text
POST /api/generations/estimate
        ↓
Core API выбирает active ModelPricing
        ↓
Видео: seconds × price_per_second
Фото: fixed price
        ↓
Пользователь подтверждает цену
        ↓
POST /api/generations/start
        ↓
Wallet ledger создаёт generation_reserve
        ↓
Generation task сохраняет exact request_payload
        ↓
Worker отправляет Kie createTask с callBackUrl
```

Если credits не хватает, task не создаётся.

## 6. Kie callback

```text
Kie вызывает /api/provider-callbacks/kie/{callback_token}
        ↓
Ingress сохраняет raw callback
        ↓
Task определяется по callback token / provider_task_id
        ↓
Если payload неполный — worker запрашивает recordInfo
        ↓
Если success — скачать result URLs в S3
        ↓
Если есть last frame — сохранить media_asset
        ↓
Wallet ledger: generation_charge
        ↓
Telegram Gateway отправляет файл пользователю
```

Если provider fail:

```text
failed callback
        ↓
Сохранить failCode/failMsg
        ↓
Wallet ledger: generation_release или refund
        ↓
Сообщить пользователю в Telegram
```

## 7. Доставка результата в Telegram

```text
Generation completed
        ↓
Core API создаёт delivery request
        ↓
Telegram Gateway выбирает последний активный channel пользователя
        ↓
Отправляет media file + buttons
        ↓
Сохраняет telegram_message_id и telegram_file_id
```

Кнопки:

```text
[Опубликовать]
[Повторить]
[Продолжить сцену]
[Открыть проект]
```

Серверная временная копия хранится 24 часа. Оригинал остаётся в Telegram-чате пользователя.

## 8. Публикация

```text
Пользователь нажимает Опубликовать
        ↓
Выбирает: профиль / общая лента
        ↓
Выбирает blur и allow_remix
        ↓
Если feed — проверяется adult consent
        ↓
Media копируется из temporary bucket в permanent bucket
        ↓
Создаётся Publication
```

Ничего не публикуется автоматически.

## 9. Удаление media по TTL

```text
media_worker периодически ищет expired temporary media
        ↓
Если media не опубликовано — удалить physical object
        ↓
media_assets.deleted_at = now()
        ↓
Generation metadata остаётся для аудита и поддержки
```

Финансовые данные и webhook logs не удаляются.

## 10. Ремикс из ленты

```text
Пользователь нажимает Создать похожее
        ↓
Core API создаёт новый Project
        ↓
Копирует структуру сцен, prompt notes, duration, camera/style notes
        ↓
Не копирует приватные avatar references автора
        ↓
Пользователь выбирает свой avatar/main frame/references
        ↓
Создаётся RemixSource
```

## 11. Платёж

```text
Пользователь выбирает пакет
        ↓
Core API создаёт PaymentOrder и checkout token
        ↓
Billing Gateway открывает checkout page
        ↓
Provider создаёт invoice/payment
        ↓
Пользователь оплачивает
        ↓
Provider отправляет webhook
        ↓
Webhook ingress сохраняет raw bytes
        ↓
Payment worker валидирует подпись и статус
        ↓
Wallet ledger: payment_credit
        ↓
Telegram уведомляет пользователя
```

Повторный webhook не должен повторно начислить кредиты: используется `operation_id` и уникальность provider payment id.

## 12. Партнёрская комиссия

```text
Successful payment
        ↓
Проверить ReferralRelation
        ↓
Если первая оплата — 20%
Если последующие в течение 90 дней — 5%
        ↓
Создать PartnerCommission pending
        ↓
После hold period перевести в available
```

При возврате платежа создаётся обратная проводка комиссии.

## 13. Ручной вывод партнёрских денег

```text
Партнёр создаёт payout request
        ↓
available → frozen
        ↓
Админ проверяет заявку
        ↓
Переводит деньги вручную
        ↓
Указывает method, external_transfer_id, comment
        ↓
status = paid
        ↓
admin_audit_events пишет действие
```

## 14. Рассылки

```text
Админ создаёт Broadcast
        ↓
Система фиксирует audience snapshot
        ↓
Получатели разбиваются на batches
        ↓
Telegram Gateway отправляет через доступный channel
        ↓
Delivery log сохраняет статус каждого получателя
```

Поддерживаются текст, фото, видео и inline-кнопки.

## 15. Failover бот-зеркала

```text
Основной бот недоступен / заблокирован
        ↓
Админ добавляет новый telegram_channel
        ↓
Настраивает webhook и Mini App URL
        ↓
Пользователь открывает новое зеркало
        ↓
telegram_user_id совпадает
        ↓
Core API возвращает тот же User и Wallet
```

Зеркала — механизм continuity/disaster recovery, не способ обхода правил платформы.
