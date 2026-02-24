from __future__ import annotations

from docreview.core.enums import (
    FieldStatus,
    HandoffAction,
    HandoffReason,
    PipelineStage,
)
from docreview.core.schemas import Handoff, NormalizeSection, ValidateSection
from docreview.core.template_loader import DocumentTemplate


def validate(
    normalize_section: NormalizeSection,
    template: DocumentTemplate,
    created_at: str,
) -> tuple[ValidateSection, list[Handoff]]:
    statuses: dict[str, FieldStatus] = {}
    missing: list[str] = []
    handoffs: list[Handoff] = []

    for field in template.fields:
        proposals = normalize_section.fields.get(field.name, [])
        if proposals:
            statuses[field.name] = FieldStatus.VALID
            continue
        if field.required:
            statuses[field.name] = FieldStatus.MISSING
            missing.append(field.name)
            handoffs.append(
                Handoff(
                    stage=PipelineStage.VALIDATE,
                    reason=HandoffReason.MISSING_REQUIRED_FIELD,
                    action=HandoffAction.PROVIDE_MISSING_INFORMATION,
                    message=f"Required field '{field.name}' is missing.",
                    field_name=field.name,
                    created_at=created_at,
                )
            )
        else:
            statuses[field.name] = FieldStatus.PROPOSED

    section = ValidateSection(
        ok=len(missing) == 0,
        field_status=statuses,
        missing_required_fields=missing,
    )
    return section, handoffs
