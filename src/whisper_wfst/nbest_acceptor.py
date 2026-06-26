from __future__ import annotations

from dataclasses import dataclass

from whisper_wfst.types import NBestArtifact


@dataclass(frozen=True)
class NBestCandidate:
    rank: int
    text: str
    asr_cost: float


def build_nbest_acceptor(artifact: NBestArtifact) -> list[NBestCandidate]:
    return [
        NBestCandidate(
            rank=hypothesis.rank,
            text=hypothesis.normalized_text,
            asr_cost=hypothesis.asr_cost,
        )
        for hypothesis in sorted(artifact.hypotheses, key=lambda item: item.rank)
    ]


def select_lowest_asr_cost(candidates: list[NBestCandidate]) -> NBestCandidate:
    if not candidates:
        raise ValueError("N-best candidates must not be empty")
    return min(candidates, key=lambda candidate: (candidate.asr_cost, candidate.rank))


__all__ = ["NBestCandidate", "build_nbest_acceptor", "select_lowest_asr_cost"]
