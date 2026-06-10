"""HireIQ Engine — Intelligence layer for candidate scoring and verification."""

from engine.claim_verifier import verify_claims
from engine.score_fusion import (
    compute_full_candidate_score,
    generate_recommendations,
)
from engine.bias_auditor import (
    create_blind_features,
    audit_bias,
    run_batch_bias_audit,
)
from engine.skill_confidence import compute_skill_confidence
from engine.ranker import compute_composite_rank_score
from engine.matcher import compute_match_breakdown

__all__ = [
    "verify_claims",
    "compute_full_candidate_score",
    "generate_recommendations",
    "create_blind_features",
    "audit_bias",
    "run_batch_bias_audit",
    "compute_skill_confidence",
    "compute_composite_rank_score",
    "compute_match_breakdown",
]
