from __future__ import annotations

import platform
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import import_module as default_import_module
from types import ModuleType
from typing import Any


@dataclass(frozen=True)
class SmokeCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class BackendProbeResult:
    backend: str
    available: bool
    python_version: str
    pynini_version: str | None
    install_method: str
    blocker: str | None
    checks: list[SmokeCheck]


def probe_pynini_backend(
    import_module: Callable[[str], ModuleType | object] = default_import_module,
) -> BackendProbeResult:
    python_version = platform.python_version()
    install_method = "import pynini from current uv/python environment"

    try:
        pynini = import_module("pynini")
    except Exception as exc:
        return BackendProbeResult(
            backend="pynini",
            available=False,
            python_version=python_version,
            pynini_version=None,
            install_method=install_method,
            blocker=f"{type(exc).__name__}: {exc}",
            checks=[],
        )

    checks = _run_pynini_smokes(pynini)
    failed = [check for check in checks if not check.passed]

    return BackendProbeResult(
        backend="pynini",
        available=not failed,
        python_version=python_version,
        pynini_version=_version_for(pynini),
        install_method=install_method,
        blocker=None if not failed else "One or more Pynini/OpenFST smoke checks failed",
        checks=checks,
    )


def render_markdown_report(
    result: BackendProbeResult,
    *,
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now(UTC)
    available = "yes" if result.available else "no"
    pynini_version = result.pynini_version or "not available"
    blocker = result.blocker or "none"

    lines = [
        "# FST Backend Feasibility Report",
        "",
        f"Generated at: {generated_at.isoformat()}",
        "",
        "## Decision",
        "",
        f"- Backend: `{result.backend}`",
        f"- Backend available: {available}",
        f"- Python version: `{result.python_version}`",
        f"- Pynini version: `{pynini_version}`",
        f"- Dependency check: {result.install_method}",
        f"- Blocker: {blocker}",
        "",
        "## Smoke Checks",
        "",
    ]

    if result.checks:
        lines.extend(
            [
                "| Check | Result | Detail |",
                "| --- | --- | --- |",
            ]
        )
        for check in result.checks:
            status = "pass" if check.passed else "fail"
            lines.append(f"| `{check.name}` | {status} | {check.detail} |")
    else:
        lines.append("No smoke checks were executed because the backend is unavailable.")

    lines.extend(
        [
            "",
            "## Fail-fast policy",
            "",
            "P3 이후 구현은 `pynini` backend availability를 먼저 확인해야 한다. backend가",
            "unavailable이면 correction engine은 암묵적으로 성공 처리하지 말고 명시적 예외,",
            "disabled trace, 또는 별도 fallback engine 중 하나를 선택해야 한다.",
            "",
            "## P3 impact",
            "",
        ]
    )

    if result.available:
        lines.append("P3 이후 Pynini backend를 구현 후보로 사용할 수 있다.")
    else:
        lines.append(
            "P3 이후 Pynini backend를 무조건 전제하면 안 된다. dependency 설치 경로 확정 "
            "또는 fallback 전략이 필요하다."
        )

    lines.append("")
    return "\n".join(lines)


def _run_pynini_smokes(pynini: Any) -> list[SmokeCheck]:
    checks = [
        _smoke("utf8_hangul_acceptor", lambda: _check_acceptor_roundtrip(pynini, "손해보험")),
        _smoke(
            "domain_cross_compose_shortest_path",
            lambda: _check_rewrite(pynini, "손해보혐", "손해보험"),
        ),
        _smoke(
            "synthetic_nbest_acceptor_compose",
            lambda: _check_nbest_compose(pynini, "손해보혐", "손해보험", "손해보힘"),
        ),
        _smoke(
            "output_string_roundtrip",
            lambda: _check_acceptor_roundtrip(pynini, "손해보험"),
        ),
        _smoke("spacing_correction", lambda: _check_rewrite(pynini, "손해 보혐", "손해 보험")),
        _smoke(
            "length_mismatch_correction",
            lambda: _check_rewrite(pynini, "보험가입", "보험 가입"),
        ),
    ]
    return checks


def _smoke(name: str, check: Callable[[], str]) -> SmokeCheck:
    try:
        return SmokeCheck(name=name, passed=True, detail=check())
    except Exception as exc:
        return SmokeCheck(name=name, passed=False, detail=f"{type(exc).__name__}: {exc}")


def _check_acceptor_roundtrip(pynini: Any, text: str) -> str:
    acceptor = pynini.accep(text, token_type="utf8")
    output = _shortest_string(pynini, acceptor)
    if output != text:
        raise ValueError(f"expected {text!r}, got {output!r}")
    return f"roundtrip {text!r}"


def _check_rewrite(pynini: Any, wrong: str, right: str) -> str:
    correction = _cross(pynini, wrong, right)
    input_acceptor = pynini.accep(wrong, token_type="utf8")
    composed = pynini.compose(input_acceptor, correction)
    output = _shortest_string(pynini, composed)
    if output != right:
        raise ValueError(f"expected {right!r}, got {output!r}")
    return f"{wrong!r} -> {right!r}"


def _check_nbest_compose(pynini: Any, wrong: str, right: str, distractor: str) -> str:
    nbest_acceptor = pynini.union(
        pynini.accep(wrong, token_type="utf8"),
        pynini.accep(distractor, token_type="utf8"),
    ).optimize()
    correction = _cross(pynini, wrong, right)
    composed = pynini.compose(nbest_acceptor, correction)
    output = _shortest_string(pynini, composed)
    if output != right:
        raise ValueError(f"expected {right!r}, got {output!r}")
    return f"N-best candidate {wrong!r} composes to {right!r}"


def _cross(pynini: Any, wrong: str, right: str) -> Any:
    try:
        return pynini.cross(
            wrong,
            right,
            input_token_type="utf8",
            output_token_type="utf8",
        )
    except TypeError:
        return pynini.cross(wrong, right)


def _shortest_string(pynini: Any, fst: Any) -> str:
    return pynini.shortestpath(fst, nshortest=1, unique=True).optimize().string(
        token_type="utf8"
    )


def _version_for(module: object) -> str:
    version = getattr(module, "__version__", None)
    return str(version) if version else "unknown"


__all__ = [
    "BackendProbeResult",
    "SmokeCheck",
    "probe_pynini_backend",
    "render_markdown_report",
]
