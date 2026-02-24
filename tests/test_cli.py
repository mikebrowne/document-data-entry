from pathlib import Path
import json

from typer.testing import CliRunner

from docreview.cli import app
from docreview.core.enums import PipelineStage
from docreview.core.schemas import FieldProposal, NormalizeSection

runner = CliRunner()


def test_doctor() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "python_version=" in result.stdout
    assert "openai_api_key=missing" in result.stdout


def test_doctor_json_format() -> None:
    result = runner.invoke(app, ["doctor", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "openai_api_key_present" in payload
    assert "openai_installed" in payload


def test_run_summarize_validate_json_and_json_summary(tmp_path: Path) -> None:
    input_file = tmp_path / "paystub.txt"
    output_dir = tmp_path / "artifacts"
    input_file.write_text(
        "\n".join(
            [
                "Paystub",
                "employee_name: Jane Doe",
                "employer_name: ACME Corp",
                "net_pay: 2450.25",
            ]
        ),
        encoding="utf-8",
    )

    run_result = runner.invoke(
        app,
        [
            "run",
            "--input",
            str(input_file),
            "--output",
            str(output_dir),
        ],
    )
    assert run_result.exit_code == 0

    generated = sorted(output_dir.glob("*.json"))
    assert len(generated) == 1
    artifact_path = generated[0]

    validate_result = runner.invoke(
        app,
        ["validate-json", "--input", str(artifact_path)],
    )
    assert validate_result.exit_code == 0
    assert "VALID" in validate_result.stdout

    summarize_result = runner.invoke(
        app,
        ["summarize", "--input", str(artifact_path)],
    )
    assert summarize_result.exit_code == 0
    assert "Document Review" in summarize_result.stdout

    summarize_json_result = runner.invoke(
        app,
        ["summarize", "--input", str(artifact_path), "--format", "json"],
    )
    assert summarize_json_result.exit_code == 0
    payload = json.loads(summarize_json_result.stdout)
    assert payload["document_type"] == "paystub"
    assert "open_handoffs" in payload


def test_run_with_custom_templates(tmp_path: Path) -> None:
    input_file = tmp_path / "lease.txt"
    output_dir = tmp_path / "artifacts"
    template_dir = tmp_path / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "lease.json").write_text(
        json.dumps(
            {
                "doc_type": "lease_agreement",
                "display_name": "Lease Agreement",
                "version": "1.0",
                "fields": [
                    {"name": "tenant_name", "type": "string", "required": True, "synonyms": ["tenant"]},
                    {"name": "rent_amount", "type": "number", "required": True, "synonyms": ["rent"]},
                ],
            }
        ),
        encoding="utf-8",
    )
    input_file.write_text(
        "Lease Agreement\ntenant_name: Jane Doe\nrent_amount: 2200",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            "--input",
            str(input_file),
            "--output",
            str(output_dir),
            "--templates",
            str(template_dir),
        ],
    )
    assert result.exit_code == 0
    artifact = sorted(output_dir.glob("*.json"))[0]
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["classify"]["document_type"] == "lease_agreement"


def test_patch_command_appends_and_resolves(tmp_path: Path) -> None:
    artifact_path = tmp_path / "artifact.json"
    patch_path = tmp_path / "patch.json"
    output_dir = tmp_path / "patched"
    artifact_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "metadata": {
                    "document_id": "abc123",
                    "source_path": "C:/tmp/doc.txt",
                    "file_name": "doc.txt",
                    "file_hash": "f" * 64,
                    "file_size_bytes": 10,
                    "extension": ".txt",
                    "created_at": "1970-01-01T00:00:00Z",
                },
                "ingest": {
                    "stage": "ingest",
                    "ok": True,
                    "source_path": "C:/tmp/doc.txt",
                    "file_hash": "f" * 64,
                    "file_size_bytes": 10,
                    "mime_type": "text/plain",
                },
                "extract": {
                    "stage": "extract",
                    "ok": True,
                    "text": "sample",
                    "used_ocr_stub": False,
                    "method": "text_layer",
                    "model": None,
                    "page_count": None,
                },
                "classify": {
                    "stage": "classify",
                    "ok": True,
                    "document_type": "paystub",
                    "confidence": 0.9,
                },
                "normalize": {
                    "stage": "normalize",
                    "ok": True,
                    "fields": {
                        "employee_name": [
                            {
                                "source": "extract_text",
                                "value": "Jane Doe",
                                "confidence": 0.9,
                                "stage": "normalize",
                                "created_at": "1970-01-01T00:00:00Z",
                                "notes": None,
                            }
                        ]
                    },
                },
                "validate": {
                    "stage": "validate",
                    "ok": True,
                    "field_status": {"employee_name": "valid"},
                    "missing_required_fields": [],
                },
                "render": {"stage": "render", "ok": True, "markdown_summary": "summary"},
                "handoffs": [
                    {
                        "stage": "classify",
                        "reason": "low_confidence",
                        "action": "manual_review",
                        "message": "check",
                        "field_name": None,
                        "created_at": "1970-01-01T00:00:00Z",
                        "blocking": False,
                        "resolved": False,
                        "resolved_at": None,
                        "resolution": None,
                        "resolved_by": None,
                    }
                ],
                "audit": [],
            }
        ),
        encoding="utf-8",
    )
    patch_path.write_text(
        json.dumps(
            {
                "field_updates": [
                    {
                        "field_name": "employee_name",
                        "value": "Jane A. Doe",
                        "confidence": 0.95,
                        "source": "agent_review",
                    }
                ],
                "handoff_resolutions": [
                    {"index": 0, "resolution": "Verified manually", "resolved_by": "agent_review"}
                ],
            }
        ),
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        ["patch", "--input", str(artifact_path), "--patch", str(patch_path), "--output", str(output_dir)],
    )
    assert result.exit_code == 0
    patched = sorted(output_dir.glob("*.json"))[0]
    payload = json.loads(patched.read_text(encoding="utf-8"))
    assert len(payload["normalize"]["fields"]["employee_name"]) == 2
    assert payload["handoffs"][0]["resolved"] is True


