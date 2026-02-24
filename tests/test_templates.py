from docreview.core.template_loader import get_template, load_templates
from docreview.utils.md_generator import template_to_markdown


def test_templates_load(template_dir) -> None:
    templates = load_templates(template_dir)
    assert "paystub" in templates
    assert "t4" in templates
    assert "notice_of_assessment" in templates
    assert "bank_statement" in templates
    assert "government_id" in templates


def test_required_fields_exist(template_dir) -> None:
    templates = load_templates(template_dir)
    paystub = templates["paystub"]
    required = [f.name for f in paystub.fields if f.required]
    assert "employee_name" in required
    assert "employer_name" in required
    assert "net_pay" in required


def test_unknown_fallback_works(template_dir) -> None:
    templates = load_templates(template_dir)
    unknown = get_template(templates, "unknown")
    assert unknown.doc_type == "unknown"
    assert unknown.fields == []


def test_markdown_generation(template_dir) -> None:
    templates = load_templates(template_dir)
    md = template_to_markdown(templates["paystub"])
    assert "# Paystub" in md
    assert "employee_name" in md
