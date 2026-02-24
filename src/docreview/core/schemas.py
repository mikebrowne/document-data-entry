from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from docreview.core.enums import (
    FieldStatus,
    HandoffAction,
    HandoffReason,
    PipelineStage,
)


class FieldProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    value: str | int | float | bool | None
    confidence: float = Field(ge=0.0, le=1.0)
    stage: PipelineStage
    created_at: str
    notes: str | None = None


class Handoff(BaseModel):
    stage: PipelineStage
    reason: HandoffReason
    action: HandoffAction
    message: str
    field_name: str | None = None
    created_at: str
    blocking: bool = False
    resolved: bool = False
    resolved_at: str | None = None
    resolution: str | None = None
    resolved_by: str | None = None


class Audit(BaseModel):
    stage: PipelineStage
    event: str
    detail: str
    created_at: str


class DocumentMetadata(BaseModel):
    document_id: str
    source_path: str
    file_name: str
    file_hash: str
    file_size_bytes: int = Field(ge=0)
    extension: str
    created_at: str


class IngestSection(BaseModel):
    stage: PipelineStage = PipelineStage.INGEST
    ok: bool
    source_path: str
    file_hash: str
    file_size_bytes: int = Field(ge=0)
    mime_type: str


class ExtractSection(BaseModel):
    stage: PipelineStage = PipelineStage.EXTRACT
    ok: bool
    text: str
    used_ocr_stub: bool
    method: str = "stub"
    model: str | None = None
    page_count: int | None = None


class ClassifySection(BaseModel):
    stage: PipelineStage = PipelineStage.CLASSIFY
    ok: bool
    document_type: str
    confidence: float = Field(ge=0.0, le=1.0)


class NormalizeSection(BaseModel):
    stage: PipelineStage = PipelineStage.NORMALIZE
    ok: bool
    fields: dict[str, list[FieldProposal]]


class ValidateSection(BaseModel):
    stage: PipelineStage = PipelineStage.VALIDATE
    ok: bool
    field_status: dict[str, FieldStatus]
    missing_required_fields: list[str]


class RenderSection(BaseModel):
    stage: PipelineStage = PipelineStage.RENDER
    ok: bool
    markdown_summary: str


class DocumentReviewPackage(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_inf_nan="null")

    schema_version: str = "1.0.0"
    metadata: DocumentMetadata
    ingest: IngestSection
    extract: ExtractSection
    classify: ClassifySection
    normalize: NormalizeSection
    validate_section: ValidateSection = Field(alias="validate")
    render: RenderSection
    handoffs: list[Handoff] = Field(default_factory=list)
    audit: list[Audit] = Field(default_factory=list)


def append_field_proposal(
    fields: dict[str, list[FieldProposal]], field_name: str, proposal: FieldProposal
) -> dict[str, list[FieldProposal]]:
    """Return a new fields mapping with proposal appended to field history."""
    next_fields: dict[str, list[FieldProposal]] = {
        key: list(value) for key, value in fields.items()
    }
    next_fields.setdefault(field_name, [])
    next_fields[field_name].append(proposal)
    return next_fields
