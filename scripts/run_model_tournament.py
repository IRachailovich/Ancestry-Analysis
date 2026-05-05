#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


MODELS = [
    {
        "name": "flare_flat_default",
        "label_file": "hgdp_labels_general.tsv",
        "label_column": "label",
        "min_maf": "0.005",
        "gen": "10.0",
        "em": "true",
        "array": "true",
    },
    {
        "name": "flare_flat_minmaf_0",
        "label_file": "hgdp_labels_general.tsv",
        "label_column": "label",
        "min_maf": "0.0",
        "gen": "10.0",
        "em": "true",
        "array": "true",
    },
    {
        "name": "flare_flat_minmaf_001",
        "label_file": "hgdp_labels_general.tsv",
        "label_column": "label",
        "min_maf": "0.001",
        "gen": "10.0",
        "em": "true",
        "array": "true",
    },
    {
        "name": "flare_flat_gen_5",
        "label_file": "hgdp_labels_general.tsv",
        "label_column": "label",
        "min_maf": "0.005",
        "gen": "5.0",
        "em": "true",
        "array": "true",
    },
    {
        "name": "flare_flat_gen_20",
        "label_file": "hgdp_labels_general.tsv",
        "label_column": "label",
        "min_maf": "0.005",
        "gen": "20.0",
        "em": "true",
        "array": "true",
    },
    {
        "name": "flare_flat_no_em",
        "label_file": "hgdp_labels_general.tsv",
        "label_column": "label",
        "min_maf": "0.005",
        "gen": "10.0",
        "em": "false",
        "array": "true",
    },
    {
        "name": "flare_broad_first",
        "label_file": "hgdp_labels_broad.tsv",
        "label_column": "label",
        "min_maf": "0.005",
        "gen": "10.0",
        "em": "true",
        "array": "true",
    },
]


def run(cmd: list[str], dry_run: bool) -> None:
    print(" ".join(cmd), flush=True)
    if not dry_run:
        subprocess.run(cmd, check=True)


def score_model(summary: dict) -> tuple[float, float, float]:
    accuracy = float(summary.get("accuracy") or 0.0)
    bridge = float(summary.get("bridgeErrors", {}).get("totalTrackedBridgeErrors") or 0.0)
    per_label = summary.get("perLabel", {})
    recalls = [float(item["recall"]) for item in per_label.values() if item.get("recall") is not None]
    balanced = sum(recalls) / len(recalls) if recalls else 0.0
    return (accuracy - bridge * 0.02, balanced, accuracy)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small validation tournament across ancestry model configurations.")
    parser.add_argument("--phased-reference-vcf", required=True, type=Path)
    parser.add_argument("--metadata-dir", required=True, type=Path)
    parser.add_argument("--map", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=Path("/mnt/d/Python/Genetics"))
    parser.add_argument("--samples-per-label", type=int, default=2)
    parser.add_argument("--min-ref-samples", type=int, default=5)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--memory-gb", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20260505)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    summaries = []
    validator = args.repo / "scripts" / "run_flare_holdout_validation.py"

    for model in MODELS:
        model_out = args.outdir / model["name"]
        cmd = [
            "python3",
            str(validator),
            "--phased-reference-vcf",
            str(args.phased_reference_vcf),
            "--labels",
            str(args.metadata_dir / model["label_file"]),
            "--label-column",
            model["label_column"],
            "--map",
            str(args.map),
            "--outdir",
            str(model_out),
            "--samples-per-label",
            str(args.samples_per_label),
            "--min-ref-samples",
            str(args.min_ref_samples),
            "--threads",
            str(args.threads),
            "--memory-gb",
            str(args.memory_gb),
            "--seed",
            str(args.seed),
            "--model-name",
            model["name"],
            "--min-maf",
            model["min_maf"],
            "--gen",
            model["gen"],
            "--em",
            model["em"],
            "--array",
            model["array"],
        ]
        if args.force:
            cmd.append("--force")
        run(cmd, args.dry_run)
        if not args.dry_run:
            summary = json.loads((model_out / "summary.json").read_text())
            summary["resultDir"] = str(model_out)
            summaries.append(summary)

    if args.dry_run:
        return

    ranked = sorted(summaries, key=score_model, reverse=True)
    result = {
        "schemaVersion": 1,
        "chrom": args.phased_reference_vcf.name,
        "metric": "accuracy minus 0.02 per tracked bridge error; balanced recall tie-break",
        "winner": ranked[0]["modelName"] if ranked else None,
        "models": [
            {
                "modelName": item["modelName"],
                "accuracy": item.get("accuracy"),
                "sampleCount": item.get("sampleCount"),
                "trackedBridgeErrors": item.get("bridgeErrors", {}).get("totalTrackedBridgeErrors"),
                "bridgePairs": item.get("bridgeErrors", {}).get("pairs", {}),
                "modelConfig": item.get("modelConfig", {}),
                "resultDir": item["resultDir"],
            }
            for item in ranked
        ],
    }
    out_json = args.outdir / "model_tournament_summary.json"
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Wrote model tournament summary: {out_json}", flush=True)


if __name__ == "__main__":
    main()
