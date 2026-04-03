"""
Rabin–Karp String Matching Algorithm with Rolling Hash.

Useful for multi-pattern matching scenarios (e.g., scanning a resume for
multiple certification names simultaneously).

Rolling Hash Explanation:
    The Rabin–Karp algorithm uses a polynomial rolling hash to avoid
    recomputing the hash of every substring from scratch. For a string
    s[0..m-1], the hash is computed as:

        hash(s) = (s[0] * BASE^(m-1) + s[1] * BASE^(m-2) + ... + s[m-1]) mod PRIME

    When sliding the window one character to the right (removing s[i] and
    adding s[i+m]), the new hash is computed in O(1):

        new_hash = (BASE * (old_hash - s[i] * BASE^(m-1)) + s[i+m]) mod PRIME

    This avoids the O(m) cost of rehashing, making the average case O(n+m).
    Worst case O(nm) occurs when all hash comparisons produce spurious hits
    (e.g., searching "aaaa" in "aaaaa...a"), requiring character-by-character
    verification after every hash match.

Time Complexity:
    - rabin_karp_search:       O(n + m) average, O(n * m) worst case
    - rabin_karp_multi_search: O(n * k) average where k = number of patterns

Space Complexity: O(1) auxiliary for single search, O(k) for multi-search.

Constants:
    BASE  = 256 (covers extended ASCII character set)
    PRIME = 101 (small prime for modular arithmetic to reduce collisions)
"""

from __future__ import annotations

BASE: int = 256
PRIME: int = 101


def rabin_karp_search(text: str, pattern: str) -> list[int]:
    """
    Find all occurrences of `pattern` in `text` using Rabin-Karp.

    Case-insensitive matching with rolling hash.

    Args:
        text:    The text to search within.
        pattern: The pattern to search for.

    Returns:
        List of starting indices (0-based) where pattern is found.

    Examples:
        >>> rabin_karp_search("AABAACAADAABAABA", "AABA")
        [0, 9, 12]
        >>> rabin_karp_search("hello world", "xyz")
        []
    """
    if not text or not pattern:
        return []

    text_lower = text.lower()
    pattern_lower = pattern.lower()

    n = len(text_lower)
    m = len(pattern_lower)

    if m > n:
        return []

    matches: list[int] = []

    # Precompute BASE^(m-1) mod PRIME for leading digit removal
    h = pow(BASE, m - 1, PRIME)

    # Compute initial hash values for pattern and first window of text
    pattern_hash = 0
    text_hash = 0

    for i in range(m):
        pattern_hash = (BASE * pattern_hash + ord(pattern_lower[i])) % PRIME
        text_hash = (BASE * text_hash + ord(text_lower[i])) % PRIME

    # Slide the window over text
    for i in range(n - m + 1):
        # If hash values match, verify character by character
        if pattern_hash == text_hash:
            if text_lower[i:i + m] == pattern_lower:
                matches.append(i)

        # Compute hash for next window (if not at the last position)
        if i < n - m:
            # Remove leading character, add trailing character
            text_hash = (
                BASE * (text_hash - ord(text_lower[i]) * h)
                + ord(text_lower[i + m])
            ) % PRIME

            # Handle negative modulo (Python handles it, but be explicit)
            if text_hash < 0:
                text_hash += PRIME

    return matches


def rabin_karp_multi_search(text: str, patterns: list[str]) -> dict[str, bool]:
    """
    Check presence of multiple patterns in text using Rabin-Karp.

    Optimized for the common case of checking many short patterns
    (skill names, certifications) against a single document.

    Args:
        text:     The text to search within.
        patterns: List of patterns to search for.

    Returns:
        Dict mapping each pattern (original case) to whether it was found.

    Examples:
        >>> result = rabin_karp_multi_search("Python and Java developer", ["python", "java", "rust"])
        >>> result
        {'python': True, 'java': True, 'rust': False}
    """
    if not text:
        return {p: False for p in patterns}

    text_lower = text.lower()
    results: dict[str, bool] = {}

    # Group patterns by length to share rolling hash computation
    length_groups: dict[int, list[str]] = {}
    for pattern in patterns:
        m = len(pattern)
        if m == 0:
            results[pattern] = False
            continue
        length_groups.setdefault(m, []).append(pattern)

    n = len(text_lower)

    for m, group in length_groups.items():
        if m > n:
            for pattern in group:
                results[pattern] = False
            continue

        # Precompute BASE^(m-1) mod PRIME
        h = pow(BASE, m - 1, PRIME)

        # Build hash set for all patterns of this length
        pattern_hashes: dict[int, list[str]] = {}
        for pattern in group:
            p_lower = pattern.lower()
            p_hash = 0
            for ch in p_lower:
                p_hash = (BASE * p_hash + ord(ch)) % PRIME
            pattern_hashes.setdefault(p_hash, []).append(pattern)
            results[pattern] = False  # default

        # Compute initial text window hash
        text_hash = 0
        for i in range(m):
            text_hash = (BASE * text_hash + ord(text_lower[i])) % PRIME

        # Slide window
        for i in range(n - m + 1):
            if text_hash in pattern_hashes:
                window = text_lower[i:i + m]
                for pattern in pattern_hashes[text_hash]:
                    if window == pattern.lower():
                        results[pattern] = True

            # Roll hash forward
            if i < n - m:
                text_hash = (
                    BASE * (text_hash - ord(text_lower[i]) * h)
                    + ord(text_lower[i + m])
                ) % PRIME
                if text_hash < 0:
                    text_hash += PRIME

    return results
