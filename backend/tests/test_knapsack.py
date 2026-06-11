from algorithms.dp_shortlist import select_candidates

def test_knapsack_basic():
    candidates = [
        {"name": "Alice", "score": 85, "cost": 2},
        {"name": "Bob", "score": 90, "cost": 3},
        {"name": "Charlie", "score": 75, "cost": 1},
        {"name": "Diana", "score": 88, "cost": 2},
        {"name": "Eve", "score": 92, "cost": 4},
    ]
    budget = 6
    res = select_candidates(candidates, budget)
    # With budget 6:
    # Charlie (cost 1, score 75)
    # Alice (cost 2, score 85)
    # Diana (cost 2, score 88)
    # Total cost = 5, total score = 248.
    # Other combo: Bob (3, 90) + Diana (2, 88) + Charlie (1, 75) = cost 6, score 253.
    # Let's verify Bob, Diana, Charlie are selected:
    selected_names = [c["name"] for c in res["selected_candidates"]]
    assert "Bob" in selected_names
    assert "Diana" in selected_names
    assert "Charlie" in selected_names
    assert res["total_score"] == 253
    assert res["budget_used"] <= 6

def test_knapsack_zero_budget():
    candidates = [
        {"name": "Alice", "score": 85, "cost": 2}
    ]
    res = select_candidates(candidates, 0)
    assert res["total_score"] == 0
    assert len(res["selected_candidates"]) == 0
    assert res["budget_used"] == 0
    assert res["budget_remaining"] == 0
