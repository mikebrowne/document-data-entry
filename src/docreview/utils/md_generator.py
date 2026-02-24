from __future__ import annotations

from docreview.core.template_loader import DocumentTemplate


def template_to_markdown(template: DocumentTemplate) -> str:
    lines = [
        f"# {template.display_name}",
        "",
        f"- Doc Type: `{template.doc_type}`",
        f"- Version: `{template.version}`",
        "",
        "## Fields",
    ]
    if not template.fields:
        lines.append("- No fields defined.")
        return "\n".join(lines)
    for field in template.fields:
        req = "required" if field.required else "optional"
        synonyms = ", ".join(field.synonyms) if field.synonyms else "(none)"
        lines.append(
            f"- `{field.name}` ({field.type}, {req}) | synonyms: {synonyms}"
        )
    return "\n".join(lines)
