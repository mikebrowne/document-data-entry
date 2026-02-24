# Windows Setup

## Requirements

- Windows 10 or 11
- Python 3.11+
- PowerShell

## Setup

```powershell
cd <repo>\docreview
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e .[dev,ocr]
```

## Verify

```powershell
pytest
docreview doctor
```

## Run

```powershell
docreview run --input "C:\path\to\document.txt" --output ".\artifacts" --fill-mode auto
docreview summarize --input ".\artifacts\document_20260101T120000Z.json"
docreview validate-json --input ".\artifacts\document_20260101T120000Z.json"
```

## Notes

- `OPENAI_API_KEY` enables OpenAI vision OCR and LLM field fill.
- `--fill-mode` supports `auto`, `llm`, and `regex`.
- `--ocr-model` and `--field-model` let agents pick models per run.
- No external API calls are required for tests or normal local validation.
