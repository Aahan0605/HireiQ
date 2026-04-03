"""
Knuth–Morris–Pratt (KMP) String Matching Algorithm.

Used for efficient skill keyword detection in resumes and job descriptions.

Time Complexity:
    - build_failure_function: O(m) where m = len(pattern)
    - kmp_search:             O(n + m) where n = len(text)
    - kmp_contains:           O(n + m) — early exit on first match

Space Complexity: O(m) for the failure/prefix table.

Why KMP over naive search?
    Resume parsing involves searching for 80+ skill patterns across
    potentially long documents. KMP avoids redundant character comparisons
    by leveraging the failure function, making batch skill detection linear.
"""

from __future__ import annotations


def build_failure_function(pattern: str) -> list[int]:
    """
    Build the KMP failure (partial match / prefix) table.

    failure[i] = length of the longest proper prefix of pattern[0..i]
                 that is also a suffix of pattern[0..i].

    Args:
        pattern: The search pattern string.

    Returns:
        A list of integers representing the failure function.
    """
    m = len(pattern)
    if m == 0:
        return []

    failure = [0] * m
    j = 0  # length of previous longest prefix-suffix
    i = 1

    while i < m:
        if pattern[i] == pattern[j]:
            j += 1
            failure[i] = j
            i += 1
        else:
            if j != 0:
                j = failure[j - 1]
            else:
                failure[i] = 0
                i += 1

    return failure


def kmp_search(text: str, pattern: str) -> list[int]:
    """
    Find all occurrences of `pattern` in `text` using KMP.

    Case-insensitive matching. Returns starting indices of all matches.

    Args:
        text:    The text to search within.
        pattern: The pattern to search for.

    Returns:
        List of starting indices (0-based) where pattern is found.

    Examples:
        >>> kmp_search("Python is great. I love python.", "python")
        [0, 25]
        >>> kmp_search("AABAACAADAABAABA", "AABA")
        [0, 9, 12]
    """
    if not pattern or not text:
        return []

    text_lower = text.lower()
    pattern_lower = pattern.lower()

    n = len(text_lower)
    m = len(pattern_lower)

    if m > n:
        return []

    failure = build_failure_function(pattern_lower)
    matches: list[int] = []

    i = 0  # index in text
    j = 0  # index in pattern

    while i < n:
        if text_lower[i] == pattern_lower[j]:
            i += 1
            j += 1

            if j == m:
                matches.append(i - j)
                j = failure[j - 1]
        else:
            if j != 0:
                j = failure[j - 1]
            else:
                i += 1

    return matches


def kmp_contains(text: str, pattern: str) -> bool:
    """
    Check if `pattern` exists in `text` using KMP.

    Case-insensitive. Short-circuits on first match for efficiency.

    Args:
        text:    The text to search within.
        pattern: The pattern to search for.

    Returns:
        True if pattern is found, False otherwise.

    Examples:
        >>> kmp_contains("Experienced in React and Node.js", "react")
        True
        >>> kmp_contains("Experienced in React and Node.js", "angular")
        False
    """
    if not pattern or not text:
        return False

    text_lower = text.lower()
    pattern_lower = pattern.lower()

    n = len(text_lower)
    m = len(pattern_lower)

    if m > n:
        return False

    failure = build_failure_function(pattern_lower)

    i = 0
    j = 0

    while i < n:
        if text_lower[i] == pattern_lower[j]:
            i += 1
            j += 1

            if j == m:
                return True
        else:
            if j != 0:
                j = failure[j - 1]
            else:
                i += 1

    return False


def kmp_search_all_patterns(text: str, patterns: list[str]) -> dict[str, list[int]]:
    """
    Search for multiple patterns in a single text.

    Args:
        text:     The text to search within.
        patterns: List of patterns to search for.

    Returns:
        Dict mapping each pattern to its list of match indices.

    Examples:
        >>> result = kmp_search_all_patterns("Python and Java", ["python", "java", "rust"])
        >>> result["python"]
        [0]
        >>> result["java"]
        [11]
        >>> result["rust"]
        []
    """
    return {pattern: kmp_search(text, pattern) for pattern in patterns}
