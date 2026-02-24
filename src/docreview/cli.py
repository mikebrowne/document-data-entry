from __future__ import annotations

import json
import os
import platform
import shutil
from datetime import UTC, datetime
from pathlib import Path

import typer

from docreview.core.patch import PatchPayload, apply_patch
from docreview.core.schemas import DocumentReviewPackage
from docreview.stages.pipeline import run_pipeline
from docreview.utils.serialization import dump_model_json

app = typer.Typer(no_args_is_help=True)


def _versioned_output_path(output_dir: Path, stem: str) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    candidate = output_dir / f"{stem}_{timestamp}.json"
    counter = 1
    while candidate.exists():
        candidate = output_dir / f"{stem}_{timestamp}_v{counter}.json"
        counter += 1
    return candidate


@app.command()
def run(
    input: Path = typer.Option(...),
    output: Path = typer.Option(...),
    templates: Path | None = typer.Option(None),
    fill_mode: str = typer.Option("auto"),
    ocr_model: str = typer.Option("gpt-4o"),
    field_model: str | None = typer.Option(None),
) -> None:
    """Run full pipeline and write one JSON artifact."""
    if not input.exists():
        raise typer.Exit(code=2)
    output.mkdir(parents=True, exist_ok=True)
    template_dir = templates if templates is not None else Path(__file__).resolve().parent / "templates"
    if not template_dir.exists() or not template_dir.is_dir():
        typer.echo(f"Template directory not found: {template_dir}")
        raise typer.Exit(code=2)
    normalized_fill_mode = fill_mode.lower()
    if normalized_fill_mode not in {"auto", "llm", "regex"}:
        typer.echo("fill_mode must be one of: auto, llm, regex")
        raise typer.Exit(code=2)
    created_at = "1970-01-01T00:00:00Z"
    package = run_pipeline(
        input_path=input,
        template_dir=template_dir,
        created_at=created_at,
        fill_mode=normalized_fill_mode,
        ocr_model=ocr_model,
        field_model=field_model,
    )
    output_path = _versioned_output_path(output, input.stem)
    output_path.write_text(dump_model_json(package), encoding="utf-8")
    typer.echo(str(output_path))
    if any(h.blocking and not h.resolved for h in package.handoffs):
        raise typer.Exit(code=3)


@app.command("summarize")
def summarize_cmd(
    input: Path = typer.Option(...),
    format: str = typer.Option("markdown"),
) -> None:
    """Print markdown summary from a pipeline JSON artifact."""
    package = DocumentReviewPackage.model_validate_json(input.read_text(encoding="utf-8"))
    if format.lower() == "json":
        payload = {
            "document_type": package.classify.document_type,
            "confidence": package.classify.confidence,
            "validation_ok": package.validate_section.ok,
            "missing_required_fields": package.validate_section.missing_required_fields,
            "open_handoffs": len([h for h in package.handoffs if not h.resolved]),
            "total_handoffs": len(package.handoffs),
            "handoffs": [handoff.model_dump(mode="json") for handoff in package.handoffs],
        }
        typer.echo(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True))
        return
    typer.echo(package.render.markdown_summary)


@app.command("validate-json")
def validate_json_cmd(input: Path = typer.Option(...)) -> None:
    """Validate artifact JSON against DocumentReviewPackage schema."""
    try:
        DocumentReviewPackage.model_validate_json(input.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - explicit CLI UX path
        typer.echo(f"INVALID: {exc}")
        raise typer.Exit(code=1)
    typer.echo("VALID")


@app.command()
def doctor(format: str = typer.Option("text")) -> None:
    """Report local dependency and environment readiness."""
    payload: dict[str, str | bool] = {}
    lines: list[str] = []  # pragma: no cover - only used for text mode
    blocking = False

    py_ok = tuple(map(int, platform.python_version_tuple()[:2])) >= (3, 11)
    payload["python_version"] = platform.python_version()
    payload["python_ok"] = py_ok
    blocking = blocking or not py_ok

    for pkg in ("pydantic", "typer"):
        try:
            __import__(pkg)
            payload[f"{pkg}_installed"] = True
        except Exception:
            payload[f"{pkg}_installed"] = False
            blocking = True
    try:
        __import__("openai")
        payload["openai_installed"] = True
    except Exception:
        payload["openai_installed"] = False

    has_openai_key = bool(os.environ.get("OPENAI_API_KEY"))
    payload["openai_api_key_present"] = has_openai_key
    payload["pdftotext_available"] = shutil.which("pdftotext") is not None
    payload["pdftoppm_available"] = shutil.which("pdftoppm") is not None

    if format.lower() == "json":
        typer.echo(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True))
    else:
        lines.append(f"python_version={payload['python_version']} ok={payload['python_ok']}")
        lines.append(f"pydantic={'installed' if payload['pydantic_installed'] else 'missing'}")
        lines.append(f"typer={'installed' if payload['typer_installed'] else 'missing'}")
        lines.append(f"openai={'installed' if payload['openai_installed'] else 'missing'}")
        lines.append(f"openai_api_key={'present' if has_openai_key else 'missing'}")
        lines.append(
            "poppler="
            + (
                "ready"
                if payload["pdftotext_available"] and payload["pdftoppm_available"]
                else "missing"
            )
        )
        lines.append(
            "ocr="
            + ("openai_vision_ready" if has_openai_key else "stub_mode (OPENAI_API_KEY missing)")
        )
        typer.echo("\n".join(lines))

    if blocking:
        raise typer.Exit(code=1)


@app.command("patch")
def patch_cmd(
    input: Path = typer.Option(...),
    patch: Path = typer.Option(...),
    output: Path = typer.Option(...),
) -> None:
    """Apply append-only updates and handoff resolutions to an artifact."""
    if not input.exists() or not patch.exists():
        raise typer.Exit(code=2)
    output.mkdir(parents=True, exist_ok=True)
    created_at = "1970-01-01T00:00:00Z"
    package = DocumentReviewPackage.model_validate_json(input.read_text(encoding="utf-8"))
    payload = PatchPayload.model_validate_json(patch.read_text(encoding="utf-8"))
    updated = apply_patch(package=package, patch=payload, created_at=created_at)
    output_path = _versioned_output_path(output, input.stem)
    output_path.write_text(dump_model_json(updated), encoding="utf-8")
    typer.echo(str(output_path))


if __name__ == "__main__":
    app()
