from __future__ import annotations

from docreview.core.enums import DocumentType, HandoffAction, HandoffReason, PipelineStage
from docreview.core.schemas import ClassifySection, Handoff
from docreview.core.template_loader import DocumentTemplate


DOC_TYPE_KEYWORDS: dict[str, set[str]] = {
    DocumentType.PAYSTUB.value: {"paystub", "gross pay", "net pay", "pay period"},
    DocumentType.T4.value: {"t4", "statement of remuneration paid"},
    DocumentType.NOTICE_OF_ASSESSMENT.value: {"notice of assessment", "tax year"},
    DocumentType.BANK_STATEMENT.value: {"bank statement", "account number", "opening balance"},
    DocumentType.GOVERNMENT_ID.value: {"driver", "passport", "issued"},
}


def _build_keyword_map(templates: dict[str, DocumentTemplate]) -> dict[str, set[str]]:
    keyword_map: dict[str, set[str]] = {
        key: set(value) for key, value in DOC_TYPE_KEYWORDS.items()
    }
    for doc_type, template in templates.items():
        key = doc_type.lower()
        keyword_map.setdefault(key, set())
        keyword_map[key].add(key.replace("_", " "))
        keyword_map[key].add(template.display_name.lower())
        for field in template.fields:
            keyword_map[key].add(field.name.lower().replace("_", " "))
            for synonym in field.synonyms:
                keyword_map[key].add(synonym.lower())
    return keyword_map


def classify(
    text: str,
    created_at: str,
    templates: dict[str, DocumentTemplate],
) -> tuple[ClassifySection, list[Handoff]]:
    lower_text = text.lower()
    keyword_map = _build_keyword_map(templates)
    scores: dict[str, float] = {}
    for doc_type, keywords in keyword_map.items():
        hits = sum(1 for keyword in keywords if keyword in lower_text)
        scores[doc_type] = hits / max(len(keywords), 1)

    best_doc_type = max(scores, key=scores.get) if scores else DocumentType.UNKNOWN.value
    best_score = scores.get(best_doc_type, 0.0)
    handoffs: list[Handoff] = []

    if best_score < 0.34:
        best_doc_type = DocumentType.UNKNOWN.value
        handoffs.append(
            Handoff(
                stage=PipelineStage.CLASSIFY,
                reason=HandoffReason.UNKNOWN_DOCUMENT_TYPE,
                action=HandoffAction.MANUAL_REVIEW,
                message="Unable to classify document with sufficient confidence.",
                created_at=created_at,
                blocking=best_score < 0.1,
            )
        )
    elif best_score < 0.67:
        handoffs.append(
            Handoff(
                stage=PipelineStage.CLASSIFY,
                reason=HandoffReason.LOW_CONFIDENCE,
                action=HandoffAction.MANUAL_REVIEW,
                message=f"Classification confidence is low ({best_score:.2f}).",
                created_at=created_at,
            )
        )

    section = ClassifySection(ok=True, document_type=best_doc_type, confidence=best_score)
    return section, handoffs
