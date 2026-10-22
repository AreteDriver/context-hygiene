#!/usr/bin/env python3
"""Score internal exact-duplicate fixtures without claiming external benchmark accuracy."""

import argparse
import json
from pathlib import Path


def pair_key(row: dict) -> tuple:
    """Use stable, unordered block identifiers within one fixture."""
    a, b = str(row["block_a"]), str(row["block_b"])
    if a == b:
        raise ValueError("pair blocks must differ")
    return (str(row["source_id"]), *sorted((a, b)))


def evaluate(gold: list[dict], predictions: list[dict]) -> dict:
    """Require a fully enumerated pair universe; no implicit true negatives."""
    gold_by_pair = {}
    for row in gold:
        key = pair_key(row)
        if key in gold_by_pair:
            raise ValueError(f"duplicate gold pair: {key}")
        if row["label"] not in {"exact_duplicate", "near_duplicate", "distinct"}:
            raise ValueError(f"invalid or unadjudicated gold label: {row['label']}")
        gold_by_pair[key] = row["label"]

    predicted = set()
    for row in predictions:
        key = pair_key(row)
        if key not in gold_by_pair:
            raise ValueError(f"prediction outside labeled pair universe: {key}")
        if key in predicted:
            raise ValueError(f"duplicate prediction: {key}")
        predicted.add(key)

    positives = {key for key, label in gold_by_pair.items() if label == "exact_duplicate"}
    tp = len(predicted & positives)
    fp = len(predicted - positives)
    fn = len(positives - predicted)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else None
    return {
        "scope": "internal_fixture_only",
        "gold_pairs": len(gold_by_pair),
        "gold_positives": len(positives),
        "predicted_positives": len(predicted),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "external_accuracy_claim_permitted": False,
    }


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold", type=Path)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(read_jsonl(args.gold), read_jsonl(args.predictions)), indent=2))


if __name__ == "__main__":
    main()
