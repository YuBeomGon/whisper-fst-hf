#!/usr/bin/env python3
"""Create a timestamped archive containing project docs, configs, and code."""

from __future__ import annotations

import argparse
import tarfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT_FILES = (
    "AGENTS.md",
    ".gitignore",
    "pyproject.toml",
    "uv.lock",
)

INCLUDE_DIRS = (
    "docs",
    "configs",
    "data",
    "src",
    "tests",
    "scripts",
)

EXCLUDED_RELATIVE_DIRS = {
    Path("data/raw"),
    Path("data/processed"),
}

EXCLUDED_DIR_NAMES = {
    ".git",
    ".agents",
    ".codex",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "outputs",
    "venv",
}

EXCLUDED_SUFFIXES = (
    ".egg-info",
    ".pyc",
    ".pyo",
    ".wav",
    ".mp3",
    ".flac",
    ".srt",
    ".jsonl.gz",
)


@dataclass(frozen=True)
class ArchiveOptions:
    project_root: Path
    output_dir: Path
    timestamp: str | None = None


def current_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def should_exclude(path: Path) -> bool:
    for excluded_dir in EXCLUDED_RELATIVE_DIRS:
        if path == excluded_dir or excluded_dir in path.parents:
            return True

    parts = set(path.parts)
    if parts & EXCLUDED_DIR_NAMES:
        return True

    return any(part.endswith(".egg-info") for part in path.parts) or any(
        path.name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES
    )


def iter_archive_files(project_root: Path) -> list[Path]:
    files: list[Path] = []

    for file_name in ROOT_FILES:
        path = project_root / file_name
        if path.is_file() and not should_exclude(path.relative_to(project_root)):
            files.append(path)

    for dir_name in INCLUDE_DIRS:
        root = project_root / dir_name
        if not root.is_dir():
            continue

        for path in sorted(root.rglob("*")):
            relative = path.relative_to(project_root)
            if path.is_file() and not should_exclude(relative):
                files.append(path)

    return sorted(files)


def create_archive(options: ArchiveOptions) -> Path:
    project_root = options.project_root.resolve()
    output_dir = options.output_dir.resolve()
    timestamp = options.timestamp or current_timestamp()
    archive_name = f"{project_root.name}_docs-config-code_{timestamp}.tar.gz"
    archive_path = output_dir / archive_name

    output_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, "w:gz") as archive:
        for path in iter_archive_files(project_root):
            relative = path.relative_to(project_root)
            archive.add(path, arcname=Path(project_root.name) / relative)

    return archive_path


def parse_args() -> ArchiveOptions:
    parser = argparse.ArgumentParser(
        description="Archive project docs, configs, and code with a timestamped file name."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root to archive. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Archive output directory. Defaults to <project-root>/outputs/archives.",
    )
    parser.add_argument(
        "--timestamp",
        default=None,
        help="Override timestamp for reproducible tests. Format: YYYYMMDD_HHMMSS.",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    output_dir = args.output_dir or project_root / "outputs" / "archives"
    return ArchiveOptions(
        project_root=project_root,
        output_dir=output_dir,
        timestamp=args.timestamp,
    )


def main() -> None:
    archive_path = create_archive(parse_args())
    print(archive_path)


if __name__ == "__main__":
    main()
