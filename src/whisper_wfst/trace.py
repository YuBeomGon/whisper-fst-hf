from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CorrectionDecisionTrace:
    segment_id: str
    decision: str
    source_hypothesis_rank: int
    before_text: str
    after_text: str
    asr_cost: float
    corrected_total_cost: float
    correction_cost: float
    applied_rule_ids: list[str]
    domain_gate_open: bool
    margin: float
    blocked_reason: str | None
    backend_strategy: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CorrectionDecisionTrace:
        return cls(
            segment_id=data["segment_id"],
            decision=data["decision"],
            source_hypothesis_rank=data["source_hypothesis_rank"],
            before_text=data["before_text"],
            after_text=data["after_text"],
            asr_cost=data["asr_cost"],
            corrected_total_cost=data["corrected_total_cost"],
            correction_cost=data["correction_cost"],
            applied_rule_ids=list(data["applied_rule_ids"]),
            domain_gate_open=data["domain_gate_open"],
            margin=data["margin"],
            blocked_reason=data.get("blocked_reason"),
            backend_strategy=data["backend_strategy"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "decision": self.decision,
            "source_hypothesis_rank": self.source_hypothesis_rank,
            "before_text": self.before_text,
            "after_text": self.after_text,
            "asr_cost": self.asr_cost,
            "corrected_total_cost": self.corrected_total_cost,
            "correction_cost": self.correction_cost,
            "applied_rule_ids": list(self.applied_rule_ids),
            "domain_gate_open": self.domain_gate_open,
            "margin": self.margin,
            "blocked_reason": self.blocked_reason,
            "backend_strategy": self.backend_strategy,
        }


__all__ = ["CorrectionDecisionTrace"]
