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

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
pytest
```

## CLI

```powershell
docreview run --input <file> --output <folder>
docreview summarize --input <json>
docreview validate-json --input <json>
docreview doctor
```
