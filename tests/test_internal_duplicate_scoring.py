"""Internal scoring harness regression tests; not external benchmark evidence."""

import pytest


def score(gold, predictions):
    from scripts.score_internal_duplicate_fixtures import evaluate

    return evaluate(gold, predictions)


def row(a, b, label=None):
    result = {"source_id": "synthetic", "block_a": a, "block_b": b}
    if label is not None:
        result["label"] = label
    return result


def test_counts_and_metrics():
    gold = [row("a", "b", "exact_duplicate"), row("a", "c", "distinct")]
    result = score(gold, [row("b", "a"), row("a", "c")])
    assert (result["tp"], result["fp"], result["fn"]) == (1, 1, 0)
    assert result["precision"] == 0.5
    assert result["recall"] == 1.0
    assert result["external_accuracy_claim_permitted"] is False


def test_undefined_metrics_are_null():
    result = score([row("a", "b", "distinct")], [])
    assert result["precision"] is None
    assert result["recall"] is None
    assert result["f1"] is None


def test_missing_predictions_count_as_false_negatives():
    result = score([row("a", "b", "exact_duplicate")], [])
    assert result["fn"] == 1
    assert result["recall"] == 0.0


def test_rejects_unlabeled_predictions():
    with pytest.raises(ValueError, match="outside labeled"):
        score([], [row("a", "b")])


def test_rejects_uncertain_labels():
    with pytest.raises(ValueError, match="unadjudicated"):
        score([row("a", "b", "uncertain")], [])


def test_rejects_duplicate_gold_and_predictions():
    with pytest.raises(ValueError, match="duplicate gold"):
        score([row("a", "b", "distinct"), row("b", "a", "distinct")], [])
    with pytest.raises(ValueError, match="duplicate prediction"):
        score([row("a", "b", "distinct")], [row("a", "b"), row("b", "a")])
