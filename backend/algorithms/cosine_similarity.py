"""
Cosine Similarity — Manual Implementation (no numpy).

Computes the cosine of the angle between two sparse vectors represented
as dicts. Used to measure similarity between TF-IDF vectors of resumes
and job descriptions.

Formula:
    cosine_similarity(A, B) = (A · B) / (‖A‖ × ‖B‖)

    where:
        A · B   = Σ (A[i] × B[i])     for all shared keys
        ‖A‖     = √( Σ A[i]² )         L2 norm
        ‖B‖     = √( Σ B[i]² )         L2 norm

    Result is in [-1.0, 1.0] for general vectors,
    or [0.0, 1.0] for TF-IDF vectors (all non-negative).

Time Complexity:
    - cosine_similarity:       O(min(|A|, |B|)) for sparse vectors
    - batch_cosine_similarity: O(k × min(|Q|, |D_i|)) where k = number of docs

Space Complexity: O(1) auxiliary.
"""

from __future__ import annotations

import math


def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """
    Compute cosine similarity between two sparse vectors.

    Vectors are represented as dicts mapping dimension names (terms) to
    their weights. Only shared keys contribute to the dot product.

    Args:
        vec_a: First sparse vector {term: weight}.
        vec_b: Second sparse vector {term: weight}.

    Returns:
        Cosine similarity in [0.0, 1.0] for non-negative vectors.
        Returns 0.0 if either vector is empty or has zero magnitude.

    Examples:
        >>> cosine_similarity({"python": 0.5, "ml": 0.3}, {"python": 0.4, "ml": 0.6})
        0.8320502943378437
        >>> cosine_similarity({"python": 1.0}, {"java": 1.0})
        0.0
        >>> cosine_similarity({}, {"python": 1.0})
        0.0
    """
    if not vec_a or not vec_b:
        return 0.0

    # Use the smaller vector for iteration (optimization for sparse vectors)
    if len(vec_a) > len(vec_b):
        vec_a, vec_b = vec_b, vec_a

    # Dot product — only iterate shared keys
    dot_product = 0.0
    for key, val_a in vec_a.items():
        if key in vec_b:
            dot_product += val_a * vec_b[key]

    if dot_product == 0.0:
        return 0.0

    # L2 norms
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    similarity = dot_product / (norm_a * norm_b)

    # Clamp to [0.0, 1.0] to handle floating point edge cases
    return max(0.0, min(1.0, similarity))


def batch_cosine_similarity(
    query_vec: dict[str, float],
    doc_vecs: list[dict[str, float]],
) -> list[float]:
    """
    Compute cosine similarity between a query vector and multiple document vectors.

    Useful for ranking all candidates against a single job description.

    Args:
        query_vec: The query (job description) TF-IDF vector.
        doc_vecs:  List of document (resume) TF-IDF vectors.

    Returns:
        List of cosine similarity scores, one per document, in the same order.

    Examples:
        >>> q = {"python": 0.5, "ml": 0.3}
        >>> docs = [{"python": 0.8}, {"java": 0.9}, {"python": 0.3, "ml": 0.7}]
        >>> scores = batch_cosine_similarity(q, docs)
        >>> len(scores)
        3
    """
    if not query_vec:
        return [0.0] * len(doc_vecs)

    # Precompute query norm (shared across all comparisons)
    query_norm = math.sqrt(sum(v * v for v in query_vec.values()))
    if query_norm == 0.0:
        return [0.0] * len(doc_vecs)

    scores: list[float] = []

    for doc_vec in doc_vecs:
        if not doc_vec:
            scores.append(0.0)
            continue

        # Dot product
        dot = 0.0
        for key, val_q in query_vec.items():
            if key in doc_vec:
                dot += val_q * doc_vec[key]

        if dot == 0.0:
            scores.append(0.0)
            continue

        doc_norm = math.sqrt(sum(v * v for v in doc_vec.values()))
        if doc_norm == 0.0:
            scores.append(0.0)
            continue

        sim = dot / (query_norm * doc_norm)
        scores.append(max(0.0, min(1.0, sim)))

    return scores


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """
    Compute Jaccard similarity between two sets.

    Useful as a secondary similarity metric for skill-set overlap.

    J(A, B) = |A ∩ B| / |A ∪ B|

    Args:
        set_a: First set of items.
        set_b: Second set of items.

    Returns:
        Jaccard index in [0.0, 1.0].

    Examples:
        >>> jaccard_similarity({"python", "java"}, {"python", "go"})
        0.3333333333333333
    """
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0
