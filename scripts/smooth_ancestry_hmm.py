#!/usr/bin/env python3
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


REQUIRED = {"chrom", "start", "end", "label"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"{path} is missing required columns: {', '.join(sorted(missing))}")
        return list(reader)


def parse_float(value: str | None, default: float) -> float:
    if value is None or value == "":
        return default
    return float(value)


def emission_log_probs(row: dict[str, str], states: list[str], min_prob: float) -> dict[str, float]:
    prob_cols = {key[5:]: parse_float(value, 0.0) for key, value in row.items() if key.startswith("prob_")}
    if prob_cols:
        total = sum(max(value, 0.0) for value in prob_cols.values())
        if total > 0:
            return {state: math.log(max(prob_cols.get(state, 0.0) / total, min_prob)) for state in states}

    label = row["label"]
    confidence = max(min(parse_float(row.get("confidence"), 0.85), 0.999), min_prob)
    other = max((1.0 - confidence) / max(len(states) - 1, 1), min_prob)
    return {state: math.log(confidence if state == label else other) for state in states}


def transition_log_probs(states: list[str], stay_prob: float) -> dict[tuple[str, str], float]:
    if len(states) == 1:
        return {(states[0], states[0]): 0.0}
    switch_prob = (1.0 - stay_prob) / (len(states) - 1)
    return {
        (prev, curr): math.log(stay_prob if prev == curr else switch_prob)
        for prev in states
        for curr in states
    }


def viterbi(rows: list[dict[str, str]], states: list[str], stay_prob: float, min_prob: float) -> list[str]:
    trans = transition_log_probs(states, stay_prob)
    emissions = [emission_log_probs(row, states, min_prob) for row in rows]

    scores = {state: math.log(1.0 / len(states)) + emissions[0][state] for state in states}
    backptrs: list[dict[str, str]] = []

    for idx in range(1, len(rows)):
        next_scores = {}
        back = {}
        for curr in states:
            prev, score = max(
                ((prev, scores[prev] + trans[(prev, curr)] + emissions[idx][curr]) for prev in states),
                key=lambda item: item[1],
            )
            next_scores[curr] = score
            back[curr] = prev
        scores = next_scores
        backptrs.append(back)

    last = max(scores, key=scores.get)
    path = [last]
    for back in reversed(backptrs):
        last = back[last]
        path.append(last)
    return list(reversed(path))


def merge_segments(rows: list[dict[str, str]], labels: list[str]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    for row, label in zip(rows, labels):
        start = int(row["start"])
        end = int(row["end"])
        confidence = parse_float(row.get("confidence"), 0.85)
        copy = row.get("copy", "")
        if (
            merged
            and merged[-1]["chrom"] == row["chrom"]
            and merged[-1].get("copy", "") == copy
            and merged[-1]["label"] == label
            and int(merged[-1]["end"]) >= start - 1
        ):
            prev = merged[-1]
            prev_len = int(prev["end"]) - int(prev["start"]) + 1
            row_len = end - start + 1
            prev["end"] = str(max(int(prev["end"]), end))
            prev["snp_count"] = str(int(prev["snp_count"]) + int(row.get("snp_count", "1") or "1"))
            prev_conf = parse_float(prev.get("confidence"), 0.85)
            prev["confidence"] = f"{((prev_conf * prev_len) + (confidence * row_len)) / (prev_len + row_len):.4f}"
        else:
            merged.append({
                "chrom": row["chrom"],
                "copy": copy,
                "start": str(start),
                "end": str(end),
                "label": label,
                "confidence": f"{confidence:.4f}",
                "snp_count": row.get("snp_count", "1") or "1",
                "source": row.get("source", ""),
            })
    return merged


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["chrom", "copy", "start", "end", "label", "confidence", "snp_count", "source"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict[str, str]]) -> None:
    by_chrom: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_chrom[row["chrom"]].append({
            "copy": row.get("copy", ""),
            "start": int(row["start"]),
            "end": int(row["end"]),
            "label": row["label"],
            "confidence": parse_float(row.get("confidence"), 0.0),
            "snpCount": int(row.get("snp_count", "0") or "0"),
            "source": row.get("source", ""),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schemaVersion": 1, "chromosomes": by_chrom}, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path, help="Raw local ancestry segments TSV.")
    parser.add_argument("--out-tsv", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--stay-prob", type=float, default=0.995)
    parser.add_argument("--min-prob", type=float, default=1e-6)
    args = parser.parse_args()

    rows = read_rows(args.input)
    by_group: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    states = sorted({row["label"] for row in rows})
    for row in rows:
        by_group[(row["chrom"], row.get("copy", ""))].append(row)

    smoothed = []
    def sort_key(group: tuple[str, str]) -> tuple[int, str]:
        chrom, copy = group
        return (int(chrom) if chrom.isdigit() else 999, copy)

    for group in sorted(by_group, key=sort_key):
        group_rows = sorted(by_group[group], key=lambda row: (int(row["start"]), int(row["end"])))
        labels = viterbi(group_rows, states, args.stay_prob, args.min_prob)
        smoothed.extend(merge_segments(group_rows, labels))

    write_tsv(args.out_tsv, smoothed)
    write_json(args.out_json, smoothed)
    print(f"Wrote smoothed segments: {args.out_tsv}", flush=True)
    print(f"Wrote chromosome JSON: {args.out_json}", flush=True)


if __name__ == "__main__":
    main()
