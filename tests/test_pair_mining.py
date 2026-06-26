from pathlib import Path

from whisper_wfst.pair_mining import (
    aggregate_pair_occurrences,
    extract_pair_occurrences,
    mine_pair_candidates,
    render_pair_mining_report,
)


def test_extract_pair_occurrences_expands_char_diff_to_word_boundary() -> None:
    occurrences = extract_pair_occurrences(
        hyp_text="손해보혐 가입 안내",
        ref_text="손해보험 가입 안내",
        source_stem="sample_l",
        run_id="run_a",
        variant="baseline",
        batch="AIG",
    )

    assert [(item.wrong, item.right) for item in occurrences] == [("손해보혐", "손해보험")]


def test_extract_pair_occurrences_rejects_digit_only_pairs() -> None:
    occurrences = extract_pair_occurrences(
        hyp_text="1234 안내",
        ref_text="5678 안내",
        source_stem="sample_l",
        run_id="run_a",
        variant="baseline",
        batch="AIG",
    )

    assert occurrences == []


def test_aggregate_pair_occurrences_separates_run_and_file_support() -> None:
    first = extract_pair_occurrences(
        hyp_text="손해보혐 안내",
        ref_text="손해보험 안내",
        source_stem="same_file_l",
        run_id="run_a",
        variant="baseline",
        batch="AIG",
    )
    second = extract_pair_occurrences(
        hyp_text="손해보혐 안내",
        ref_text="손해보험 안내",
        source_stem="same_file_l",
        run_id="run_b",
        variant="candidate",
        batch="AIG",
    )

    candidates = aggregate_pair_occurrences([*first, *second])

    assert len(candidates) == 1
    assert candidates[0].support_run_count == 2
    assert candidates[0].support_file_count == 1
    assert candidates[0].support_variant_count == 2


def test_mine_pair_candidates_uses_time_window_alignment(tmp_path: Path) -> None:
    annotations = tmp_path / "annotations" / "AIG"
    annotations.mkdir(parents=True)
    (annotations / "sample_l.txt").write_text(
        "1\n손해보험 가입 안내입니다\n"
        "2\n" + "다른 문장입니다 " * 20 + "\n"
        "3\n" + "추가 문장입니다 " * 20,
        encoding="utf-8",
    )
    srt_dir = tmp_path / "output" / "run_a" / "baseline"
    srt_dir.mkdir(parents=True)
    (srt_dir / "sample_l.srt").write_text(
        "1\n00:00:01,000 --> 00:00:03,000\n손해보혐 가입 안내입니다\n",
        encoding="utf-8",
    )

    result = mine_pair_candidates(
        srt_root=tmp_path / "output",
        annotations_root=tmp_path / "annotations",
    )

    assert [(candidate.wrong, candidate.right) for candidate in result.candidates] == [
        ("손해보혐", "손해보험")
    ]


def test_pair_mining_report_omits_candidate_surfaces() -> None:
    occurrences = extract_pair_occurrences(
        hyp_text="손해보혐 안내",
        ref_text="손해보험 안내",
        source_stem="sample_l",
        run_id="run_a",
        variant="baseline",
        batch="AIG",
    )
    result = aggregate_pair_occurrences(occurrences)
    report = render_pair_mining_report(
        candidate_count=len(result),
        occurrence_count=len(occurrences),
    )

    assert "Candidate pairs: 1" in report
    assert "손해보혐" not in report
    assert "손해보험" not in report
