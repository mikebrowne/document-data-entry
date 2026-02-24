from __future__ import annotations

from docreview.core.schemas import DocumentReviewPackage, RenderSection


def render(package: DocumentReviewPackage) -> RenderSection:
    lines = [
        f"# Document Review: {package.metadata.file_name}",
        "",
        f"- Document Type: `{package.classify.document_type}`",
        f"- Classification Confidence: `{package.classify.confidence:.2f}`",
        f"- Validation OK: `{package.validate_section.ok}`",
        f"- Handoff Count: `{len(package.handoffs)}`",
        "",
        "## Field Status",
    ]
    for field_name, status in sorted(package.validate_section.field_status.items()):
        lines.append(f"- `{field_name}`: {status.value}")

    if package.handoffs:
        lines.append("")
        lines.append("## Handoffs")
        for handoff in package.handoffs:
            lines.append(f"- [{handoff.stage.value}] {handoff.reason.value}: {handoff.message}")

    return RenderSection(ok=True, markdown_summary="\n".join(lines))
