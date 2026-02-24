from __future__ import annotations

from pydantic import BaseModel, Field

from docreview.core.enums import PipelineStage
from docreview.core.schemas import (
    Audit,
    DocumentReviewPackage,
    FieldProposal,
    append_field_proposal,
)


class FieldUpdate(BaseModel):
    field_name: str
    value: str | int | float | bool | None
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = "agent_review"
    notes: str | None = None


class HandoffResolution(BaseModel):
    index: int
    resolution: str
    resolved_by: str = "agent_review"


class PatchPayload(BaseModel):
    field_updates: list[FieldUpdate] = Field(default_factory=list)
    handoff_resolutions: list[HandoffResolution] = Field(default_factory=list)


def apply_patch(
    package: DocumentReviewPackage,
    patch: PatchPayload,
    created_at: str,
) -> DocumentReviewPackage:
    updated = package.model_copy(deep=True)
    fields = updated.normalize.fields

    for field_update in patch.field_updates:
        proposal = FieldProposal(
            source=field_update.source,
            value=field_update.value,
            confidence=field_update.confidence,
            stage=PipelineStage.NORMALIZE,
            created_at=created_at,
            notes=field_update.notes,
        )
        fields = append_field_proposal(fields, field_update.field_name, proposal)
        updated.audit.append(
            Audit(
                stage=PipelineStage.NORMALIZE,
                event="patched_field",
                detail=f"Appended proposal for '{field_update.field_name}'.",
                created_at=created_at,
            )
        )
    updated.normalize.fields = fields

    for resolution in patch.handoff_resolutions:
        if 0 <= resolution.index < len(updated.handoffs):
            handoff = updated.handoffs[resolution.index]
            handoff.resolved = True
            handoff.resolved_at = created_at
            handoff.resolution = resolution.resolution
            handoff.resolved_by = resolution.resolved_by
            updated.audit.append(
                Audit(
                    stage=PipelineStage.VALIDATE,
                    event="resolved_handoff",
                    detail=f"Resolved handoff index {resolution.index}.",
                    created_at=created_at,
                )
            )

    return updated
