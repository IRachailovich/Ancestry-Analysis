#!/usr/bin/env python3
import argparse
import csv
import gzip
import json
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


def read_labels(path: Path, label_column: str) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = {"sample", label_column} - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"{path} is missing required columns: {', '.join(sorted(missing))}")
        return list(reader)


def write_lines(path: Path, values: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{value}\n" for value in values))


def run(cmd: list[str], dry_run: bool) -> None:
    print(" ".join(cmd), flush=True)
    if not dry_run:
        subprocess.run(cmd, check=True)


def choose_holdouts(rows: list[dict[str, str]], label_column: str, samples_per_label: int, min_ref_samples: int, seed: int) -> tuple[list[str], list[str], dict[str, str]]:
    rng = random.Random(seed)
    by_label: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        by_label[row[label_column]].append(row["sample"])

    holdouts = []
    truth = {}
    for label, samples in sorted(by_label.items()):
        if len(samples) < min_ref_samples + 1:
            continue
        shuffled = sorted(samples)
        rng.shuffle(shuffled)
        chosen = shuffled[: min(samples_per_label, max(1, len(samples) - min_ref_samples))]
        for sample in chosen:
            holdouts.append(sample)
            truth[sample] = label

    ref_samples = [row["sample"] for row in rows if row["sample"] not in truth]
    if not holdouts:
        raise SystemExit("No holdout samples could be selected.")
    return sorted(ref_samples), sorted(holdouts), truth


def write_ref_panel(path: Path, rows: list[dict[str, str]], label_column: str, excluded: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        for row in rows:
            if row["sample"] not in excluded:
                writer.writerow([row["sample"], row[label_column]])


def read_global_ancestry(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader)


def write_predictions(path: Path, global_rows: list[dict[str, str]], truth: dict[str, str]) -> list[dict[str, str]]:
    predictions = []
    for row in global_rows:
        sample = row["SAMPLE"]
        scores = {key: float(value) for key, value in row.items() if key != "SAMPLE" and value not in {"", "."}}
        predicted, score = max(scores.items(), key=lambda item: item[1])
        true_label = truth.get(sample, "")
        predictions.append({
            "sample": sample,
            "true_label": true_label,
            "predicted_label": predicted,
            "top_probability": f"{score:.6f}",
            "correct": str(predicted == true_label).lower(),
            **{f"prob_{key}": f"{value:.6f}" for key, value in sorted(scores.items())},
        })

    fields = sorted({key for row in predictions for key in row})
    first = ["sample", "true_label", "predicted_label", "top_probability", "correct"]
    fields = first + [field for field in fields if field not in first]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(predictions)
    return predictions


def write_confusion(path: Path, predictions: list[dict[str, str]]) -> dict[str, object]:
    labels = sorted({row["true_label"] for row in predictions} | {row["predicted_label"] for row in predictions})
    matrix = {label: Counter() for label in labels}
    correct = 0
    for row in predictions:
        matrix[row["true_label"]][row["predicted_label"]] += 1
        correct += int(row["true_label"] == row["predicted_label"])

    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["true_label", *labels])
        for true_label in labels:
            writer.writerow([true_label, *[matrix[true_label][pred] for pred in labels]])

    per_label = {}
    for label in labels:
        total = sum(matrix[label].values())
        per_label[label] = {
            "n": total,
            "recall": round(matrix[label][label] / total, 4) if total else None,
            "topConfusions": matrix[label].most_common(5),
        }

    return {
        "sampleCount": len(predictions),
        "accuracy": round(correct / len(predictions), 4) if predictions else None,
        "perLabel": per_label,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run unbiased FLARE holdout validation on known reference samples.")
    parser.add_argument("--phased-reference-vcf", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--map", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--label-column", default="label")
    parser.add_argument("--samples-per-label", type=int, default=2)
    parser.add_argument("--min-ref-samples", type=int, default=5)
    parser.add_argument("--flare-jar", type=Path, default=Path("/opt/flare/flare.jar"))
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--memory-gb", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20260505)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = read_labels(args.labels, args.label_column)
    ref_samples, holdouts, truth = choose_holdouts(rows, args.label_column, args.samples_per_label, args.min_ref_samples, args.seed)
    args.outdir.mkdir(parents=True, exist_ok=True)

    ref_samples_path = args.outdir / "reference_samples.txt"
    holdouts_path = args.outdir / "holdout_samples.txt"
    truth_path = args.outdir / "holdout_truth.tsv"
    ref_panel_path = args.outdir / "ref_panel.tsv"
    ref_vcf = args.outdir / "reference_without_holdouts.vcf.gz"
    gt_vcf = args.outdir / "holdout_targets.vcf.gz"
    out_prefix = args.outdir / "flare_holdout"

    write_lines(ref_samples_path, ref_samples)
    write_lines(holdouts_path, holdouts)
    write_ref_panel(ref_panel_path, rows, args.label_column, set(holdouts))
    with truth_path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["sample", "true_label"])
        for sample in holdouts:
            writer.writerow([sample, truth[sample]])

    if args.force or not ref_vcf.exists():
        run(["bcftools", "view", "-S", str(ref_samples_path), "-Oz", "-o", str(ref_vcf), str(args.phased_reference_vcf)], args.dry_run)
        run(["tabix", "-f", "-p", "vcf", str(ref_vcf)], args.dry_run)
    if args.force or not gt_vcf.exists():
        run(["bcftools", "view", "-S", str(holdouts_path), "-Oz", "-o", str(gt_vcf), str(args.phased_reference_vcf)], args.dry_run)
        run(["tabix", "-f", "-p", "vcf", str(gt_vcf)], args.dry_run)

    global_path = Path(f"{out_prefix}.global.anc.gz")
    if args.force or not global_path.exists():
        run([
            "java",
            f"-Xmx{args.memory_gb}g",
            "-jar",
            str(args.flare_jar),
            f"ref={ref_vcf}",
            f"ref-panel={ref_panel_path}",
            f"gt={gt_vcf}",
            f"map={args.map}",
            f"out={out_prefix}",
            "probs=true",
            "array=true",
            f"nthreads={args.threads}",
            f"seed={args.seed}",
        ], args.dry_run)

    if args.dry_run:
        return

    global_rows = read_global_ancestry(global_path)
    predictions = write_predictions(args.outdir / "predictions.tsv", global_rows, truth)
    summary = write_confusion(args.outdir / "confusion_matrix.tsv", predictions)
    summary.update({
        "schemaVersion": 1,
        "phasedReferenceVcf": str(args.phased_reference_vcf),
        "labelColumn": args.label_column,
        "samplesPerLabel": args.samples_per_label,
        "minRefSamples": args.min_ref_samples,
        "seed": args.seed,
        "labelCounts": dict(sorted(Counter(row[args.label_column] for row in rows).items())),
    })
    (args.outdir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"Wrote validation summary: {args.outdir / 'summary.json'}", flush=True)


if __name__ == "__main__":
    main()
