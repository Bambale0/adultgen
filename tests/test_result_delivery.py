import pytest

from adultgen.telegram_gateway.result_delivery import (
    ResultDeliveryCommand,
    ResultDeliveryError,
    TelegramDeliveryMediaKind,
    deliver_generation_result,
)


class FakeTelegramResultClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def send_text(self, **kwargs) -> int:
        self.calls.append(("send_text", kwargs))
        return 101

    async def send_photo(self, **kwargs) -> int:
        self.calls.append(("send_photo", kwargs))
        return 102

    async def send_video(self, **kwargs) -> int:
        self.calls.append(("send_video", kwargs))
        return 103

    async def send_document(self, **kwargs) -> int:
        self.calls.append(("send_document", kwargs))
        return 104


@pytest.mark.asyncio
async def test_deliver_text_result_uses_send_text() -> None:
    client = FakeTelegramResultClient()

    result = await deliver_generation_result(
        client,
        command=ResultDeliveryCommand(
            chat_id=123,
            media_kind=TelegramDeliveryMediaKind.TEXT,
            caption="✅ Готово",
        ),
    )

    assert result.telegram_message_id == 101
    assert client.calls == [
        (
            "send_text",
            {"chat_id": 123, "text": "✅ Готово", "reply_markup": None},
        )
    ]


@pytest.mark.asyncio
async def test_deliver_image_result_uses_send_photo() -> None:
    client = FakeTelegramResultClient()

    result = await deliver_generation_result(
        client,
        command=ResultDeliveryCommand(
            chat_id=123,
            media_kind=TelegramDeliveryMediaKind.IMAGE,
            caption="✅ Фото готово",
            telegram_file_id="photo-file-id",
        ),
    )

    assert result.telegram_message_id == 102
    assert client.calls[0][0] == "send_photo"
    assert client.calls[0][1]["media"] == "photo-file-id"


@pytest.mark.asyncio
async def test_deliver_video_result_uses_send_video() -> None:
    client = FakeTelegramResultClient()

    result = await deliver_generation_result(
        client,
        command=ResultDeliveryCommand(
            chat_id=123,
            media_kind=TelegramDeliveryMediaKind.VIDEO,
            caption="✅ Видео готово",
            media_url="https://cdn.example.com/video.mp4",
        ),
    )

    assert result.telegram_message_id == 103
    assert client.calls[0][0] == "send_video"
    assert client.calls[0][1]["media"] == "https://cdn.example.com/video.mp4"


@pytest.mark.asyncio
async def test_deliver_document_result_uses_send_document() -> None:
    client = FakeTelegramResultClient()

    result = await deliver_generation_result(
        client,
        command=ResultDeliveryCommand(
            chat_id=123,
            media_kind=TelegramDeliveryMediaKind.DOCUMENT,
            caption="✅ Файл готов",
            media_url="https://cdn.example.com/result.bin",
        ),
    )

    assert result.telegram_message_id == 104
    assert client.calls[0][0] == "send_document"


@pytest.mark.asyncio
async def test_media_delivery_requires_media_reference() -> None:
    client = FakeTelegramResultClient()

    with pytest.raises(ResultDeliveryError, match="media_url or telegram_file_id"):
        await deliver_generation_result(
            client,
            command=ResultDeliveryCommand(
                chat_id=123,
                media_kind=TelegramDeliveryMediaKind.VIDEO,
                caption="✅ Видео готово",
            ),
        )


@pytest.mark.asyncio
async def test_delivery_rejects_empty_caption() -> None:
    client = FakeTelegramResultClient()

    with pytest.raises(ResultDeliveryError, match="cannot be empty"):
        await deliver_generation_result(
            client,
            command=ResultDeliveryCommand(
                chat_id=123,
                media_kind=TelegramDeliveryMediaKind.TEXT,
                caption=" ",
            ),
        )
