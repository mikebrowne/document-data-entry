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
pip install -e .[dev]
```

## Verify

```powershell
pytest
docreview doctor
```

## Run

```powershell
docreview run --input "C:\path\to\document.txt" --output ".\artifacts"
docreview summarize --input ".\artifacts\document_20260101T120000Z.json"
docreview validate-json --input ".\artifacts\document_20260101T120000Z.json"
```

## Notes

- OCR is stubbed in PRD A.
- No external API calls are required for tests or normal local validation.
