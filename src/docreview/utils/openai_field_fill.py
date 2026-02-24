from __future__ import annotations

import json

from pydantic import BaseModel, Field

from docreview.core.template_loader import DocumentTemplate


class FieldFillError(RuntimeError):
    """Raised when LLM field fill cannot complete safely."""


class FieldFillItem(BaseModel):
    field_name: str
    value: str | int | float | bool | None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None = None
    notes: str | None = None


class FieldFillResponse(BaseModel):
    field_values: list[FieldFillItem] = Field(default_factory=list)


def _template_payload(template: DocumentTemplate) -> list[dict[str, object]]:
    return [
        {
            "name": field.name,
            "type": field.type,
            "required": field.required,
            "synonyms": field.synonyms,
        }
        for field in template.fields
    ]


def openai_field_fill(
    *,
    text: str,
    template: DocumentTemplate,
    api_key: str,
    model: str,
) -> list[FieldFillItem]:
    if not api_key:
        raise FieldFillError("OPENAI_API_KEY is missing.")
    if not template.fields:
        return []

    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise FieldFillError("openai package not installed; install with `.[ocr]`") from exc

    client = OpenAI(api_key=api_key)
    prompt = (
        "You are a deterministic information extraction system.\n"
        "Extract values for the provided template fields from DOCUMENT_TEXT.\n"
        "Rules:\n"
        "- Use only explicit information in DOCUMENT_TEXT.\n"
        "- If a field value is not present, set value to null.\n"
        "- Do not infer or fabricate missing values.\n"
        "- Confidence must be between 0 and 1.\n"
        "- Provide a short evidence quote when available.\n"
        "- Return JSON only matching the requested shape.\n"
    )

    content = [
        {"type": "input_text", "text": prompt},
        {"type": "input_text", "text": f"TEMPLATE_FIELDS:\n{json.dumps(_template_payload(template), ensure_ascii=True)}"},
        {"type": "input_text", "text": f"DOCUMENT_TEXT:\n{text}"},
        {
            "type": "input_text",
            "text": (
                "Return exactly this JSON shape:\n"
                '{"field_values":[{"field_name":"...", "value":null, "confidence":0.0, "evidence":null, "notes":null}]}\n'
            ),
        },
    ]

    try:
        response = client.responses.create(
            model=model,
            input=[{"role": "user", "content": content}],
            temperature=0,
            text={"format": {"type": "json_object"}},
        )
        raw = response.output_text.strip()
        if not raw:
            raise FieldFillError("LLM returned empty output for field extraction.")
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        payload = json.loads(raw)
        parsed = FieldFillResponse.model_validate(payload)
    except FieldFillError:
        raise
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        raise FieldFillError(f"LLM field extraction failed: {exc}") from exc

    allowed = {field.name for field in template.fields}
    return [item for item in parsed.field_values if item.field_name in allowed]
