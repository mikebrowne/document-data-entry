# macOS Setup

## Requirements

- macOS 12+
- Python 3.11+
- Homebrew

## System dependencies

```bash
brew update
brew install poppler
```

This provides `pdftotext` and `pdftoppm` for PDF text-layer extraction and page-to-image conversion.

## Clone and install

```bash
git clone <REPO_URL>
cd docreview

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -e '.[dev,ocr]'
```

The `ocr` extra installs the `openai` package, which is required for both vision OCR and LLM field filling.

## Set environment variables

```bash
export OPENAI_API_KEY="sk-..."
```

Optional model/mode overrides (CLI flags take precedence):

```bash
export DOCREVIEW_FILL_MODE="auto"       # auto | llm | regex
export DOCREVIEW_OCR_MODEL="gpt-4o"     # vision OCR model
export DOCREVIEW_FIELD_MODEL="gpt-4.1-mini"  # text-to-fields model
```

## Verify

```bash
docreview doctor --format json
```

Confirm:

- `python_ok`: true
- `pydantic_installed`: true
- `typer_installed`: true
- `openai_installed`: true
- `openai_api_key_present`: true
- `pdftotext_available`: true
- `pdftoppm_available`: true

If `openai_installed` is false, you likely installed with `.[dev]` instead of `.[dev,ocr]`. Fix with:

```bash
pip install -e '.[dev,ocr]'
```

## Run

```bash
docreview run --input "/path/to/document.pdf" --output "./artifacts"
docreview run --input "/path/to/document.pdf" --output "./artifacts" --fill-mode llm --field-model gpt-4.1-mini
docreview summarize --input "./artifacts/document_*.json" --format json
docreview validate-json --input "./artifacts/document_*.json"
```

## Patch workflow (agent review loop)

```bash
docreview patch --input "./artifacts/original.json" --patch "./patch.json" --output "./artifacts"
docreview validate-json --input "./artifacts/original_*.json"
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `openai package not installed` in audit/handoff | Installed with `.[dev]` only | `pip install -e '.[dev,ocr]'` |
| `pdftotext` / `pdftoppm` not found | Poppler missing | `brew install poppler` |
| `OPENAI_API_KEY missing` handoff | Env var not set | `export OPENAI_API_KEY="sk-..."` |
| Exit code 3 | Blocking handoffs exist | Check artifact JSON `handoffs` for details |
