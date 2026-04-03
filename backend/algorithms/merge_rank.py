"""
Divide & Conquer — Merge Sort with Rank Delta Tracking.

Sorts candidates by fusion score and tracks position change (rank_delta).
Merge sort splits problem in half recursively, then merges sorted halves.

Time: O(n log n), Space: O(n)
"""


def merge_sort_candidates(candidates):
    """
    Merge sort candidates by fusion_score, add rank_delta field.

    Args:
        candidates: List of candidate dicts with 'name', 'fusion_score'

    Returns: Sorted list with rank_delta and final_rank fields added
    Time: O(n log n), Space: O(n)
    """
    # Store original indices to track rank changes
    indexed = [(i, c) for i, c in enumerate(candidates)]

    def merge_sort(arr):
        """Recursive merge sort helper."""
        if len(arr) <= 1:
            return arr

        mid = len(arr) // 2
        left = merge_sort(arr[:mid])
        right = merge_sort(arr[mid:])

        return merge(left, right)

    def merge(left, right):
        """Merge two sorted halves, sorting by fusion_score descending."""
        result = []
        i = j = 0

        while i < len(left) and j < len(right):
            # Sort by score descending (higher score = better rank)
            if left[i][1]["fusion_score"] >= right[j][1]["fusion_score"]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1

        result.extend(left[i:])
        result.extend(right[j:])
        return result

    # Run merge sort on indexed candidates
    sorted_indexed = merge_sort(indexed)

    # Add rank_delta: original_index - final_index (positive = moved up)
    result = []
    for final_rank, (original_idx, candidate) in enumerate(sorted_indexed):
        candidate["rank_delta"] = original_idx - final_rank
        candidate["final_rank"] = final_rank + 1
        result.append(candidate)

    return result


if __name__ == "__main__":
    # Demo: 5 candidates with scores
    candidates = [
        {"name": "Alice", "fusion_score": 85},
        {"name": "Bob", "fusion_score": 90},
        {"name": "Charlie", "fusion_score": 75},
        {"name": "Diana", "fusion_score": 88},
        {"name": "Eve", "fusion_score": 92},
    ]

    sorted_candidates = merge_sort_candidates(candidates)

    print("Ranked Candidates (by fusion_score):")
    for c in sorted_candidates:
        delta_str = f"{c['rank_delta']:+d}" if c["rank_delta"] != 0 else "0"
        print(
            f"  Rank {c['final_rank']}: {c['name']} "
            f"(Score: {c['fusion_score']}, Δ: {delta_str})"
        )
