#!/usr/bin/env python3
import argparse
import csv
import json
import subprocess
from pathlib import Path


PRESETS = {
    "default": {},
    "shorter_windows": {"rf_window_size": "0.1", "crf_spacing": "0.05"},
    "longer_windows": {"rf_window_size": "0.4", "crf_spacing": "0.2"},
    "higher_transition_penalty": {"generations": "4", "crf_weight": "2"},
    "lower_transition_penalty": {"generations": "16", "crf_weight": "6"},
    "more_trees": {"trees": "200"},
    "em1": {"em_iterations": "1"},
}


def run(cmd: list[str], dry_run: bool) -> None:
    print(" ".join(cmd), flush=True)
    if not dry_run:
        subprocess.run(cmd, check=True)


def add_params(cmd: list[str], params: dict[str, str]) -> list[str]:
    flags = {
        "crf_spacing": "--crf-spacing",
        "rf_window_size": "--rf-window-size",
        "crf_weight": "--crf-weight",
        "generations": "--generations",
        "em_iterations": "--em-iterations",
        "trees": "--trees",
        "node_size": "--node-size",
    }
    out = list(cmd)
    for key, value in params.items():
        out.extend([flags[key], value])
    return out


def read_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small RFMix parameter grid against holdout and synthetic validation targets.")
    parser.add_argument("--repo", default=Path("/mnt/d/Python/Genetics"), type=Path)
    parser.add_argument("--out-root", default=Path("/mnt/f/data/processed/genetics_eagle"), type=Path)
    parser.add_argument("--chrom", default="22")
    parser.add_argument("--presets", default="default,shorter_windows,longer_windows,higher_transition_penalty,lower_transition_penalty")
    parser.add_argument("--samples-per-label", type=int, default=2)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    chrom = args.chrom.removeprefix("chr")
    reference_vcf = args.out_root / "results" / "phased_reference" / "hgdp" / f"hgdp.chr{chrom}.shared.reference.phased.vcf.gz"
    labels = args.out_root / "metadata" / "hgdp_labels_general.tsv"
    sample_map = args.out_root / "metadata" / "hgdp_flare_ref_panel_general.tsv"
    rfmix_map = args.out_root / "work" / "rfmix_maps" / f"hg38.{chrom}.rfmix.map"
    synthetic_vcf = args.out_root / "results" / "simulations" / "hgdp" / f"chr{chrom}" / f"synthetic_admixed_chr{chrom}.vcf.gz"
    synthetic_truth = args.out_root / "results" / "simulations" / "hgdp" / f"chr{chrom}" / "synthetic_admixed_truth.tsv"
    outdir = args.out_root / "results" / "rfmix_parameter_grid" / "hgdp" / f"chr{chrom}"
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    for preset in [item.strip() for item in args.presets.split(",") if item.strip()]:
        if preset not in PRESETS:
            raise SystemExit(f"Unknown preset {preset}. Choose from: {', '.join(PRESETS)}")
        params = PRESETS[preset]
        holdout_dir = outdir / preset / "holdout"
        synthetic_dir = outdir / preset / "synthetic"

        holdout_cmd = [
            "python3",
            str(args.repo / "scripts" / "run_rfmix_holdout_validation.py"),
            "--phased-reference-vcf",
            str(reference_vcf),
            "--labels",
            str(labels),
            "--map",
            str(rfmix_map),
            "--outdir",
            str(holdout_dir),
            "--chrom",
            chrom,
            "--samples-per-label",
            str(args.samples_per_label),
            "--threads",
            str(args.threads),
            "--model-name",
            preset,
        ]
        if args.force:
            holdout_cmd.append("--force")
        run(add_params(holdout_cmd, params), args.dry_run)

        synthetic_summary = {}
        if synthetic_vcf.exists() and synthetic_truth.exists():
            synthetic_cmd = [
                "python3",
                str(args.repo / "scripts" / "run_rfmix_synthetic_validation.py"),
                "--reference-vcf",
                str(reference_vcf),
                "--synthetic-vcf",
                str(synthetic_vcf),
                "--truth-tsv",
                str(synthetic_truth),
                "--sample-map",
                str(sample_map),
                "--genetic-map",
                str(rfmix_map),
                "--outdir",
                str(synthetic_dir),
                "--chrom",
                chrom,
                "--threads",
                str(args.threads),
                "--model-name",
                preset,
                "--exclude-source-samples",
            ]
            if args.force:
                synthetic_cmd.append("--force")
            run(add_params(synthetic_cmd, params), args.dry_run)
            synthetic_summary = read_json(synthetic_dir / f"{preset}.summary.json") if not args.dry_run else {}

        holdout_summary = read_json(holdout_dir / "summary.json") if not args.dry_run else {}
        rows.append({
            "preset": preset,
            "accuracy": holdout_summary.get("accuracy"),
            "sampleCount": holdout_summary.get("sampleCount"),
            "trackedBridgeErrors": (holdout_summary.get("bridgeErrors") or {}).get("totalTrackedBridgeErrors"),
            "meanMixtureAbsError": synthetic_summary.get("meanMixtureAbsError"),
            "meanUnexpectedSouthernEuropean": synthetic_summary.get("meanUnexpectedSouthernEuropean"),
            "params": params,
        })

    if not args.dry_run:
        (outdir / "summary.json").write_text(json.dumps({"schemaVersion": 1, "chrom": chrom, "models": rows}, indent=2, sort_keys=True) + "\n")
        with (outdir / "summary.tsv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, delimiter="\t", fieldnames=["preset", "accuracy", "sampleCount", "trackedBridgeErrors", "meanMixtureAbsError", "meanUnexpectedSouthernEuropean", "params"], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote RFMix parameter-grid summary: {outdir / 'summary.json'}", flush=True)


if __name__ == "__main__":
    main()
