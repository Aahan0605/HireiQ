"""
Greedy Algorithm — Interview Scheduling (Activity Selection).

Selects the maximum number of non-overlapping interviews.
Sorts by end time, greedily picks earliest-finishing candidates.

Time: O(n log n) for sorting
Space: O(n)
"""


def schedule_interviews(candidates):
    """
    Select maximum non-overlapping interview slots using greedy activity selection.

    Args:
        candidates: List of dicts with 'name', 'start_time', 'end_time'

    Returns: Dict with selected_interviews, total_slots, slot times
    Time: O(n log n) for sorting, Space: O(n)
    """
    # Sort by end time (greedy choice: earliest finish first)
    sorted_candidates = sorted(candidates, key=lambda x: x["end_time"])

    selected = []
    last_end = -1

    for candidate in sorted_candidates:
        # If candidate's start >= last end, no overlap
        if candidate["start_time"] >= last_end:
            selected.append(candidate)
            last_end = candidate["end_time"]

    return {
        "selected_interviews": selected,
        "total_slots": len(selected),
        "slots": [(c["name"], c["start_time"], c["end_time"]) for c in selected],
    }


if __name__ == "__main__":
    # Demo: 6 candidates with time slots
    candidates = [
        {"name": "Alice", "start_time": 9, "end_time": 10},
        {"name": "Bob", "start_time": 10, "end_time": 11},
        {"name": "Charlie", "start_time": 9, "end_time": 10},  # overlaps Alice
        {"name": "Diana", "start_time": 11, "end_time": 12},
        {"name": "Eve", "start_time": 10, "end_time": 12},
        {"name": "Frank", "start_time": 12, "end_time": 13},
    ]

    result = schedule_interviews(candidates)

    print("Scheduled Interviews:")
    for name, start, end in result["slots"]:
        print(f"  {name}: {start}:00 - {end}:00")
    print(f"Total: {result['total_slots']} interviews scheduled")
