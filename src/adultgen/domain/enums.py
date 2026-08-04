"""Shared domain enums for the first MVP implementation."""

from enum import StrEnum


class TelegramChannelStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class WalletEntryType(StrEnum):
    PAYMENT_CREDIT = "payment_credit"
    SUBSCRIPTION_CREDIT = "subscription_credit"
    BONUS_CREDIT = "bonus_credit"
    GENERATION_RESERVE = "generation_reserve"
    GENERATION_CHARGE = "generation_charge"
    GENERATION_RELEASE = "generation_release"
    REFUND = "refund"
    ADMIN_ADJUSTMENT = "admin_adjustment"
    CHARGEBACK = "chargeback"


class CreditBucket(StrEnum):
    PURCHASED = "purchased"
    SUBSCRIPTION = "subscription"
    BONUS = "bonus"


class PaymentProviderCode(StrEnum):
    SHARPAY = "sharpay"
    CROCOPAY = "crocopay"


class PaymentOrderStatus(StrEnum):
    CREATED = "created"
    REDIRECTED = "redirected"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"
    CHARGEBACK = "chargeback"
    CANCELLED = "cancelled"


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    DELETED = "deleted"


class GenerationStatus(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    SUBMITTED = "submitted"
    PROVIDER_PROCESSING = "provider_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class GenerationOperation(StrEnum):
    IMAGE_TEXT_TO_IMAGE = "image_text_to_image"
    IMAGE_TO_IMAGE = "image_to_image"
    VIDEO_TEXT_TO_VIDEO = "video_text_to_video"
    VIDEO_IMAGE_TO_VIDEO_FIRST_FRAME = "video_image_to_video_first_frame"
    VIDEO_IMAGE_TO_VIDEO_FIRST_LAST_FRAMES = "video_image_to_video_first_last_frames"
    VIDEO_MULTIMODAL_REFERENCE_TO_VIDEO = "video_multimodal_reference_to_video"


class ModelProvider(StrEnum):
    KIE = "kie"


class ModelCode(StrEnum):
    SEEDREAM_5_PRO_TEXT_TO_IMAGE = "seedream-5-pro-text-to-image"
    SEEDREAM_5_PRO_IMAGE_TO_IMAGE = "seedream-5-pro-image-to-image"
    SEEDANCE_2 = "seedance-2.0"


class KieProviderModel(StrEnum):
    SEEDREAM_5_PRO_TEXT_TO_IMAGE = "seedream/5-pro-text-to-image"
    SEEDREAM_5_PRO_IMAGE_TO_IMAGE = "seedream/5-pro-image-to-image"
    SEEDANCE_2 = "bytedance/seedance-2"


class BillingUnit(StrEnum):
    GENERATION = "generation"
    SECOND = "second"


class ReferenceRole(StrEnum):
    AVATAR_IDENTITY = "avatar_identity"
    MAIN_FRAME = "main_frame"
    LOCATION = "location"
    VISUAL_STYLE = "visual_style"
    LIGHTING = "lighting"
    COMPOSITION = "composition"
    CAMERA_MOTION = "camera_motion"
    SUBJECT_MOTION = "subject_motion"
    AUDIO_ATMOSPHERE = "audio_atmosphere"
    VOICE = "voice"
    MUSIC = "music"
    FIRST_FRAME = "first_frame"
    LAST_FRAME = "last_frame"
    EXTRA = "extra"


class PublicationVisibility(StrEnum):
    PROFILE = "profile"
    FEED = "feed"


class PublicationStatus(StrEnum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    DELETED = "deleted"
    MODERATION_HOLD = "moderation_hold"


class FeedEventType(StrEnum):
    IMPRESSION = "impression"
    REVEAL_BLUR = "reveal_blur"
    VIEW_COMPLETE = "view_complete"
    SKIP = "skip"
    REMIX_CLICK = "remix_click"


class ModerationCategory(StrEnum):
    MINOR_OR_YOUNG_LOOKING = "minor_or_young_looking"
    NON_CONSENSUAL_IDENTITY = "non_consensual_identity"
    PUBLIC_FIGURE = "public_figure"
    PROHIBITED_CONTENT = "prohibited_content"
    VIOLENCE_OR_COERCION = "violence_or_coercion"
    SPAM = "spam"
    WRONG_18_MARKING = "wrong_18_marking"
    COPYRIGHT = "copyright"
    OTHER = "other"


class PartnerPayoutStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    PAID = "paid"
    CANCELLED = "cancelled"


class NotificationDeliveryStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    RETRY_SCHEDULED = "retry_scheduled"
    FAILED = "failed"
