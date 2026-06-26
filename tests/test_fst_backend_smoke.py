from pathlib import Path

from scripts.probe_fst_backend import run
from whisper_wfst.fst_backend import (
    BackendProbeResult,
    SmokeCheck,
    probe_pynini_backend,
    render_markdown_report,
)


def test_missing_pynini_is_reported_as_unavailable() -> None:
    def missing_import(name: str) -> object:
        raise ModuleNotFoundError(f"No module named {name!r}")

    result = probe_pynini_backend(import_module=missing_import)

    assert result.backend == "pynini"
    assert result.available is False
    assert result.blocker is not None
    assert "ModuleNotFoundError" in result.blocker
    assert result.checks == []


def test_current_environment_probe_is_structured() -> None:
    result = probe_pynini_backend()

    assert result.backend == "pynini"
    assert result.python_version

    if result.available:
        assert result.pynini_version
        assert {check.name for check in result.checks} >= {
            "utf8_hangul_acceptor",
            "domain_cross_compose_shortest_path",
            "output_string_roundtrip",
            "spacing_correction",
            "length_mismatch_correction",
        }
        assert all(check.passed for check in result.checks)
    else:
        assert result.blocker
        assert result.checks == []


def test_markdown_report_records_backend_decision() -> None:
    result = BackendProbeResult(
        backend="pynini",
        available=False,
        python_version="3.12.0",
        pynini_version=None,
        install_method="not installed in current uv environment",
        blocker="ModuleNotFoundError: No module named 'pynini'",
        checks=[
            SmokeCheck(
                name="utf8_hangul_acceptor",
                passed=False,
                detail="skipped because backend unavailable",
            )
        ],
    )

    report = render_markdown_report(result)

    assert "Backend available: no" in report
    assert "ModuleNotFoundError" in report
    assert "utf8_hangul_acceptor" in report
    assert "Fail-fast policy" in report


def test_cli_writes_probe_report(tmp_path: Path) -> None:
    output = tmp_path / "fst_backend_feasibility.md"

    exit_code = run(["--output", str(output)])

    assert exit_code == 0
    assert output.exists()
    report = output.read_text(encoding="utf-8")
    assert "# FST Backend Feasibility Report" in report
    assert "Backend available:" in report
