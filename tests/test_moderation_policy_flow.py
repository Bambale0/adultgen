from pathlib import Path

from adultgen.domain.adult_policy import (
    AdultPolicyAction,
    AdultPolicyFlag,
    AdultPolicyInput,
    evaluate_adult_policy,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_adult_policy_blocks_minors_and_coercion() -> None:
    minor = evaluate_adult_policy(
        AdultPolicyInput(text="explicit teen schoolgirl scene", surface="generation_submit")
    )
    coercion = evaluate_adult_policy(
        AdultPolicyInput(text="forced sexual violence scene", surface="generation_submit")
    )

    assert minor.action == AdultPolicyAction.BLOCK
    assert AdultPolicyFlag.MINOR_OR_UNDERAGE in minor.flags
    assert minor.public_allowed is False
    assert coercion.action == AdultPolicyAction.BLOCK
    assert AdultPolicyFlag.COERCION_OR_VIOLENCE in coercion.flags


def test_adult_policy_reviews_real_person_or_public_figure() -> None:
    real_person = evaluate_adult_policy(
        AdultPolicyInput(
            text="adult consensual style reference",
            surface="generation_submit",
            has_real_person_reference=True,
            has_identity_consent=False,
        )
    )
    public_figure = evaluate_adult_policy(
        AdultPolicyInput(text="celebrity lookalike adult prompt", surface="generation_submit")
    )

    assert real_person.action == AdultPolicyAction.BLOCK
    assert AdultPolicyFlag.NCII_OR_REAL_PERSON in real_person.flags
    assert public_figure.action == AdultPolicyAction.REVIEW
    assert AdultPolicyFlag.PUBLIC_FIGURE in public_figure.flags


def test_generation_and_publication_routes_use_policy_checks() -> None:
    generations = read("src/adultgen/api/routers/generations.py")
    publications = read("src/adultgen/api/routers/publications.py")

    assert "evaluate_request_payload" in generations
    assert "AdultPolicyAction.BLOCK" in generations
    assert "create_policy_moderation_case" in generations
    assert "await session.commit()" in generations
    assert "evaluate_request_payload" in publications
    assert "blur_required = payload.blur_required or payload.is_explicit or policy_decision.needs_review" in publications
    assert "publication_id=publication.id" in publications


def test_moderation_routes_are_registered() -> None:
    core_api = read("src/adultgen/apps/core_api.py")
    moderation_router = read("src/adultgen/api/routers/moderation.py")

    assert "moderation," in core_api
    assert "app.include_router(moderation.router)" in core_api
    assert '"/publications/{publication_id}/reports"' in moderation_router
    assert '"/admin/moderation/cases"' in moderation_router
    assert '"/admin/moderation/cases/{case_id}/resolve"' in moderation_router
    assert "require_admin_api_token" in moderation_router


def test_moderation_service_prioritizes_and_hides_publications() -> None:
    service = read("src/adultgen/services/moderation.py")

    assert '"minor_or_underage": 100' in service
    assert '"ncii_or_real_person": 90' in service
    assert '"hide_publication"' in service
    assert "PublicationStatus.HIDDEN.value" in service
    assert "list_open_moderation_cases" in service


def test_web_client_exposes_report_and_admin_moderation_methods() -> None:
    api = read("apps/web_app/src/api.ts")

    assert "type ModerationCase" in api
    assert "reportPublication" in api
    assert "fetchAdminModerationCases" in api
    assert "resolveAdminModerationCase" in api
    assert "`/publications/${publicationId}/reports`" in api
    assert "'/admin/moderation/cases?limit=" not in api
    assert "`/admin/moderation/cases?limit=${limit}`" in api
