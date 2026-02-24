import sys
from types import SimpleNamespace

from docreview.core.template_loader import DocumentTemplate, TemplateField
from docreview.stages.normalize import normalize_llm
from docreview.utils.openai_field_fill import openai_field_fill


def _template() -> DocumentTemplate:
    return DocumentTemplate(
        doc_type="paystub",
        display_name="Paystub",
        version="1.0",
        fields=[
            TemplateField(name="employee_name", type="string", required=True, synonyms=["employee"]),
            TemplateField(name="net_pay", type="number", required=True, synonyms=["net"]),
        ],
    )


def test_openai_field_fill_parses_json_and_filters_unknown_fields(monkeypatch) -> None:
    class FakeResponses:
        @staticmethod
        def create(**kwargs):
            _ = kwargs
            return SimpleNamespace(
                output_text=(
                    '{"field_values": ['
                    '{"field_name":"employee_name","value":"Jane Doe","confidence":0.91,'
                    '"evidence":"employee_name: Jane Doe","notes":null},'
                    '{"field_name":"not_in_template","value":"x","confidence":0.8,'
                    '"evidence":"x","notes":null}'
                    "]}"
                )
            )

    class FakeClient:
        def __init__(self, api_key: str):
            _ = api_key
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeClient))

    items = openai_field_fill(
        text="employee_name: Jane Doe",
        template=_template(),
        api_key="test-key",
        model="gpt-4.1-mini",
    )
    assert len(items) == 1
    assert items[0].field_name == "employee_name"
    assert items[0].value == "Jane Doe"


def test_normalize_llm_ignores_null_values(monkeypatch) -> None:
    class FakeResponses:
        @staticmethod
        def create(**kwargs):
            _ = kwargs
            return SimpleNamespace(
                output_text=(
                    '{"field_values": ['
                    '{"field_name":"employee_name","value":"Jane Doe","confidence":0.9,'
                    '"evidence":"employee_name: Jane Doe","notes":"from llm"},'
                    '{"field_name":"net_pay","value":null,"confidence":0.1,'
                    '"evidence":null,"notes":null}'
                    "]}"
                )
            )

    class FakeClient:
        def __init__(self, api_key: str):
            _ = api_key
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeClient))

    section = normalize_llm(
        text="employee_name: Jane Doe",
        template=_template(),
        created_at="1970-01-01T00:00:00Z",
        api_key="test-key",
        model="gpt-4.1-mini",
    )
    assert "employee_name" in section.fields
    assert "net_pay" not in section.fields
