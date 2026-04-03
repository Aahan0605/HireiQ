"""
Dynamic Programming — 0/1 Knapsack Candidate Selection.

Selects candidates to maximize total fusion score within a hiring budget.
Recurrence: dp[i][w] = max(dp[i-1][w], dp[i-1][w-cost[i]] + score[i])

Time: O(n * budget), Space: O(n * budget)
"""


def select_candidates(candidates: list[dict], budget: int) -> dict:
    """
    Select candidates to maximize total score within budget using DP.

    Args:
        candidates: List of dicts with 'name', 'score', 'cost'
        budget: Total hiring budget (cost units)

    Returns: Dict with selected_candidates, total_score, budget used/remaining
    Time: O(n * budget), Space: O(n * budget)
    """
    n = len(candidates)

    # dp[i][w] = max score using first i candidates with budget w
    dp = [[0] * (budget + 1) for _ in range(n + 1)]

    # Fill DP table bottom-up
    for i in range(1, n + 1):
        score = candidates[i - 1]["score"]
        cost = candidates[i - 1]["cost"]

        for w in range(budget + 1):
            # Don't take candidate i
            dp[i][w] = dp[i - 1][w]

            # Take candidate i if budget allows
            # Recurrence: dp[i][w] = max(dp[i-1][w], dp[i-1][w-cost[i]] + score[i])
            if w >= cost:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - cost] + score)

    # Backtrack to find selected candidates
    selected = []
    w = budget
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(candidates[i - 1])
            w -= candidates[i - 1]["cost"]

    return {
        "selected_candidates": selected,
        "total_score": dp[n][budget],
        "budget_used": budget - w,
        "budget_remaining": w,
    }


if __name__ == "__main__":
    # Demo: 5 candidates with scores and hiring costs
    candidates = [
        {"name": "Alice", "score": 85, "cost": 2},
        {"name": "Bob", "score": 90, "cost": 3},
        {"name": "Charlie", "score": 75, "cost": 1},
        {"name": "Diana", "score": 88, "cost": 2},
        {"name": "Eve", "score": 92, "cost": 4},
    ]

    budget = 6
    result = select_candidates(candidates, budget)

    print(f"Budget: {budget}")
    print(f"Selected: {[c['name'] for c in result['selected_candidates']]}")
    print(f"Total Score: {result['total_score']}")
    print(
        f"Budget Used: {result['budget_used']}, Remaining: {result['budget_remaining']}"
    )
