from whisper_wfst.nbest_acceptor import build_nbest_acceptor, select_lowest_asr_cost
from whisper_wfst.types import Hypothesis, NBestArtifact


def _artifact() -> NBestArtifact:
    return NBestArtifact(
        segment_id="seg-p5",
        model="mock",
        runtime="hf-transformers",
        decode_config={"num_beams": 2},
        hypotheses=[
            Hypothesis(2, [2], "손해보험", "손해보험", "mock", True, None, None, -2.0, 2.0),
            Hypothesis(1, [1], "손해보혐", "손해보혐", "mock", True, None, None, -1.0, 1.0),
        ],
        created_at="2026-06-26T12:00:00+09:00",
    )


def test_build_nbest_acceptor_preserves_hypothesis_costs() -> None:
    candidates = build_nbest_acceptor(_artifact())

    assert [candidate.rank for candidate in candidates] == [1, 2]
    assert [candidate.text for candidate in candidates] == ["손해보혐", "손해보험"]
    assert [candidate.asr_cost for candidate in candidates] == [1.0, 2.0]


def test_select_lowest_asr_cost_uses_rank_tiebreak() -> None:
    selected = select_lowest_asr_cost(build_nbest_acceptor(_artifact()))

    assert selected.rank == 1
    assert selected.text == "손해보혐"
