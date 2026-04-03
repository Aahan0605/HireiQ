"""HireIQ Algorithms — String matching, TF-IDF, similarity, and ranking."""

from algorithms.kmp import kmp_search, kmp_contains, build_failure_function
from algorithms.rabin_karp import rabin_karp_search, rabin_karp_multi_search
from algorithms.tfidf import TFIDFVectorizer, tf, idf
from algorithms.cosine_similarity import cosine_similarity, batch_cosine_similarity, jaccard_similarity
from algorithms.heap import CandidateHeap

__all__ = [
    "kmp_search", "kmp_contains", "build_failure_function",
    "rabin_karp_search", "rabin_karp_multi_search",
    "TFIDFVectorizer", "tf", "idf",
    "cosine_similarity", "batch_cosine_similarity", "jaccard_similarity",
    "CandidateHeap",
]
