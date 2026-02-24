import pytest
from pydantic import ValidationError

from docreview.core.enums import (
    FieldStatus,
    HandoffAction,
    HandoffReason,
    PipelineStage,
)
from docreview.core.schemas import (
    Audit,
    ClassifySection,
    DocumentMetadata,
    DocumentReviewPackage,
    ExtractSection,
    FieldProposal,
    Handoff,
    IngestSection,
    NormalizeSection,
    RenderSection,
    ValidateSection,
    append_field_proposal,
)


def _proposal() -> FieldProposal:
    return FieldProposal(
        source="unit_test",
        value="Jane Doe",
        confidence=0.9,
        stage=PipelineStage.NORMALIZE,
        created_at="1970-01-01T00:00:00Z",
    )


def test_schema_validity() -> None:
    metadata = DocumentMetadata(
        document_id="abc123",
        source_path="C:/tmp/doc.txt",
        file_name="doc.txt",
        file_hash="f" * 64,
        file_size_bytes=10,
        extension=".txt",
        created_at="1970-01-01T00:00:00Z",
    )
    package = DocumentReviewPackage(
        metadata=metadata,
        ingest=IngestSection(
            ok=True,
            source_path="C:/tmp/doc.txt",
            file_hash="f" * 64,
            file_size_bytes=10,
            mime_type="text/plain",
        ),
        extract=ExtractSection(
            ok=True,
            text="sample",
            used_ocr_stub=False,
            method="text_layer",
        ),
        classify=ClassifySection(ok=True, document_type="paystub", confidence=0.9),
        normalize=NormalizeSection(ok=True, fields={"employee_name": [_proposal()]}),
        validate_section=ValidateSection(
            ok=True,
            field_status={"employee_name": FieldStatus.VALID},
            missing_required_fields=[],
        ),
        render=RenderSection(ok=True, markdown_summary="summary"),
        handoffs=[
            Handoff(
                stage=PipelineStage.CLASSIFY,
                reason=HandoffReason.LOW_CONFIDENCE,
                action=HandoffAction.MANUAL_REVIEW,
                message="test",
                created_at="1970-01-01T00:00:00Z",
                blocking=False,
                resolved=False,
            )
        ],
        audit=[
            Audit(
                stage=PipelineStage.INGEST,
                event="completed",
                detail="ok",
                created_at="1970-01-01T00:00:00Z",
            )
        ],
    )
    assert package.metadata.file_name == "doc.txt"


def test_required_fields_enforced() -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata(
            document_id="abc123",
            source_path="C:/tmp/doc.txt",
            file_name="doc.txt",
            file_size_bytes=10,
            extension=".txt",
            created_at="1970-01-01T00:00:00Z",
        )


def test_original_proposals_are_immutable() -> None:
    proposal = _proposal()
    with pytest.raises(ValidationError):
        proposal.value = "Changed"


def test_append_only_field_history() -> None:
    first = _proposal()
    initial = {"employee_name": [first]}
    second = FieldProposal(
        source="unit_test",
        value="Jane A. Doe",
        confidence=0.8,
        stage=PipelineStage.NORMALIZE,
        created_at="1970-01-01T00:00:00Z",
    )
    updated = append_field_proposal(initial, "employee_name", second)
    assert len(initial["employee_name"]) == 1
    assert len(updated["employee_name"]) == 2
    assert updated["employee_name"][0].value == "Jane Doe"
