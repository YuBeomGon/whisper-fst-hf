from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from whisper_wfst.types import ContractValidationError, NBestArtifact


def read_nbest_artifact(path: Path) -> NBestArtifact:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ContractValidationError("N-best artifact root must be an object")
        return NBestArtifact.from_dict(data)
    except ContractValidationError:
        raise
    except Exception as exc:
        raise ContractValidationError(f"failed to read N-best artifact {path}: {exc}") from exc


def write_nbest_artifact(artifact: NBestArtifact, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_nbest_jsonl(path: Path) -> list[NBestArtifact]:
    artifacts: list[NBestArtifact] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                raise ContractValidationError("JSONL row root must be an object")
            artifacts.append(NBestArtifact.from_dict(data))
        except ContractValidationError as exc:
            raise ContractValidationError(f"{path}:{line_number}: {exc}") from exc
        except Exception as exc:
            raise ContractValidationError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
    return artifacts


def write_nbest_jsonl(artifacts: Iterable[NBestArtifact], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(artifact.to_dict(), ensure_ascii=False, separators=(",", ":"))
        for artifact in artifacts
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


__all__ = [
    "read_nbest_artifact",
    "read_nbest_jsonl",
    "write_nbest_artifact",
    "write_nbest_jsonl",
]
