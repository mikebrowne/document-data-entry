# docreview

Deterministic document review engine (CLI + library) for single-document processing.

## Purpose

`docreview` processes one document at a time and emits one JSON artifact that preserves all AI proposals, explicit uncertainty handoffs, and an audit trail.

## What this is

- A local Python engine and CLI.
- A deterministic artifact builder focused on auditability.
- A Windows-built codebase intended to run later on macOS without code changes.

## What this is not

- Not a UI.
- Not underwriting, borrower, or deal decision logic.
- Not OpenClaw or skill logic.
- Not an automatic decisioning system.

## Quick start

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev,ocr]
pytest
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,ocr]'
pytest
```

See [docs/setup-windows.md](docs/setup-windows.md) or [docs/setup-macos.md](docs/setup-macos.md) for full setup guides.

## CLI

```powershell
docreview run --input <file> --output <folder> --fill-mode auto --ocr-model gpt-4o --field-model gpt-4.1-mini
docreview summarize --input <json>
docreview validate-json --input <json>
docreview doctor
```

## Field population modes

- `--fill-mode auto` (default): use LLM field fill when possible; fallback to regex.
- `--fill-mode llm`: require LLM field fill; unresolved setup becomes a blocking handoff.
- `--fill-mode regex`: force deterministic regex-only normalization.

Model configuration:

- `--ocr-model` controls PDF/image OCR model (OpenAI vision path).
- `--field-model` controls text-to-structured field filling.
- If `--field-model` is omitted, `docreview` uses the OCR model.

Environment fallbacks:

- `DOCREVIEW_FILL_MODE`
- `DOCREVIEW_OCR_MODEL`
- `DOCREVIEW_FIELD_MODEL`
- `OPENAI_API_KEY`
