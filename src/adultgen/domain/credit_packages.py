"""Credit package catalog for website checkout."""

from __future__ import annotations

from dataclasses import dataclass


class CreditPackageError(ValueError):
    """Raised when a credit package is invalid or unavailable."""


@dataclass(frozen=True, slots=True)
class CreditPackage:
    """A purchasable credit bundle shown in website billing UI."""

    code: str
    title: str
    credits: int
    amount_minor: int
    currency: str = "RUB"
    description: str = ""
    is_popular: bool = False

    @property
    def amount_major(self) -> str:
        """Return major currency amount as a fixed two-decimal string."""

        return f"{self.amount_minor / 100:.2f}"


CREDIT_PACKAGES: tuple[CreditPackage, ...] = (
    CreditPackage(
        code="starter_500",
        title="Starter",
        credits=500,
        amount_minor=99000,
        description="Первые тесты фото/видео генерации.",
    ),
    CreditPackage(
        code="creator_1500",
        title="Creator",
        credits=1_500,
        amount_minor=249000,
        description="Оптимальный пакет для регулярной генерации.",
        is_popular=True,
    ),
    CreditPackage(
        code="studio_5000",
        title="Studio",
        credits=5_000,
        amount_minor=699000,
        description="Запас кредитов для активной работы с видео.",
    ),
)

_PACKAGES_BY_CODE = {package.code: package for package in CREDIT_PACKAGES}


def list_credit_packages() -> tuple[CreditPackage, ...]:
    """Return enabled credit packages in display order."""

    return CREDIT_PACKAGES


def get_credit_package(code: str) -> CreditPackage:
    """Return a credit package by code or raise a domain error."""

    try:
        return _PACKAGES_BY_CODE[code]
    except KeyError as exc:
        raise CreditPackageError("Unknown credit package.") from exc
