#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def read_labels(path: Path, label_column: str) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = {"sample", label_column} - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"{path} is missing required columns: {', '.join(sorted(missing))}")
        return list(reader)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a FLARE ref-panel file from labeled reference samples.")
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--label-column", default="label")
    parser.add_argument("--min-samples-per-label", type=int, default=5)
    parser.add_argument("--exclude-label", action="append", default=[])
    args = parser.parse_args()

    rows = read_labels(args.labels, args.label_column)
    excluded = set(args.exclude_label)
    counts = Counter(row[args.label_column] for row in rows if row[args.label_column] not in excluded)
    kept_labels = {label for label, count in counts.items() if count >= args.min_samples_per_label}
    kept_rows = [row for row in rows if row[args.label_column] in kept_labels]

    if not kept_rows:
        raise SystemExit("No reference samples remain after FLARE panel filtering.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        for row in kept_rows:
            writer.writerow([row["sample"], row[args.label_column]])

    summary = {
        "schemaVersion": 1,
        "source": str(args.labels),
        "refPanel": str(args.out),
        "labelColumn": args.label_column,
        "minSamplesPerLabel": args.min_samples_per_label,
        "excludedLabels": sorted(excluded),
        "sampleCount": len(kept_rows),
        "labelCounts": dict(sorted(Counter(row[args.label_column] for row in kept_rows).items())),
        "droppedLabelCounts": dict(sorted((label, count) for label, count in counts.items() if label not in kept_labels)),
    }

    if args.summary_json:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    print(f"Wrote FLARE ref-panel: {args.out}", flush=True)
    print(f"Kept {summary['sampleCount']} samples across {len(summary['labelCounts'])} labels", flush=True)


if __name__ == "__main__":
    main()
