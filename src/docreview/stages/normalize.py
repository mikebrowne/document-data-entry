from __future__ import annotations

import re

from docreview.core.enums import PipelineStage
from docreview.core.schemas import FieldProposal, NormalizeSection, append_field_proposal
from docreview.core.template_loader import DocumentTemplate


def normalize(
    text: str,
    template: DocumentTemplate,
    created_at: str,
) -> NormalizeSection:
    fields: dict[str, list[FieldProposal]] = {}
    lines = text.splitlines()

    for field in template.fields:
        candidates = [field.name] + field.synonyms
        found_value = None
        confidence = 0.0
        for line in lines:
            lowered = line.lower()
            for candidate in candidates:
                pattern = rf"\b{re.escape(candidate.lower())}\b\s*[:=-]\s*(.+)$"
                match = re.search(pattern, lowered)
                if match:
                    raw_match = re.search(
                        rf"\b{re.escape(candidate)}\b\s*[:=-]\s*(.+)$",
                        line,
                        flags=re.IGNORECASE,
                    )
                    found_value = raw_match.group(1).strip() if raw_match else match.group(1).strip()
                    confidence = 0.9 if candidate == field.name else 0.75
                    break
            if found_value is not None:
                break

        if found_value is not None:
            proposal = FieldProposal(
                source="extract_text",
                value=found_value,
                confidence=confidence,
                stage=PipelineStage.NORMALIZE,
                created_at=created_at,
            )
            fields = append_field_proposal(fields, field.name, proposal)

    return NormalizeSection(ok=True, fields=fields)
