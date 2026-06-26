from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


class ContractValidationError(ValueError):
    """Raised when a persisted contract object is structurally invalid."""


@dataclass(frozen=True)
class Hypothesis:
    rank: int
    token_ids: list[int]
    raw_text: str
    normalized_text: str
    score_source: str
    score_is_logprob: bool
    length_penalty: float | None
    raw_logprob: float | None
    decoder_score: float
    asr_cost: float

    def __post_init__(self) -> None:
        _require_int("rank", self.rank, minimum=1)
        if not isinstance(self.token_ids, list) or not all(
            isinstance(token_id, int) and not isinstance(token_id, bool)
            for token_id in self.token_ids
        ):
            raise ContractValidationError("token_ids must be a list[int]")
        _require_str("raw_text", self.raw_text)
        _require_str("normalized_text", self.normalized_text)
        _require_non_empty_str("score_source", self.score_source)
        _require_bool("score_is_logprob", self.score_is_logprob)
        _require_optional_number("length_penalty", self.length_penalty)
        _require_optional_number("raw_logprob", self.raw_logprob)
        _require_number("decoder_score", self.decoder_score)
        _require_number("asr_cost", self.asr_cost, minimum=0.0)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Hypothesis:
        return cls(
            rank=data["rank"],
            token_ids=list(data["token_ids"]),
            raw_text=data["raw_text"],
            normalized_text=data["normalized_text"],
            score_source=data["score_source"],
            score_is_logprob=data["score_is_logprob"],
            length_penalty=data.get("length_penalty"),
            raw_logprob=data.get("raw_logprob"),
            decoder_score=data["decoder_score"],
            asr_cost=data["asr_cost"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "token_ids": list(self.token_ids),
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "score_source": self.score_source,
            "score_is_logprob": self.score_is_logprob,
            "length_penalty": self.length_penalty,
            "raw_logprob": self.raw_logprob,
            "decoder_score": self.decoder_score,
            "asr_cost": self.asr_cost,
        }


@dataclass(frozen=True)
class NBestArtifact:
    segment_id: str
    model: str
    runtime: str
    decode_config: dict[str, Any]
    hypotheses: list[Hypothesis]
    created_at: str
    audio_ref: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str("segment_id", self.segment_id)
        _require_non_empty_str("model", self.model)
        _require_non_empty_str("runtime", self.runtime)
        if not isinstance(self.decode_config, dict):
            raise ContractValidationError("decode_config must be a dict")
        if not isinstance(self.hypotheses, list) or not all(
            isinstance(hypothesis, Hypothesis) for hypothesis in self.hypotheses
        ):
            raise ContractValidationError("hypotheses must be a list[Hypothesis]")
        _require_non_empty_str("created_at", self.created_at)
        if self.audio_ref is not None:
            _require_non_empty_str("audio_ref", self.audio_ref)
        object.__setattr__(self, "hypotheses", dedupe_hypotheses(self.hypotheses))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NBestArtifact:
        return cls(
            segment_id=data["segment_id"],
            model=data["model"],
            runtime=data["runtime"],
            decode_config=dict(data["decode_config"]),
            hypotheses=[
                Hypothesis.from_dict(hypothesis) for hypothesis in data["hypotheses"]
            ],
            created_at=data["created_at"],
            audio_ref=data.get("audio_ref"),
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "segment_id": self.segment_id,
            "model": self.model,
            "runtime": self.runtime,
            "decode_config": self.decode_config,
            "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
            "created_at": self.created_at,
        }
        if self.audio_ref is not None:
            data["audio_ref"] = self.audio_ref
        return data


@dataclass(frozen=True)
class BackendStatus:
    backend: str
    available: bool
    fail_fast: bool
    fallback: str | None
    blocker: str | None

    def __post_init__(self) -> None:
        _require_non_empty_str("backend", self.backend)
        _require_bool("available", self.available)
        _require_bool("fail_fast", self.fail_fast)
        if self.fallback is not None:
            _require_non_empty_str("fallback", self.fallback)
        if self.blocker is not None:
            _require_non_empty_str("blocker", self.blocker)
        if not self.available and not self.fail_fast and self.fallback is None:
            raise ContractValidationError(
                "fallback is required when backend is unavailable and fail_fast is false"
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BackendStatus:
        return cls(
            backend=data["backend"],
            available=data["available"],
            fail_fast=data["fail_fast"],
            fallback=data.get("fallback"),
            blocker=data.get("blocker"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "available": self.available,
            "fail_fast": self.fail_fast,
            "fallback": self.fallback,
            "blocker": self.blocker,
        }


@dataclass(frozen=True)
class CorrectionTrace:
    segment_id: str
    original_text: str
    corrected_text: str
    applied_rule_ids: list[str]
    backend_status: BackendStatus

    def __post_init__(self) -> None:
        _require_non_empty_str("segment_id", self.segment_id)
        _require_str("original_text", self.original_text)
        _require_str("corrected_text", self.corrected_text)
        if not isinstance(self.applied_rule_ids, list) or not all(
            isinstance(rule_id, str) and rule_id for rule_id in self.applied_rule_ids
        ):
            raise ContractValidationError("applied_rule_ids must be a list of strings")
        if not isinstance(self.backend_status, BackendStatus):
            raise ContractValidationError("backend_status must be a BackendStatus")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CorrectionTrace:
        return cls(
            segment_id=data["segment_id"],
            original_text=data["original_text"],
            corrected_text=data["corrected_text"],
            applied_rule_ids=list(data["applied_rule_ids"]),
            backend_status=BackendStatus.from_dict(data["backend_status"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "original_text": self.original_text,
            "corrected_text": self.corrected_text,
            "applied_rule_ids": list(self.applied_rule_ids),
            "backend_status": self.backend_status.to_dict(),
        }


@dataclass(frozen=True)
class CorrectionRule:
    rule_id: str
    wrong: str
    right: str
    mode: str
    enabled: bool
    priority: int
    cost: float
    left_context: str = ""
    right_context: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        _require_non_empty_str("rule_id", self.rule_id)
        _require_non_empty_str("wrong", self.wrong)
        _require_non_empty_str("right", self.right)
        if self.mode not in {"obligatory", "optional", "disabled"}:
            raise ContractValidationError(
                "mode must be one of obligatory, optional, disabled"
            )
        _require_bool("enabled", self.enabled)
        _require_int("priority", self.priority, minimum=0)
        _require_number("cost", self.cost, minimum=0.0)
        _require_str("source", self.source)
        if self.left_context:
            raise ContractValidationError(
                "left_context is reserved in MVP and must be empty"
            )
        if self.right_context:
            raise ContractValidationError(
                "right_context is reserved in MVP and must be empty"
            )


def dedupe_hypotheses(hypotheses: list[Hypothesis]) -> list[Hypothesis]:
    best_by_text: dict[str, Hypothesis] = {}
    for hypothesis in hypotheses:
        current = best_by_text.get(hypothesis.normalized_text)
        if current is None or (hypothesis.asr_cost, hypothesis.rank) < (
            current.asr_cost,
            current.rank,
        ):
            best_by_text[hypothesis.normalized_text] = hypothesis
    return sorted(best_by_text.values(), key=lambda hypothesis: hypothesis.rank)


def _require_str(name: str, value: object) -> None:
    if not isinstance(value, str):
        raise ContractValidationError(f"{name} must be a string")


def _require_non_empty_str(name: str, value: object) -> None:
    _require_str(name, value)
    if not value:
        raise ContractValidationError(f"{name} must be non-empty")


def _require_bool(name: str, value: object) -> None:
    if not isinstance(value, bool):
        raise ContractValidationError(f"{name} must be a bool")


def _require_int(name: str, value: object, *, minimum: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ContractValidationError(f"{name} must be an int")
    if value < minimum:
        raise ContractValidationError(f"{name} must be >= {minimum}")


def _require_number(name: str, value: object, *, minimum: float | None = None) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ContractValidationError(f"{name} must be a number")
    if not math.isfinite(value):
        raise ContractValidationError(f"{name} must be finite")
    if minimum is not None and value < minimum:
        raise ContractValidationError(f"{name} must be >= {minimum}")


def _require_optional_number(name: str, value: object) -> None:
    if value is not None:
        _require_number(name, value)


__all__ = [
    "BackendStatus",
    "ContractValidationError",
    "CorrectionRule",
    "CorrectionTrace",
    "Hypothesis",
    "NBestArtifact",
    "dedupe_hypotheses",
]
