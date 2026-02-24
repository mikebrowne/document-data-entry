from __future__ import annotations

import os
from pathlib import Path

from docreview.core.enums import PipelineStage
from docreview.core.schemas import Audit, DocumentMetadata, DocumentReviewPackage
from docreview.core.template_loader import get_template, load_templates
from docreview.stages.classify import classify
from docreview.stages.extract import extract
from docreview.stages.ingest import ingest
from docreview.stages.normalize import normalize
from docreview.stages.render import render
from docreview.stages.validate import validate


def run_pipeline(input_path: Path, template_dir: Path, created_at: str) -> DocumentReviewPackage:
    ingest_section, data = ingest(input_path)
    audit: list[Audit] = [
        Audit(stage=PipelineStage.INGEST, event="completed", detail="Ingest completed", created_at=created_at)
    ]
    handoffs = []

    extract_section, extract_handoffs = extract(
        data=data,
        extension=input_path.suffix,
        created_at=created_at,
        api_key=os.environ.get("OPENAI_API_KEY"),
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

    normalize_section = normalize(extract_section.text, template=template, created_at=created_at)
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
