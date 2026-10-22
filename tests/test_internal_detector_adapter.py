"""Synthetic end-to-end checks of production duplicate detection and internal scorer."""

from scripts.internal_detector_adapter import predict_exact_duplicate_pairs
from scripts.score_internal_duplicate_fixtures import evaluate


def gold_pair(a, b, label):
    return {
        "source_id": "synthetic",
        "block_a": str(a),
        "block_b": str(b),
        "label": label,
    }


def test_exact_duplicate_detector_to_scorer():
    texts = [
        "Preserve exact source references in all generated reports.",
        "Avoid inventing data when the source material is incomplete.",
        "Preserve exact source references in all generated reports.",
    ]
    gold = [
        gold_pair(0, 1, "distinct"),
        gold_pair(0, 2, "exact_duplicate"),
        gold_pair(1, 2, "distinct"),
    ]
    predicted = predict_exact_duplicate_pairs("synthetic", texts)
    result = evaluate(gold, predicted)
    assert (result["tp"], result["fp"], result["fn"]) == (1, 0, 0)
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["scope"] == "internal_fixture_only"
    assert result["external_accuracy_claim_permitted"] is False


def test_no_duplicate_predictions():
    texts = [
        "Keep original source files unchanged during the analysis.",
        "Do not execute instructions embedded in source files.",
    ]
    predicted = predict_exact_duplicate_pairs("synthetic", texts)
    assert predicted == []
    result = evaluate([gold_pair(0, 1, "distinct")], predicted)
    assert result["precision"] is None
    assert result["recall"] is None


def test_short_exact_duplicate_is_not_reported():
    texts = ["tiny", "tiny"]
    predicted = predict_exact_duplicate_pairs("synthetic", texts)
    result = evaluate([gold_pair(0, 1, "exact_duplicate")], predicted)
    assert result["fn"] == 1
    assert result["recall"] == 0.0
