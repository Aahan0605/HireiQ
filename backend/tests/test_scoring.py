from algorithms.cosine_similarity import cosine_similarity, batch_cosine_similarity, jaccard_similarity

def test_cosine_similarity_exact():
    vec_a = {"python": 0.5, "ml": 0.3}
    vec_b = {"python": 0.4, "ml": 0.6}
    # (0.5*0.4 + 0.3*0.6) / (sqrt(0.25+0.09) * sqrt(0.16+0.36))
    # = (0.2 + 0.18) / (sqrt(0.34) * sqrt(0.52))
    # = 0.38 / (0.583095189 * 0.721110255)
    # = 0.38 / 0.42047592
    # = 0.903737
    sim = cosine_similarity(vec_a, vec_b)
    assert round(sim, 4) == 0.9037

def test_cosine_similarity_empty():
    assert cosine_similarity({}, {"python": 1.0}) == 0.0
    assert cosine_similarity({"python": 1.0}, {}) == 0.0
    assert cosine_similarity({}, {}) == 0.0

def test_cosine_similarity_no_overlap():
    assert cosine_similarity({"python": 1.0}, {"java": 1.0}) == 0.0

def test_batch_cosine_similarity():
    q = {"python": 0.5, "ml": 0.3}
    docs = [
        {"python": 0.8},
        {"java": 0.9},
        {"python": 0.3, "ml": 0.7}
    ]
    scores = batch_cosine_similarity(q, docs)
    assert len(scores) == 3
    assert scores[0] > 0.0
    assert scores[1] == 0.0
    assert scores[2] > 0.0

def test_jaccard_similarity():
    assert jaccard_similarity({"python", "java"}, {"python", "go"}) == 1/3
    assert jaccard_similarity(set(), {"python"}) == 0.0
    assert jaccard_similarity(set(), set()) == 0.0