def test_run_returns_blocking_code_for_empty_input(tmp_path: Path) -> None:
    input_file = tmp_path / "empty.pdf"
    output_dir = tmp_path / "artifacts"
    input_file.write_bytes(b"")
    result = runner.invoke(
        app,
        ["run", "--input", str(input_file), "--output", str(output_dir)],
    )
    assert result.exit_code == 3


def test_run_returns_blocking_code_for_unclassifiable_input(tmp_path: Path) -> None:
    input_file = tmp_path / "unknown.txt"
    output_dir = tmp_path / "artifacts"
    input_file.write_text("x y z no matching keywords", encoding="utf-8")
    result = runner.invoke(
        app,
        ["run", "--input", str(input_file), "--output", str(output_dir)],
    )
    assert result.exit_code == 3


def test_run_auto_mode_falls_back_to_regex_with_handoff(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    input_file = tmp_path / "paystub.txt"
    output_dir = tmp_path / "artifacts"
    input_file.write_text(
        "Paystub\nemployee_name: Jane Doe\nemployer_name: ACME Corp\nnet_pay: 1000",
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        ["run", "--input", str(input_file), "--output", str(output_dir)],
    )
    assert result.exit_code == 0
    artifact = sorted(output_dir.glob("*.json"))[0]
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert any(
        h["stage"] == "normalize" and h["reason"] == "invalid_input" and h["blocking"] is False
        for h in payload["handoffs"]
    )
    assert payload["normalize"]["fields"]["employee_name"][0]["source"] == "extract_text"


def test_run_llm_mode_missing_key_is_blocking(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    input_file = tmp_path / "paystub.txt"
    output_dir = tmp_path / "artifacts"
    input_file.write_text("Paystub\nemployee_name: Jane Doe", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "run",
            "--input",
            str(input_file),
            "--output",
            str(output_dir),
            "--fill-mode",
            "llm",
        ],
    )
    assert result.exit_code == 3


def test_run_regex_mode_forces_regex(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    input_file = tmp_path / "paystub.txt"
    output_dir = tmp_path / "artifacts"
    input_file.write_text("Paystub\nemployee_name: Jane Doe", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "run",
            "--input",
            str(input_file),
            "--output",
            str(output_dir),
            "--fill-mode",
            "regex",
        ],
    )
    assert result.exit_code == 0
    artifact = sorted(output_dir.glob("*.json"))[0]
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert not any(h["stage"] == "normalize" and h["reason"] == "invalid_input" for h in payload["handoffs"])


def test_run_llm_mode_uses_field_model(tmp_path: Path, monkeypatch) -> None:
    import docreview.stages.pipeline as pipeline_module

    captured: dict[str, str] = {}

    def fake_normalize_llm(
        text: str,
        template,
        created_at: str,
        *,
        api_key: str,
        model: str,
    ) -> NormalizeSection:
        captured["model"] = model
        proposal = FieldProposal(
            source="openai_field_fill",
            value="Jane Doe",
            confidence=0.93,
            stage=PipelineStage.NORMALIZE,
            created_at=created_at,
            notes="evidence=employee_name: Jane Doe",
        )
        return NormalizeSection(ok=True, fields={"employee_name": [proposal]})

    monkeypatch.setattr(pipeline_module, "normalize_llm", fake_normalize_llm)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    input_file = tmp_path / "paystub.txt"
    output_dir = tmp_path / "artifacts"
    input_file.write_text("Paystub\nemployee_name: Jane Doe", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "run",
            "--input",
            str(input_file),
            "--output",
            str(output_dir),
            "--fill-mode",
            "llm",
            "--field-model",
            "gpt-4.1-mini",
        ],
    )
    assert result.exit_code == 0
    assert captured["model"] == "gpt-4.1-mini"
    artifact = sorted(output_dir.glob("*.json"))[0]
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["normalize"]["fields"]["employee_name"][0]["source"] == "openai_field_fill"
