from __future__ import annotations

import os
from pathlib import Path

from docreview.core.enums import HandoffAction, HandoffReason, PipelineStage
from docreview.core.schemas import Audit, DocumentMetadata, DocumentReviewPackage, Handoff
from docreview.core.template_loader import get_template, load_templates
from docreview.stages.classify import classify
from docreview.stages.extract import extract
from docreview.stages.ingest import ingest
from docreview.stages.normalize import normalize_llm, normalize_regex
from docreview.stages.render import render
from docreview.stages.validate import validate
from docreview.utils.openai_field_fill import FieldFillError


def _env_or_value(value: str | None, env_key: str, default: str) -> str:
    return value or os.environ.get(env_key, default)


def run_pipeline(
    input_path: Path,
    template_dir: Path,
    created_at: str,
    *,
    fill_mode: str | None = None,
    ocr_model: str | None = None,
    field_model: str | None = None,
) -> DocumentReviewPackage:
    ingest_section, data = ingest(input_path)
    audit: list[Audit] = [
        Audit(stage=PipelineStage.INGEST, event="completed", detail="Ingest completed", created_at=created_at)
    ]
    handoffs = []
    resolved_fill_mode = _env_or_value(fill_mode, "DOCREVIEW_FILL_MODE", "auto").lower()
    resolved_ocr_model = _env_or_value(ocr_model, "DOCREVIEW_OCR_MODEL", "gpt-4o")
    resolved_field_model = field_model or os.environ.get("DOCREVIEW_FIELD_MODEL") or resolved_ocr_model
    api_key = os.environ.get("OPENAI_API_KEY")

    extract_section, extract_handoffs = extract(
        data=data,
        extension=input_path.suffix,
        created_at=created_at,
        api_key=api_key,
        ocr_model=resolved_ocr_model,
    )
    handoffs.extend(extract_handoffs)
    audit.append(
        Audit(stage=PipelineStage.EXTRACT, event="completed", detail="Extraction completed", created_at=created_at)
    )

    templates = load_templates(template_dir)
    classify_section, classify_handoffs = classify(
        extract_section.text,
        created_at=created_at,
        templates=templates,
    )
    handoffs.extend(classify_handoffs)
    audit.append(
        Audit(stage=PipelineStage.CLASSIFY, event="completed", detail="Classification completed", created_at=created_at)
    )

    template = get_template(templates, classify_section.document_type)

    llm_available = bool(api_key)
    if resolved_fill_mode == "regex":
        normalize_section = normalize_regex(extract_section.text, template=template, created_at=created_at)
        audit.append(
            Audit(
                stage=PipelineStage.NORMALIZE,
                event="mode_selected",
                detail="Normalization mode: regex",
                created_at=created_at,
            )
        )
    else:
        try:
            if resolved_fill_mode == "llm" and not llm_available:
                raise FieldFillError("LLM mode requested but OPENAI_API_KEY is missing.")
            if resolved_fill_mode == "auto" and not llm_available:
                raise FieldFillError("LLM unavailable (OPENAI_API_KEY missing); falling back to regex.")
            normalize_section = normalize_llm(
                extract_section.text,
                template=template,
                created_at=created_at,
                api_key=api_key or "",
                model=resolved_field_model,
            )
            audit.append(
                Audit(
                    stage=PipelineStage.NORMALIZE,
                    event="mode_selected",
                    detail=f"Normalization mode: llm ({resolved_field_model})",
                    created_at=created_at,
                )
            )
        except FieldFillError as exc:
            blocking = resolved_fill_mode == "llm"
            handoffs.append(
                Handoff(
                    stage=PipelineStage.NORMALIZE,
                    reason=HandoffReason.INVALID_INPUT,
                    action=HandoffAction.MANUAL_REVIEW,
                    message=f"LLM field fill unavailable: {exc}",
                    created_at=created_at,
                    blocking=blocking,
                )
            )
            normalize_section = normalize_regex(extract_section.text, template=template, created_at=created_at)
            audit.append(
                Audit(
                    stage=PipelineStage.NORMALIZE,
                    event="fallback",
                    detail=f"LLM field fill failed; fallback to regex ({exc})",
                    created_at=created_at,
                )
            )
    audit.append(
        Audit(stage=PipelineStage.NORMALIZE, event="completed", detail="Normalization completed", created_at=created_at)
    )

    validate_section, validate_handoffs = validate(
        normalize_section=normalize_section,
        template=template,
        created_at=created_at,
    )
    handoffs.extend(validate_handoffs)
    audit.append(
        Audit(stage=PipelineStage.VALIDATE, event="completed", detail="Validation completed", created_at=created_at)
    )

    metadata = DocumentMetadata(
        document_id=ingest_section.file_hash[:12],
        source_path=str(input_path),
        file_name=input_path.name,
        file_hash=ingest_section.file_hash,
        file_size_bytes=ingest_section.file_size_bytes,
        extension=input_path.suffix.lower(),
        created_at=created_at,
    )

    package = DocumentReviewPackage(
        metadata=metadata,
        ingest=ingest_section,
        extract=extract_section,
        classify=classify_section,
        normalize=normalize_section,
        validate_section=validate_section,
        render={"ok": True, "markdown_summary": ""},
        handoffs=handoffs,
        audit=audit,
    )
    package.render = render(package)
    package.audit.append(
        Audit(stage=PipelineStage.RENDER, event="completed", detail="Render completed", created_at=created_at)
    )
    return package
