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

__all__ = [
    "verify_claims",
    "compute_full_candidate_score",
    "generate_recommendations",
    "create_blind_features",
    "audit_bias",
    "run_batch_bias_audit",
]
