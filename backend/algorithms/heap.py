"""
CandidateHeap — Max-Heap–based Candidate Ranking.

Uses Python's heapq (a min-heap) with negated scores to achieve max-heap
behavior, allowing efficient retrieval of top-K candidates.

Complexity:
    - push():           O(log n)
    - pop():            O(log n)
    - top_k(k):         O(k log n)
    - get_all_ranked(): O(n log n)
    - peek():           O(1)
    - __len__():        O(1)

Space Complexity: O(n) where n = number of candidates.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class _HeapEntry:
    """
    Internal heap entry with negated score for max-heap behavior.

    The `order=True` on the dataclass generates comparison methods
    based on field order. Since `neg_score` is first, heapq sorts
    by negated score (most negative = highest original score = first out).

    The `seq` field breaks ties in FIFO order (first pushed = first out
    when scores are equal), ensuring stable ordering.
    """
    neg_score: float
    seq: int = field(compare=True)
    name: str = field(compare=False)
    data: dict[str, Any] = field(compare=False, default_factory=dict)


class CandidateHeap:
    """
    A max-heap for ranking candidates by composite score.

    Wraps Python's heapq (min-heap) with score negation so that
    pop() always returns the highest-scoring candidate.

    Usage:
        >>> heap = CandidateHeap()
        >>> heap.push(85.5, "Alice", {"role": "SDE"})
        >>> heap.push(92.3, "Bob", {"role": "SDE"})
        >>> heap.push(78.0, "Charlie", {"role": "SDE"})
        >>> top = heap.pop()
        >>> top  # Bob with 92.3
        (92.3, 'Bob', {'role': 'SDE'})
    """

    def __init__(self) -> None:
        self._heap: list[_HeapEntry] = []
        self._counter: int = 0  # sequence counter for tie-breaking

    def push(self, score: float, name: str, data: dict[str, Any] | None = None) -> None:
        """
        Add a candidate to the heap.

        Args:
            score: The candidate's composite score (higher = better).
            name:  Candidate identifier (name or ID).
            data:  Arbitrary metadata dict.

        Complexity: O(log n)
        """
        entry = _HeapEntry(
            neg_score=-score,
            seq=self._counter,
            name=name,
            data=data or {},
        )
        heapq.heappush(self._heap, entry)
        self._counter += 1

    def pop(self) -> tuple[float, str, dict[str, Any]]:
        """
        Remove and return the highest-scoring candidate.

        Returns:
            Tuple of (score, name, data).

        Raises:
            IndexError: If the heap is empty.

        Complexity: O(log n)
        """
        if not self._heap:
            raise IndexError("pop from empty CandidateHeap")
        entry = heapq.heappop(self._heap)
        return (-entry.neg_score, entry.name, entry.data)

    def peek(self) -> tuple[float, str, dict[str, Any]]:
        """
        Return the highest-scoring candidate without removing it.

        Returns:
            Tuple of (score, name, data).

        Raises:
            IndexError: If the heap is empty.

        Complexity: O(1)
        """
        if not self._heap:
            raise IndexError("peek on empty CandidateHeap")
        entry = self._heap[0]
        return (-entry.neg_score, entry.name, entry.data)

    def top_k(self, k: int) -> list[tuple[float, str, dict[str, Any]]]:
        """
        Return the top-k highest-scoring candidates.

        Non-destructive: the heap is NOT modified. Uses heapq.nsmallest
        on the negated-score heap (smallest negated = highest original).

        Args:
            k: Number of top candidates to return.

        Returns:
            List of (score, name, data) tuples, sorted by score descending.

        Complexity: O(k log n)

        Examples:
            >>> heap = CandidateHeap()
            >>> for s, n in [(90, "A"), (85, "B"), (95, "C"), (70, "D")]:
            ...     heap.push(s, n)
            >>> heap.top_k(2)
            [(95, 'C', {}), (90, 'A', {})]
        """
        k = min(k, len(self._heap))
        if k <= 0:
            return []

        top_entries = heapq.nsmallest(k, self._heap)
        return [(-e.neg_score, e.name, e.data) for e in top_entries]

    def get_all_ranked(self) -> list[tuple[float, str, dict[str, Any]]]:
        """
        Return ALL candidates ranked by score descending.

        Non-destructive: works on a copy of the heap.

        Returns:
            List of (score, name, data) tuples, sorted by score descending.

        Complexity: O(n log n)
        """
        sorted_entries = sorted(self._heap)
        return [(-e.neg_score, e.name, e.data) for e in sorted_entries]

    def merge(self, other: "CandidateHeap") -> None:
        """
        Merge another CandidateHeap into this one.

        After merge, `other` is unchanged. Duplicate names are allowed
        (caller should deduplicate if needed).

        Args:
            other: Another CandidateHeap to merge from.

        Complexity: O(m log(n + m)) where m = len(other)
        """
        for entry in other._heap:
            new_entry = _HeapEntry(
                neg_score=entry.neg_score,
                seq=self._counter,
                name=entry.name,
                data=entry.data.copy(),
            )
            heapq.heappush(self._heap, new_entry)
            self._counter += 1

    def clear(self) -> None:
        """Remove all candidates from the heap."""
        self._heap.clear()
        self._counter = 0

    def __len__(self) -> int:
        """Return number of candidates in the heap. O(1)."""
        return len(self._heap)

    def __bool__(self) -> bool:
        """Return True if heap is non-empty."""
        return bool(self._heap)

    def __repr__(self) -> str:
        return f"CandidateHeap(size={len(self._heap)})"
