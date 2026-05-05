#!/usr/bin/env python3
import argparse
import csv
import json
import random
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_BRIDGE_PAIRS = [
    ("Middle_Eastern", "Southern_European"),
    ("Western_European", "Southern_European"),
    ("Caucasus", "Southern_European"),
    ("Greater_Iranian", "South_Asian"),
    ("South_Asian", "Greater_Iranian"),
]


def read_labels(path: Path, label_column: str) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = {"sample", label_column} - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"{path} is missing required columns: {', '.join(sorted(missing))}")
        return list(reader)


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


def write_lines(path: Path, values: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{value}\n" for value in values))


def write_ref_panel(path: Path, rows: list[dict[str, str]], label_column: str, excluded: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        for row in rows:
            if row["sample"] not in excluded:
                writer.writerow([row["sample"], row[label_column]])


def run(cmd: list[str], dry_run: bool) -> None:
    print(" ".join(cmd), flush=True)
    if not dry_run:
        subprocess.run(cmd, check=True)


def read_rfmix_q(path: Path) -> list[dict[str, str]]:
    labels = []
    rows = []
    with path.open() as handle:
        for line in handle:
            if line.startswith("#sample"):
                labels = line.strip().split("\t")[1:]
                continue
            if line.startswith("#") or not line.strip():
                continue
            values = line.strip().split("\t")
            sample = values[0]
            rows.append({"SAMPLE": sample, **dict(zip(labels, values[1:]))})
    return rows


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


def bridge_errors(predictions: list[dict[str, str]], pairs: list[tuple[str, str]]) -> dict[str, object]:
    pair_counts = {}
    total = 0
    for true_label, predicted_label in pairs:
        count = sum(1 for row in predictions if row["true_label"] == true_label and row["predicted_label"] == predicted_label)
        pair_counts[f"{true_label}->{predicted_label}"] = count
        total += count
    southern_attractor = Counter(row["true_label"] for row in predictions if row["predicted_label"] == "Southern_European" and row["true_label"] != "Southern_European")
    return {
        "totalTrackedBridgeErrors": total,
        "pairs": pair_counts,
        "nonSouthernEuropeanToSouthernEuropean": dict(sorted(southern_attractor.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run unbiased RFMix holdout validation on known reference samples.")
    parser.add_argument("--phased-reference-vcf", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--map", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--chrom", default="22")
    parser.add_argument("--label-column", default="label")
    parser.add_argument("--samples-per-label", type=int, default=2)
    parser.add_argument("--min-ref-samples", type=int, default=5)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260505)
    parser.add_argument("--model-name", default="rfmix_general")
    parser.add_argument("--rfmix-bin", default="rfmix")
    parser.add_argument("--crf-spacing")
    parser.add_argument("--rf-window-size")
    parser.add_argument("--crf-weight")
    parser.add_argument("--generations")
    parser.add_argument("--em-iterations")
    parser.add_argument("--trees")
    parser.add_argument("--node-size")
    parser.add_argument("--reanalyze-reference", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rfmix = shutil.which(args.rfmix_bin) or args.rfmix_bin
    rows = read_labels(args.labels, args.label_column)
    ref_samples, holdouts, truth = choose_holdouts(rows, args.label_column, args.samples_per_label, args.min_ref_samples, args.seed)
    args.outdir.mkdir(parents=True, exist_ok=True)

    ref_samples_path = args.outdir / "reference_samples.txt"
    holdouts_path = args.outdir / "holdout_samples.txt"
    truth_path = args.outdir / "holdout_truth.tsv"
    ref_panel_path = args.outdir / "ref_panel.tsv"
    ref_vcf = args.outdir / "reference_without_holdouts.vcf.gz"
    gt_vcf = args.outdir / "holdout_targets.vcf.gz"
    out_prefix = args.outdir / "rfmix_holdout"

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

    q_path = Path(f"{out_prefix}.rfmix.Q")
    if args.force or not q_path.exists():
        cmd = [
            rfmix,
            "-f",
            str(gt_vcf),
            "-r",
            str(ref_vcf),
            "-m",
            str(ref_panel_path),
            "-g",
            str(args.map),
            "-o",
            str(out_prefix),
            f"--chromosome=chr{args.chrom.removeprefix('chr')}",
            f"--n-threads={args.threads}",
            f"--random-seed={args.seed}",
        ]
        for option, value in [
            ("--crf-spacing", args.crf_spacing),
            ("--rf-window-size", args.rf_window_size),
            ("--crf-weight", args.crf_weight),
            ("--generations", args.generations),
            ("--em-iterations", args.em_iterations),
            ("--trees", args.trees),
            ("--node-size", args.node_size),
        ]:
            if value is not None:
                cmd.append(f"{option}={value}")
        if args.reanalyze_reference:
            cmd.append("--reanalyze-reference")
        run(cmd, args.dry_run)

    if args.dry_run:
        return

    global_rows = read_rfmix_q(q_path)
    predictions = write_predictions(args.outdir / "predictions.tsv", global_rows, truth)
    summary = write_confusion(args.outdir / "confusion_matrix.tsv", predictions)
    summary.update({
        "schemaVersion": 1,
        "modelName": args.model_name,
        "phasedReferenceVcf": str(args.phased_reference_vcf),
        "labelColumn": args.label_column,
        "samplesPerLabel": args.samples_per_label,
        "minRefSamples": args.min_ref_samples,
        "seed": args.seed,
        "modelConfig": {
            "program": "RFMix",
            "threads": args.threads,
            "crfSpacing": args.crf_spacing,
            "rfWindowSize": args.rf_window_size,
            "crfWeight": args.crf_weight,
            "generations": args.generations,
            "emIterations": args.em_iterations,
            "trees": args.trees,
            "nodeSize": args.node_size,
            "reanalyzeReference": args.reanalyze_reference,
        },
        "bridgeErrors": bridge_errors(predictions, DEFAULT_BRIDGE_PAIRS),
        "labelCounts": dict(sorted(Counter(row[args.label_column] for row in rows).items())),
    })
    (args.outdir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"Wrote RFMix holdout summary: {args.outdir / 'summary.json'}", flush=True)


if __name__ == "__main__":
    main()
