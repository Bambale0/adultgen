"""ORM models registry.

Importing this package loads all model modules so Alembic can see metadata.
"""

from adultgen.db.models.audit import AdminAuditEvent
from adultgen.db.models.broadcasts import Broadcast, BroadcastRecipient
from adultgen.db.models.generations import GenerationTask, SceneTake
from adultgen.db.models.media import MediaAsset, MediaDerivative
from adultgen.db.models.moderation import ModerationCase
from adultgen.db.models.notifications import NotificationDelivery
from adultgen.db.models.payments import PaymentOrder, PaymentWebhookProcessing, PaymentWebhookRaw
from adultgen.db.models.projects import (
    AvatarProfile,
    AvatarReference,
    Project,
    Scene,
    SceneReference,
)
from adultgen.db.models.publications import (
    FeedEvent,
    Publication,
    PublicationLike,
    RemixSource,
    SavedPublication,
    UserProfile,
)
from adultgen.db.models.referrals import (
    PartnerCommission,
    PartnerPayoutRequest,
    PartnerWallet,
    ReferralRelation,
)
from adultgen.db.models.users import AdultConsent, TelegramChannel, User, UserChannelActivity
from adultgen.db.models.wallets import Wallet, WalletEntry

__all__ = [
    "AdminAuditEvent",
    "AdultConsent",
    "AvatarProfile",
    "AvatarReference",
    "Broadcast",
    "BroadcastRecipient",
    "FeedEvent",
    "GenerationTask",
    "MediaAsset",
    "MediaDerivative",
    "ModerationCase",
    "NotificationDelivery",
    "PartnerCommission",
    "PartnerPayoutRequest",
    "PartnerWallet",
    "PaymentOrder",
    "PaymentWebhookProcessing",
    "PaymentWebhookRaw",
    "Project",
    "Publication",
    "PublicationLike",
    "ReferralRelation",
    "RemixSource",
    "SavedPublication",
    "Scene",
    "SceneReference",
    "SceneTake",
    "TelegramChannel",
    "User",
    "UserChannelActivity",
    "UserProfile",
    "Wallet",
    "WalletEntry",
]
