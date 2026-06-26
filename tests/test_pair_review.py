from pathlib import Path

from whisper_wfst.pair_review import (
    PairReviewCandidate,
    PairReviewConfig,
    audit_pair_candidates,
    render_pair_rule_source_audit_report,
    write_pair_review_csv,
    write_seed_rules_csv,
)
from whisper_wfst.rule_io import read_correction_rules_csv


def test_eval_only_candidate_cannot_become_seed_rule() -> None:
    candidate = _candidate(
        pair_id="P17_000001",
        source_files=["eval_a_l", "eval_b_l"],
        support_file_count=2,
    )

    result = audit_pair_candidates(
        [candidate],
        split_by_source={"eval_a_l": "eval_holdout", "eval_b_l": "eval_holdout"},
    )

    assert result.rows[0].review_class == "reject"
    assert result.rows[0].reason == "eval_holdout_only"
    assert result.seed_rules == []


def test_low_confidence_and_protected_candidates_are_rejected() -> None:
    low_confidence = _candidate(
        pair_id="P17_000002",
        source_files=["train_a_l", "train_b_l"],
        support_file_count=2,
        risk_flags=["low_alignment_confidence"],
    )
    protected = _candidate(
        pair_id="P17_000003",
        wrong="[NAME]",
        right="홍길동",
        source_files=["train_a_l", "train_b_l"],
        support_file_count=2,
        risk_flags=["protected_span"],
    )

    result = audit_pair_candidates(
        [low_confidence, protected],
        split_by_source={"train_a_l": "rule_mining", "train_b_l": "rule_mining"},
    )

    assert [row.review_class for row in result.rows] == ["reject", "reject"]
    assert [row.reason for row in result.rows] == [
        "low_alignment_confidence",
        "protected_or_pii_surface",
    ]
    assert result.seed_rules == []


def test_single_allowed_file_support_stays_needs_review() -> None:
    candidate = _candidate(
        pair_id="P17_000004",
        source_files=["train_a_l"],
        support_file_count=1,
    )

    result = audit_pair_candidates(
        [candidate],
        split_by_source={"train_a_l": "rule_mining"},
    )

    assert result.rows[0].review_class == "needs_review"
    assert result.rows[0].reason == "low_allowed_file_support"
    assert result.seed_rules == []


def test_optional_and_obligatory_seed_rules_are_valid_csv(tmp_path: Path) -> None:
    optional = _candidate(
        pair_id="P17_000005",
        source_files=["train_a_l", "train_b_l"],
        support_file_count=2,
        support_batch_count=1,
        alignment_confidence=0.72,
    )
    obligatory = _candidate(
        pair_id="P17_000006",
        source_files=["train_a_l", "train_b_l", "dev_a_l"],
        support_file_count=3,
        support_batch_count=2,
        alignment_confidence=0.91,
    )
    result = audit_pair_candidates(
        [optional, obligatory],
        split_by_source={
            "train_a_l": "rule_mining",
            "train_b_l": "rule_mining",
            "dev_a_l": "dev_review",
        },
        config=PairReviewConfig(
            min_allowed_file_support=2,
            obligatory_min_file_support=3,
            obligatory_min_batch_support=2,
            obligatory_min_confidence=0.9,
        ),
    )
    output = tmp_path / "correction_rules_seed_v2.csv"

    write_seed_rules_csv(result, output)
    rules = read_correction_rules_csv(output)

    assert [rule.rule_id for rule in rules] == ["P18_P17_000005", "P18_P17_000006"]
    assert [rule.mode for rule in rules] == ["optional", "obligatory"]
    assert all(rule.enabled for rule in rules)
    assert all(rule.source.startswith("pair_mining_v2:") for rule in rules)


def test_format_only_change_is_rejected() -> None:
    candidate = _candidate(
        pair_id="P17_000008",
        wrong="'개인정보",
        right="개인정보",
        source_files=["train_a_l", "train_b_l", "train_c_l"],
        support_file_count=3,
        alignment_confidence=0.9,
    )

    result = audit_pair_candidates(
        [candidate],
        split_by_source={
            "train_a_l": "rule_mining",
            "train_b_l": "rule_mining",
            "train_c_l": "rule_mining",
        },
    )

    assert result.rows[0].review_class == "reject"
    assert result.rows[0].reason == "format_only_change"
    assert result.seed_rules == []


def test_review_csv_and_report_are_redacted(tmp_path: Path) -> None:
    candidate = _candidate(
        pair_id="P17_000007",
        wrong="손해보혐",
        right="손해보험",
        source_files=["train_a_l", "train_b_l"],
        support_file_count=2,
    )
    result = audit_pair_candidates(
        [candidate],
        split_by_source={"train_a_l": "rule_mining", "train_b_l": "rule_mining"},
        config=PairReviewConfig(min_allowed_file_support=2),
    )
    review_csv = tmp_path / "pair_rule_source_audit_v2.csv"

    write_pair_review_csv(result, review_csv)
    report = render_pair_rule_source_audit_report(result)

    assert "P17_000007" in review_csv.read_text(encoding="utf-8")
    assert "Input candidates: 1" in report
    assert "Seed optional rules: 1" in report
    assert "손해보혐" not in report
    assert "손해보험" not in report


def test_committed_seed_v2_sample_is_valid() -> None:
    rules = read_correction_rules_csv(Path("data/correction_rules_seed_v2.sample.csv"))

    assert [rule.rule_id for rule in rules] == ["P18_P17_SAMPLE_001"]
    assert rules[0].mode == "optional"


def _candidate(
    *,
    pair_id: str,
    wrong: str = "손해보혐",
    right: str = "손해보험",
    source_files: list[str],
    support_file_count: int,
    support_batch_count: int = 1,
    alignment_confidence: float = 0.8,
    risk_flags: list[str] | None = None,
) -> PairReviewCandidate:
    return PairReviewCandidate(
        pair_id=pair_id,
        wrong=wrong,
        right=right,
        normalized_wrong=wrong,
        normalized_right=right,
        support_run_count=max(support_file_count, 1),
        support_file_count=support_file_count,
        support_batch_count=support_batch_count,
        support_variant_count=1,
        source_files=source_files,
        source_runs=["run_a"],
        alignment_confidence=alignment_confidence,
        risk_flags=risk_flags or [],
        suggested_class="candidate",
    )
