from algorithms.interview_scheduler import schedule_interviews

def test_schedule_no_overlap():
    candidates = [
        {"name": "Alice", "start_time": 9, "end_time": 10},
        {"name": "Bob", "start_time": 10, "end_time": 11},
        {"name": "Diana", "start_time": 11, "end_time": 12}
    ]
    res = schedule_interviews(candidates)
    assert res["total_slots"] == 3
    assert [c[0] for c in res["slots"]] == ["Alice", "Bob", "Diana"]

def test_schedule_with_overlaps():
    candidates = [
        {"name": "Alice", "start_time": 9, "end_time": 10},
        {"name": "Bob", "start_time": 10, "end_time": 12},
        {"name": "Charlie", "start_time": 9, "end_time": 11}, # overlaps Alice and Bob
        {"name": "Diana", "start_time": 11, "end_time": 12}, # overlaps Bob
        {"name": "Eve", "start_time": 12, "end_time": 13}
    ]
    res = schedule_interviews(candidates)
    # Alice (9-10), Diana (11-12) or Bob (10-12) can be scheduled, plus Eve (12-13).
    # Since it sorts by end_time:
    # 1. Alice (end 10) selected. last_end = 10.
    # 2. Charlie (end 11) - start 9 < last_end (10) -> skip.
    # 3. Bob (end 12) - start 10 >= last_end (10) -> select. last_end = 12.
    # 4. Diana (end 12) - start 11 < last_end (12) -> skip.
    # 5. Eve (end 13) - start 12 >= last_end (12) -> select. last_end = 13.
    # Total slots should be 3: Alice, Bob, Eve.
    assert res["total_slots"] == 3
    assert [c[0] for c in res["slots"]] == ["Alice", "Bob", "Eve"]

def test_schedule_empty():
    res = schedule_interviews([])
    assert res["total_slots"] == 0
    assert len(res["slots"]) == 0
