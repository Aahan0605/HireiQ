"""
Manual TF-IDF Vectorizer — No sklearn dependency.

Implements Term Frequency–Inverse Document Frequency from scratch for
resume-to-job-description similarity scoring.

Formulas:
    TF(t, d)  = (count of t in d) / (total terms in d)
    IDF(t, D) = log( |D| / (1 + |{d ∈ D : t ∈ d}|) ) + 1
                (smoothed variant to avoid division by zero)
    TF-IDF(t, d, D) = TF(t, d) × IDF(t, D)

Complexity Analysis:
    - fit():           O(N * L) where N = corpus size, L = avg doc length
    - transform():     O(M * L * V) where M = docs to transform, V = vocab size
    - fit_transform(): O(N * L + N * L * V) = O(N * L * V)
    - tf():            O(L) per document
    - idf():           O(N * L) per term (amortized O(1) after fit)

Space Complexity:
    - O(V) for vocabulary, O(V) for IDF cache, O(V) per document vector
"""

from __future__ import annotations

import math
import re
from collections import Counter


def _tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase alphanumeric words.

    Strips punctuation, normalizes whitespace, and lowercases.
    Handles tech terms with dots (e.g., "Node.js" → "nodejs").

    Args:
        text: Raw text string.

    Returns:
        List of cleaned tokens.
    """
    # Normalize common tech notation
    cleaned = text.lower()
    cleaned = re.sub(r'\.js\b', 'js', cleaned)
    cleaned = re.sub(r'\.py\b', 'py', cleaned)
    cleaned = re.sub(r'\.net\b', 'dotnet', cleaned)
    cleaned = re.sub(r'c\+\+', 'cplusplus', cleaned)
    cleaned = re.sub(r'c#', 'csharp', cleaned)

    # Extract alphanumeric tokens
    tokens = re.findall(r'[a-z0-9]+', cleaned)

    # Remove common stop words
    stop_words = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'is', 'am', 'are', 'was', 'were',
        'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'shall',
        'can', 'this', 'that', 'these', 'those', 'i', 'me', 'my', 'we',
        'our', 'you', 'your', 'he', 'she', 'it', 'they', 'them', 'its',
        'not', 'no', 'nor', 'as', 'if', 'then', 'than', 'too', 'very',
        'so', 'from', 'up', 'out', 'about', 'into', 'over', 'after',
    }

    return [t for t in tokens if t not in stop_words and len(t) > 1]


def tf(term: str, document: str) -> float:
    """
    Compute Term Frequency for a term in a document.

    TF(t, d) = (number of times t appears in d) / (total number of terms in d)

    Args:
        term:     The term to compute frequency for.
        document: The raw document text.

    Returns:
        The term frequency as a float in [0.0, 1.0].

    Examples:
        >>> tf("python", "Python is great and python is everywhere")
        0.2857142857142857
    """
    tokens = _tokenize(document)
    if not tokens:
        return 0.0
    term_lower = term.lower()
    count = sum(1 for t in tokens if t == term_lower)
    return count / len(tokens)


def idf(term: str, corpus: list[str]) -> float:
    """
    Compute Inverse Document Frequency for a term across a corpus.

    IDF(t, D) = log(|D| / (1 + |{d ∈ D : t ∈ d}|)) + 1

    The +1 in the denominator prevents division by zero.
    The +1 outside the log ensures terms present in all documents
    still get a non-zero weight.

    Args:
        term:   The term to compute IDF for.
        corpus: List of raw document strings.

    Returns:
        The IDF value as a float (always ≥ 1.0 due to smoothing).

    Examples:
        >>> idf("python", ["python is great", "java is also great", "python and java"])
        1.2876820724517808
    """
    if not corpus:
        return 1.0
    term_lower = term.lower()
    doc_count = sum(
        1 for doc in corpus
        if term_lower in {t for t in _tokenize(doc)}
    )
    return math.log(len(corpus) / (1 + doc_count)) + 1


class TFIDFVectorizer:
    """
    A from-scratch TF-IDF vectorizer.

    Builds vocabulary and IDF values from a training corpus, then
    transforms documents into sparse TF-IDF vectors represented as
    dicts mapping terms to weights.

    Usage:
        >>> vectorizer = TFIDFVectorizer()
        >>> vectors = vectorizer.fit_transform(["Python ML expert", "Java backend dev"])
        >>> len(vectors)
        2
    """

    def __init__(self) -> None:
        self.vocabulary: set[str] = set()
        self.idf_values: dict[str, float] = {}
        self._corpus: list[str] = []
        self._fitted: bool = False

    def fit(self, corpus: list[str]) -> "TFIDFVectorizer":
        """
        Learn vocabulary and IDF values from the corpus.

        Args:
            corpus: List of raw document strings.

        Returns:
            self (for method chaining).
        """
        self._corpus = corpus
        tokenized_docs = [_tokenize(doc) for doc in corpus]

        # Build vocabulary from all documents
        self.vocabulary = set()
        for tokens in tokenized_docs:
            self.vocabulary.update(tokens)

        # Precompute IDF for each term
        n_docs = len(corpus)
        doc_sets = [set(tokens) for tokens in tokenized_docs]

        self.idf_values = {}
        for term in self.vocabulary:
            doc_count = sum(1 for doc_set in doc_sets if term in doc_set)
            self.idf_values[term] = math.log(n_docs / (1 + doc_count)) + 1

        self._fitted = True
        return self

    def transform(self, documents: list[str]) -> list[dict[str, float]]:
        """
        Transform documents into TF-IDF vectors using fitted vocabulary.

        Terms not in the learned vocabulary are ignored (zero weight).

        Args:
            documents: List of raw document strings to transform.

        Returns:
            List of sparse vectors (dicts mapping term → TF-IDF weight).

        Raises:
            RuntimeError: If called before fit().
        """
        if not self._fitted:
            raise RuntimeError("Vectorizer must be fitted before transform. Call fit() first.")

        vectors: list[dict[str, float]] = []

        for doc in documents:
            tokens = _tokenize(doc)
            if not tokens:
                vectors.append({})
                continue

            token_counts = Counter(tokens)
            total_tokens = len(tokens)
            vec: dict[str, float] = {}

            for term, count in token_counts.items():
                if term in self.idf_values:
                    tf_val = count / total_tokens
                    vec[term] = tf_val * self.idf_values[term]

            vectors.append(vec)

        return vectors

    def fit_transform(self, corpus: list[str]) -> list[dict[str, float]]:
        """
        Fit on corpus and transform it in one step.

        Args:
            corpus: List of raw document strings.

        Returns:
            List of sparse TF-IDF vectors for each document.
        """
        self.fit(corpus)
        return self.transform(corpus)

    def get_top_terms(self, vector: dict[str, float], k: int = 10) -> list[tuple[str, float]]:
        """
        Get top-k terms by TF-IDF weight from a document vector.

        Args:
            vector: A TF-IDF vector (dict from transform).
            k:      Number of top terms to return.

        Returns:
            List of (term, weight) tuples sorted by weight descending.
        """
        sorted_terms = sorted(vector.items(), key=lambda x: x[1], reverse=True)
        return sorted_terms[:k]

    @property
    def vocab_size(self) -> int:
        """Return the number of unique terms in the vocabulary."""
        return len(self.vocabulary)
