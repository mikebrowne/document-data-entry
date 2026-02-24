from __future__ import annotations

from docreview.core.enums import HandoffAction, HandoffReason, PipelineStage
from docreview.core.schemas import ExtractSection, Handoff
from docreview.utils.openai_extract import openai_vision_extract
from docreview.utils.pdf_extract import extract_text_layer, pdf_to_images

PAGE_LIMIT = 25


def extract(
    data: bytes,
    extension: str,
    created_at: str,
    api_key: str | None = None,
) -> tuple[ExtractSection, list[Handoff]]:
    handoffs: list[Handoff] = []
    ext = extension.lower()
    if len(data) == 0:
        handoffs.append(
            Handoff(
                stage=PipelineStage.EXTRACT,
                reason=HandoffReason.UNREADABLE_INPUT,
                action=HandoffAction.FIX_INPUT,
                message="Input file is empty or unreadable.",
                created_at=created_at,
                blocking=True,
            )
        )
        return (
            ExtractSection(
                ok=False,
                text="",
                used_ocr_stub=True,
                method="stub",
            ),
            handoffs,
        )

    if ext in {".txt", ".md", ".json", ".csv"}:
        return (
            ExtractSection(
                ok=True,
                text=data.decode("utf-8", errors="replace"),
                used_ocr_stub=False,
                method="text_layer",
            ),
            handoffs,
        )

    if ext == ".pdf":
        page_count = data.count(b"/Type /Page") or None
        if page_count is not None and page_count > PAGE_LIMIT:
            handoffs.append(
                Handoff(
                    stage=PipelineStage.EXTRACT,
                    reason=HandoffReason.PAGE_LIMIT_EXCEEDED,
                    action=HandoffAction.MANUAL_REVIEW,
                    message=f"PDF exceeds page limit ({page_count} > {PAGE_LIMIT}).",
                    created_at=created_at,
                    blocking=True,
                )
            )
            return (
                ExtractSection(
                    ok=False,
                    text="",
                    used_ocr_stub=True,
                    method="stub",
                    page_count=page_count,
                ),
                handoffs,
            )

        text_layer = extract_text_layer(data)
        if text_layer:
            return (
                ExtractSection(
                    ok=True,
                    text=text_layer,
                    used_ocr_stub=False,
                    method="text_layer",
                    page_count=page_count,
                ),
                handoffs,
            )

        if api_key:
            images = pdf_to_images(data)
            if images:
                text = openai_vision_extract(images, api_key=api_key, model="gpt-4o")
                if text:
                    return (
                        ExtractSection(
                            ok=True,
                            text=text,
                            used_ocr_stub=False,
                            method="openai_vision",
                            model="gpt-4o",
                            page_count=len(images),
                        ),
                        handoffs,
                    )

        handoffs.append(
            Handoff(
                stage=PipelineStage.EXTRACT,
                reason=HandoffReason.OCR_REQUIRED,
                action=HandoffAction.MANUAL_REVIEW,
                message="No PDF text layer found and OCR could not run; using stub output.",
                created_at=created_at,
            )
        )
        return (
            ExtractSection(
                ok=True,
                text="[OCR_STUB: not available]",
                used_ocr_stub=True,
                method="stub",
                page_count=page_count,
            ),
            handoffs,
        )

    if ext in {".png", ".jpg", ".jpeg", ".tiff", ".webp"} and api_key:
        text = openai_vision_extract([data], api_key=api_key, model="gpt-4o")
        if text:
            return (
                ExtractSection(
                    ok=True,
                    text=text,
                    used_ocr_stub=False,
                    method="openai_vision",
                    model="gpt-4o",
                    page_count=1,
                ),
                handoffs,
            )

    handoffs.append(
        Handoff(
            stage=PipelineStage.EXTRACT,
            reason=HandoffReason.OCR_REQUIRED,
            action=HandoffAction.MANUAL_REVIEW,
            message="Unsupported or image-like document without configured OCR; stub used.",
            created_at=created_at,
        )
    )
    return (
        ExtractSection(
            ok=True,
            text="[OCR_STUB: not available]",
            used_ocr_stub=True,
            method="stub",
            page_count=1 if ext in {".png", ".jpg", ".jpeg", ".tiff", ".webp"} else None,
        ),
        handoffs,
    )
