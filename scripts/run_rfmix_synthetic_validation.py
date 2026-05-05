#!/usr/bin/env python3
import argparse
import csv
import json
import shutil
import subprocess
from pathlib import Path


def run(cmd: list[str], dry_run: bool) -> None:
    print(" ".join(cmd), flush=True)
    if not dry_run:
        subprocess.run(cmd, check=True)


def read_truth(path: Path) -> tuple[dict[str, list[str]], set[str]]:
    truth = {}
    source_samples = set()
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            truth[row["sample"]] = row["true_mixture"].split("+", 1)
            source_samples.add(row["source_sample_1"])
            source_samples.add(row["source_sample_2"])
    return truth, source_samples


def filter_reference_panel(sample_map: Path, excluded_samples: set[str], out_panel: Path, out_samples: Path) -> None:
    kept = []
    out_panel.parent.mkdir(parents=True, exist_ok=True)
    with sample_map.open() as src, out_panel.open("w", newline="") as panel_handle:
        writer = csv.writer(panel_handle, delimiter="\t", lineterminator="\n")
        for line in src:
            if not line.strip():
                continue
            sample, label = line.rstrip("\n").split("\t")[:2]
            if sample in excluded_samples:
                continue
            kept.append(sample)
            writer.writerow([sample, label])
    out_samples.write_text("".join(f"{sample}\n" for sample in kept))


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
            rows.append({"SAMPLE": values[0], **dict(zip(labels, values[1:]))})
    return rows


def summarize(rows: list[dict[str, str]], truth: dict[str, list[str]]) -> dict[str, object]:
    predictions = []
    total_abs_error = 0.0
    n = 0
    southern_excess = []
    for row in rows:
        sample = row["SAMPLE"]
        expected_labels = truth[sample]
        probs = {key: float(value) for key, value in row.items() if key != "SAMPLE"}
        expected = {label: 0.5 for label in expected_labels}
        labels = set(probs) | set(expected)
        abs_error = sum(abs(probs.get(label, 0.0) - expected.get(label, 0.0)) for label in labels) / 2
        total_abs_error += abs_error
        n += 1
        top_label, top_prob = max(probs.items(), key=lambda item: item[1])
        if "Southern_European" not in expected:
            southern_excess.append(probs.get("Southern_European", 0.0))
        predictions.append({
            "sample": sample,
            "truth": "+".join(expected_labels),
            "topLabel": top_label,
            "topProbability": round(top_prob, 6),
            "mixtureAbsError": round(abs_error, 6),
            "probabilities": {label: round(probs.get(label, 0.0), 6) for label in sorted(probs)},
        })

    return {
        "schemaVersion": 1,
        "sampleCount": n,
        "meanMixtureAbsError": round(total_abs_error / n, 6) if n else None,
        "meanUnexpectedSouthernEuropean": round(sum(southern_excess) / len(southern_excess), 6) if southern_excess else None,
        "predictions": predictions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RFMix on synthetic admixed targets and score probability calibration.")
    parser.add_argument("--reference-vcf", required=True, type=Path)
    parser.add_argument("--synthetic-vcf", required=True, type=Path)
    parser.add_argument("--truth-tsv", required=True, type=Path)
    parser.add_argument("--sample-map", required=True, type=Path)
    parser.add_argument("--genetic-map", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--chrom", default="22")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260505)
    parser.add_argument("--model-name", default="rfmix_synthetic")
    parser.add_argument("--rfmix-bin", default="rfmix")
    parser.add_argument("--crf-spacing")
    parser.add_argument("--rf-window-size")
    parser.add_argument("--crf-weight")
    parser.add_argument("--generations")
    parser.add_argument("--em-iterations")
    parser.add_argument("--trees")
    parser.add_argument("--node-size")
    parser.add_argument("--reanalyze-reference", action="store_true")
    parser.add_argument("--exclude-source-samples", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rfmix = shutil.which(args.rfmix_bin) or args.rfmix_bin
    args.outdir.mkdir(parents=True, exist_ok=True)
    truth, source_samples = read_truth(args.truth_tsv)
    reference_vcf = args.reference_vcf
    sample_map = args.sample_map
    if args.exclude_source_samples:
        filtered_panel = args.outdir / "ref_panel_without_synthetic_sources.tsv"
        filtered_samples = args.outdir / "reference_samples_without_synthetic_sources.txt"
        filtered_reference = args.outdir / "reference_without_synthetic_sources.vcf.gz"
        filter_reference_panel(args.sample_map, source_samples, filtered_panel, filtered_samples)
        if args.force or not filtered_reference.exists():
            run(["bcftools", "view", "-S", str(filtered_samples), "-Oz", "-o", str(filtered_reference), str(args.reference_vcf)], args.dry_run)
            run(["tabix", "-f", "-p", "vcf", str(filtered_reference)], args.dry_run)
        reference_vcf = filtered_reference
        sample_map = filtered_panel

    out_prefix = args.outdir / args.model_name
    q_path = Path(f"{out_prefix}.rfmix.Q")
    if args.force or not q_path.exists():
        cmd = [
            rfmix,
            "-f",
            str(args.synthetic_vcf),
            "-r",
            str(reference_vcf),
            "-m",
            str(sample_map),
            "-g",
            str(args.genetic_map),
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

    result = summarize(read_rfmix_q(q_path), truth)
    result["modelName"] = args.model_name
    result["modelConfig"] = {
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
        "excludeSourceSamples": args.exclude_source_samples,
    }
    (args.outdir / f"{args.model_name}.summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Wrote synthetic validation summary: {args.outdir / f'{args.model_name}.summary.json'}", flush=True)


if __name__ == "__main__":
    main()
