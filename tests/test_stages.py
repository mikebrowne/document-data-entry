from pathlib import Path

from docreview.core.template_loader import get_template, load_templates
from docreview.stages.classify import classify
from docreview.stages.extract import extract
from docreview.stages.ingest import ingest
from docreview.stages.normalize import normalize
from docreview.stages.pipeline import run_pipeline
from docreview.stages.validate import validate


def test_stage_structure(template_dir, created_at) -> None:
    fixture = Path(__file__).parent / "fixtures" / "paystub_sample.txt"
    templates = load_templates(template_dir)
    ingest_section, data = ingest(fixture)
    extract_section, extract_handoffs = extract(data, fixture.suffix, created_at)
    classify_section, classify_handoffs = classify(extract_section.text, created_at, templates)
    template = get_template(templates, classify_section.document_type)
    normalize_section = normalize(extract_section.text, template, created_at)
    validate_section, validate_handoffs = validate(normalize_section, template, created_at)

    assert ingest_section.ok
    assert extract_section.ok
    assert classify_section.ok
    assert normalize_section.ok
    assert validate_section.ok
    assert isinstance(extract_handoffs, list)
    assert isinstance(classify_handoffs, list)
    assert isinstance(validate_handoffs, list)


def test_handoff_creation_on_unknown(created_at, template_dir) -> None:
    text = "Totally ambiguous content with no doc signals."
    templates = load_templates(template_dir)
    section, handoffs = classify(text, created_at, templates)
    assert section.document_type == "unknown"
    assert len(handoffs) >= 1
    assert handoffs[0].blocking


def test_status_transitions(template_dir, created_at) -> None:
    fixture = Path(__file__).parent / "fixtures" / "paystub_sample.txt"
    package = run_pipeline(fixture, template_dir=template_dir, created_at=created_at)
    assert package.ingest.stage.value == "ingest"
    assert package.extract.stage.value == "extract"
    assert package.classify.stage.value == "classify"
    assert package.normalize.stage.value == "normalize"
    assert package.validate_section.stage.value == "validate"
    assert package.render.stage.value == "render"
    assert len(package.audit) >= 6


def test_extract_pdf_without_ocr_key_falls_back_to_stub(created_at) -> None:
    section, handoffs = extract(b"%PDF-1.4 fake", ".pdf", created_at, api_key=None)
    assert section.method == "stub"
    assert section.used_ocr_stub is True
    assert handoffs


def test_extract_text_uses_text_layer(created_at) -> None:
    section, handoffs = extract(b"employee_name: Jane Doe", ".txt", created_at, api_key=None)
    assert section.method == "text_layer"
    assert section.used_ocr_stub is False
    assert handoffs == []


def test_extract_pdf_page_limit_handoff(created_at) -> None:
    fake_pdf = b"%PDF-1.4 " + (b"/Type /Page " * 30)
    section, handoffs = extract(fake_pdf, ".pdf", created_at, api_key=None)
    assert section.ok is False
    assert handoffs
    assert handoffs[0].reason.value == "page_limit_exceeded"
    assert handoffs[0].blocking is True
