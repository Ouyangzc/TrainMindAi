"""MMR retrieval diversity tests."""

from app.services.retrieval import _cosine_similarity, mmr_diversify


def test_cosine_similarity_handles_zero_vectors() -> None:
    assert _cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
    assert _cosine_similarity([1.0], [1.0, 0.0]) == 0.0


def test_mmr_diversify_prefers_relevant_but_distinct_chunks() -> None:
    items = [
        {"chunk_id": 1, "final_score": 0.90},
        {"chunk_id": 2, "final_score": 0.89},
        {"chunk_id": 3, "final_score": 0.70},
    ]
    embeddings = {
        1: [1.0, 0.0],
        2: [0.99, 0.01],
        3: [0.0, 1.0],
    }

    diversified = mmr_diversify(items, embeddings, lambda_param=0.5, top_k=2)

    assert [item["chunk_id"] for item in diversified] == [1, 3]
    assert all("rerank_score" in item for item in diversified)


def test_mmr_diversify_keeps_original_order_without_embeddings() -> None:
    items = [
        {"chunk_id": 1, "final_score": 0.90},
        {"chunk_id": 2, "final_score": 0.89},
        {"chunk_id": 3, "final_score": 0.70},
    ]

    diversified = mmr_diversify(items, {}, top_k=2)

    assert [item["chunk_id"] for item in diversified] == [1, 2]
