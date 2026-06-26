import tarfile
from pathlib import Path

from scripts.archive_project_snapshot import ArchiveOptions, create_archive


def test_archive_uses_timestamped_name_and_includes_project_sources(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "AGENTS.md").write_text("agent guide\n", encoding="utf-8")
    (project_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (project_root / "docs").mkdir()
    (project_root / "docs" / "wbs.md").write_text("# WBS\n", encoding="utf-8")
    (project_root / "configs").mkdir()
    (project_root / "configs" / "hf.yaml").write_text("model: demo\n", encoding="utf-8")
    (project_root / "data").mkdir()
    (project_root / "data" / "correction_rules.csv").write_text(
        "rule_id,wrong,right\nR001,손해보혐,손해보험\n",
        encoding="utf-8",
    )
    (project_root / "src").mkdir()
    (project_root / "src" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    (project_root / "tests").mkdir()
    (project_root / "tests" / "test_module.py").write_text(
        "def test_ok(): pass\n", encoding="utf-8"
    )
    (project_root / "scripts").mkdir()
    (project_root / "scripts" / "tool.py").write_text("print('ok')\n", encoding="utf-8")

    archive_path = create_archive(
        ArchiveOptions(
            project_root=project_root,
            output_dir=project_root / "outputs" / "archives",
            timestamp="20260626_103000",
        )
    )

    assert archive_path.name == "project_docs-config-code_20260626_103000.tar.gz"
    assert archive_path.parent == project_root / "outputs" / "archives"

    with tarfile.open(archive_path, "r:gz") as archive:
        names = set(archive.getnames())

    assert "project/AGENTS.md" in names
    assert "project/pyproject.toml" in names
    assert "project/docs/wbs.md" in names
    assert "project/configs/hf.yaml" in names
    assert "project/data/correction_rules.csv" in names
    assert "project/src/module.py" in names
    assert "project/tests/test_module.py" in names
    assert "project/scripts/tool.py" in names


def test_archive_excludes_generated_and_large_artifact_paths(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "docs").mkdir()
    (project_root / "docs" / "index.md").write_text("# Index\n", encoding="utf-8")
    (project_root / "outputs").mkdir()
    (project_root / "outputs" / "large.jsonl").write_text("{}\n", encoding="utf-8")
    (project_root / "data").mkdir()
    (project_root / "data" / "raw").mkdir()
    (project_root / "data" / "raw" / "audio.wav").write_bytes(b"ignored")
    (project_root / "data" / "processed").mkdir()
    (project_root / "data" / "processed" / "full.jsonl").write_text(
        "{}\n", encoding="utf-8"
    )
    (project_root / ".venv").mkdir()
    (project_root / ".venv" / "pyvenv.cfg").write_text("ignored\n", encoding="utf-8")
    (project_root / "src").mkdir()
    (project_root / "src" / "__pycache__").mkdir()
    (project_root / "src" / "__pycache__" / "module.pyc").write_bytes(b"ignored")
    (project_root / "src" / "project.egg-info").mkdir()
    (project_root / "src" / "project.egg-info" / "PKG-INFO").write_text(
        "ignored\n", encoding="utf-8"
    )
    (project_root / "model.wav").write_bytes(b"ignored")

    archive_path = create_archive(
        ArchiveOptions(
            project_root=project_root,
            output_dir=project_root / "outputs" / "archives",
            timestamp="20260626_103001",
        )
    )

    with tarfile.open(archive_path, "r:gz") as archive:
        names = set(archive.getnames())

    assert "project/docs/index.md" in names
    assert "project/outputs/large.jsonl" not in names
    assert "project/data/raw/audio.wav" not in names
    assert "project/data/processed/full.jsonl" not in names
    assert "project/.venv/pyvenv.cfg" not in names
    assert "project/src/__pycache__/module.pyc" not in names
    assert "project/src/project.egg-info/PKG-INFO" not in names
    assert "project/model.wav" not in names
