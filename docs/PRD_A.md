# PRD A (Concise)

This repository implements PRD A only: a deterministic Python document review engine for Windows development that is portable to later macOS execution.

Core behavior:

- Process exactly one document per run.
- Emit one JSON artifact per document.
- Preserve original AI proposals and proposal history.
- Emit explicit handoffs for uncertainty.
- Keep an auditable stage-by-stage trail.

Included scope:

- Pydantic contracts and enums.
- JSON template system and Markdown generator.
- Pure pipeline stage logic (ingest, extract, classify, normalize, validate, render).
- Typer CLI (`run`, `summarize`, `validate-json`, `doctor`).
- Local tests with no external API dependency.

Excluded scope:

- macOS runtime implementation details.
- OpenClaw logic, UI, skills, borrower/deal logic, underwriting decisions.
