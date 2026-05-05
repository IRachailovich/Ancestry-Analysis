#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path


BRIDGE_PAIRS = [
    ("Middle_Eastern", "Southern_European"),
    ("Western_European", "Southern_European"),
    ("Caucasus", "Southern_European"),
    ("Greater_Iranian", "South_Asian"),
    ("South_Asian", "Greater_Iranian"),
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def read_predictions(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build app JSON for validation metrics and bridge-error diagnostics.")
    parser.add_argument("--validation-summary", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--tournament-summary", required=True, type=Path)
    parser.add_argument("--rfmix-summary", type=Path)
    parser.add_argument("--rfmix-synthetic-summary", type=Path)
    parser.add_argument("--rfmix-grid-summary", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    validation = read_json(args.validation_summary)
    tournament = read_json(args.tournament_summary)
    rfmix = read_json(args.rfmix_summary) if args.rfmix_summary else {}
    rfmix_synthetic = read_json(args.rfmix_synthetic_summary) if args.rfmix_synthetic_summary else {}
    rfmix_grid = read_json(args.rfmix_grid_summary) if args.rfmix_grid_summary else {}
    predictions = read_predictions(args.predictions)
    errors = [row for row in predictions if row.get("correct") != "true"]

    southern_errors = [
        {
            "sample": row["sample"],
            "trueLabel": row["true_label"],
            "predictedLabel": row["predicted_label"],
            "topProbability": float(row["top_probability"]),
        }
        for row in errors
        if row.get("predicted_label") == "Southern_European" and row.get("true_label") != "Southern_European"
    ]
    bridge_pairs = {
        f"{true_label}->{predicted_label}": sum(1 for row in predictions if row.get("true_label") == true_label and row.get("predicted_label") == predicted_label)
        for true_label, predicted_label in BRIDGE_PAIRS
    }
    bridge_errors = validation.get("bridgeErrors") or {
        "totalTrackedBridgeErrors": sum(bridge_pairs.values()),
        "pairs": bridge_pairs,
        "nonSouthernEuropeanToSouthernEuropean": {
            row["true_label"]: sum(1 for item in southern_errors if item["trueLabel"] == row["true_label"])
            for row in errors
            if row.get("predicted_label") == "Southern_European" and row.get("true_label") != "Southern_European"
        },
    }

    result = {
        "schemaVersion": 1,
        "holdout": {
            "chrom": "22",
            "accuracy": validation.get("accuracy"),
            "sampleCount": validation.get("sampleCount"),
            "errorCount": len(errors),
            "bridgeErrors": bridge_errors,
            "perLabel": validation.get("perLabel", {}),
            "errors": [
                {
                    "sample": row["sample"],
                    "trueLabel": row["true_label"],
                    "predictedLabel": row["predicted_label"],
                    "topProbability": float(row["top_probability"]),
                }
                for row in errors
            ],
            "southernEuropeanAttractorErrors": southern_errors,
        },
        "tournament": tournament,
        "independentModels": [
            {
                "id": "rfmix_general",
                "displayName": "RFMix HGDP general",
                "accuracy": rfmix.get("accuracy"),
                "sampleCount": rfmix.get("sampleCount"),
                "bridgeErrors": rfmix.get("bridgeErrors"),
                "status": "validated_chr22" if rfmix else "pending",
            }
        ] if rfmix else [],
        "syntheticValidation": {
            "rfmixDefaultStrict": {
                "meanMixtureAbsError": rfmix_synthetic.get("meanMixtureAbsError"),
                "meanUnexpectedSouthernEuropean": rfmix_synthetic.get("meanUnexpectedSouthernEuropean"),
                "sampleCount": rfmix_synthetic.get("sampleCount"),
                "status": "source_parents_excluded" if rfmix_synthetic else "pending",
            }
        } if rfmix_synthetic else {},
        "parameterGrid": rfmix_grid,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Wrote validation dashboard JSON: {args.out}", flush=True)


if __name__ == "__main__":
    main()
