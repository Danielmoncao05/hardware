"""Static check: no patient or clinical fields, endpoints, or screens exist (spec: Keep inventory data
technical and non-clinical; Generate operational reports). Runs without a backend."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Identifiers that would indicate patient/clinical data (Portuguese and English)
FORBIDDEN = re.compile(
    r"\b\w*(paciente|patient|prontuario|prontuário|diagnos\w*|clinic\w*|clínic\w*|cpf|cns|cartao_sus|medical_record|mrn|leito|bed_number|prescri\w*)\w*\b",
    re.IGNORECASE,
)


def _schema_field_names(xs: str) -> list[str]:
    """Field names declared in a XanoScript table schema block."""
    block = re.search(r"schema\s*\{(.*)\n  \}", xs, re.S)
    if not block:
        return []
    return re.findall(r"^\s*(?:int|text|email|password|decimal|bool|timestamp|date|uuid|json|enum|object|image|attachment)\??\s+(\w+)", block.group(1), re.M)


def test_tables_have_no_clinical_fields():
    offenders = []
    for path in sorted((ROOT / "xano" / "table").glob("*.xs")):
        for name in _schema_field_names(path.read_text(encoding="utf-8")):
            if FORBIDDEN.search(name):
                offenders.append(f"{path.name}: {name}")
    assert not offenders, f"Clinical/patient fields found: {offenders}"


def test_no_clinical_endpoints_or_inputs():
    offenders = []
    for path in sorted((ROOT / "xano" / "api").rglob("*.xs")):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r'query\s+"?([^"\s]+)"?\s+verb=', text):
            if FORBIDDEN.search(m.group(1)):
                offenders.append(f"{path.name}: route {m.group(1)}")
        inputs = re.search(r"input\s*\{(.*?)\n  \}", text, re.S)
        if inputs:
            for name in re.findall(r"^\s*\w+\??(?:\[\])?\s+(\w+)\??", inputs.group(1), re.M):
                if FORBIDDEN.search(name):
                    offenders.append(f"{path.name}: input {name}")
    assert not offenders, f"Clinical/patient endpoints or inputs found: {offenders}"


def test_no_clinical_routes_or_report_columns_in_ui():
    app = (ROOT / "hardware" / "hardware.py").read_text(encoding="utf-8")
    routes = re.findall(r'route="([^"]+)"', app)
    assert routes, "no routes found"
    assert not [r for r in routes if FORBIDDEN.search(r)], routes

    reports = (ROOT / "hardware" / "pages" / "reports.py").read_text(encoding="utf-8")
    columns = re.findall(r'\("(\w+)",\s*"[^"]+"\)', reports)
    assert columns
    assert not [c for c in columns if FORBIDDEN.search(c)], columns


def test_csv_report_columns_are_operational_only():
    for path in sorted((ROOT / "xano" / "api" / "reports").glob("relatorio_*.xs")):
        keys = re.findall(r'\{key:\s*"(\w+)"', path.read_text(encoding="utf-8"))
        assert keys, path.name
        assert not [k for k in keys if FORBIDDEN.search(k)], (path.name, keys)
