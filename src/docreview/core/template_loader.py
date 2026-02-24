from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

class TemplateField(BaseModel):
    name: str
    type: str
    required: bool = False
    synonyms: list[str] = Field(default_factory=list)


class DocumentTemplate(BaseModel):
    doc_type: str
    display_name: str
    version: str
    fields: list[TemplateField]


def unknown_template() -> DocumentTemplate:
    return DocumentTemplate(
        doc_type="unknown",
        display_name="Unknown Document",
        version="1.0",
        fields=[],
    )


def load_template(path: Path) -> DocumentTemplate:
    data = json.loads(path.read_text(encoding="utf-8"))
    return DocumentTemplate.model_validate(data)


def load_templates(template_dir: Path) -> dict[str, DocumentTemplate]:
    templates: dict[str, DocumentTemplate] = {}
    for path in sorted(template_dir.glob("*.json"), key=lambda p: p.name):
        template = load_template(path)
        templates[template.doc_type.lower()] = template
    templates["unknown"] = unknown_template()
    return templates


def get_template(
    templates: dict[str, DocumentTemplate], doc_type: str
) -> DocumentTemplate:
    return templates.get(doc_type.lower(), templates["unknown"])
