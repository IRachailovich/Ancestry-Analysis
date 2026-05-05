#!/usr/bin/env python3
import argparse
import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path


def open_text(path: Path):
    return gzip.open(path, "rt") if path.suffix == ".gz" else path.open()


def read_global(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    with open_text(path) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        row = next(reader, None)
        if not row:
            return {}
        return {key: float(value) for key, value in row.items() if key != "SAMPLE" and value not in {"", "."}}


def read_rfmix_q(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    labels = []
    with path.open() as handle:
        for line in handle:
            if line.startswith("#sample"):
                labels = line.strip().split("\t")[1:]
                continue
            if line.startswith("#") or not line.strip():
                continue
            values = line.strip().split("\t")[1:]
            return {label: float(value) for label, value in zip(labels, values)}
    return {}


def summarize_rfmix_msp(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"perChrom": {}, "perCopy": {}, "overall": {}}
    code_to_label = {}
    rows = []
    with path.open() as handle:
        for line in handle:
            if line.startswith("#Subpopulation order/codes:"):
                body = line.split(":", 1)[1].strip()
                for item in body.split("\t"):
                    if "=" in item:
                        label, code = item.split("=", 1)
                        code_to_label[code] = label
                continue
            if line.startswith("#chm"):
                header = line.lstrip("#").rstrip("\n").split("\t")
                continue
            if line.startswith("#") or not line.strip():
                continue
            values = line.rstrip("\n").split("\t")
            rows.append(dict(zip(header, values)))

    overall = defaultdict(int)
    per_chrom: dict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    per_copy: dict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        chrom = row["chm"].removeprefix("chr")
        length = max(0, int(row["epos"]) - int(row["spos"]) + 1)
        for copy, column in [("1", "MY_SAMPLE.0"), ("2", "MY_SAMPLE.1")]:
            label = code_to_label.get(row[column], row[column])
            overall[label] += length
            per_chrom[chrom][label] += length
            per_copy[copy][label] += length

    def pct_map(values: dict[str, int]) -> dict[str, float]:
        total = sum(values.values()) or 1
        return {label: round((length / total) * 100, 2) for label, length in sorted(values.items(), key=lambda item: (-item[1], item[0]))}

    return {
        "overall": pct_map(overall),
        "perChrom": {chrom: pct_map(values) for chrom, values in sorted(per_chrom.items(), key=lambda item: int(item[0]) if item[0].isdigit() else 999)},
        "perCopy": {copy: pct_map(values) for copy, values in sorted(per_copy.items())},
    }


def summarize_segments(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"perChrom": {}, "perCopy": {}, "overall": {}}
    totals: dict[str, defaultdict[str, int]] = {
        "overall": defaultdict(int),
    }
    per_chrom: dict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    per_copy: dict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))

    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            length = max(0, int(row["end"]) - int(row["start"]) + 1)
            label = row["label"]
            chrom = row["chrom"]
            copy = row.get("copy", "")
            totals["overall"][label] += length
            per_chrom[chrom][label] += length
            per_copy[copy][label] += length

    def pct_map(values: dict[str, int]) -> dict[str, float]:
        total = sum(values.values()) or 1
        return {label: round((length / total) * 100, 2) for label, length in sorted(values.items(), key=lambda item: (-item[1], item[0]))}

    return {
        "overall": pct_map(totals["overall"]),
        "perChrom": {chrom: pct_map(values) for chrom, values in sorted(per_chrom.items(), key=lambda item: int(item[0]) if item[0].isdigit() else 999)},
        "perCopy": {copy: pct_map(values) for copy, values in sorted(per_copy.items())},
    }


def top_probs(probs: dict[str, float], limit: int = 8) -> list[dict[str, object]]:
    return [
        {"label": label, "probability": round(value * 100, 2)}
        for label, value in sorted(probs.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def build_meta(models: list[dict[str, object]]) -> dict[str, object]:
    broad = next((model for model in models if model["id"] == "broad_first"), None)
    flat = next((model for model in models if model["id"] == "flat_general"), None)
    rfmix = next((model for model in models if model["id"] == "rfmix_general"), None)
    notes = []
    if flat:
        flat_top = (flat.get("globalTop") or [{}])[0]
        if flat_top.get("label") == "Southern_European":
            notes.append("Flat model top label is Southern_European; validation shows this label can act as a bridge/attractor.")
    if broad:
        broad_top = (broad.get("globalTop") or [{}])[0]
        notes.append(f"Broad-first top label is {broad_top.get('label', 'unknown')}; use as a coarse first-stage result only.")
    if rfmix:
        notes.append("RFMix is included as an independent local ancestry model; it still needs the same autosome-wide holdout validation before final reporting.")

    consensus_inputs = [model for model in [flat, rfmix] if model]
    consensus: dict[str, float] = defaultdict(float)
    if consensus_inputs:
        for model in consensus_inputs:
            for label, pct in (model.get("globalProbabilities") or {}).items():
                consensus[label] += float(pct) / len(consensus_inputs)

    return {
        "status": "provisional_chr22_only",
        "method": "probability-level consensus over models with the same HGDP general label space; no hard-label voting",
        "topConsensus": [
            {"label": label, "probability": round(value, 2)}
            for label, value in sorted(consensus.items(), key=lambda item: (-item[1], item[0]))[:8]
        ],
        "labelPolicy": {
            "allowedForFinalReport": [],
            "reason": "No fine label is allowed into the final report until it passes autosome-wide holdout validation.",
            "currentValidationScope": "chr22",
        },
        "notes": notes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build app JSON for personal model outputs and copy-specific summaries.")
    parser.add_argument("--flat-global", required=True, type=Path)
    parser.add_argument("--flat-segments", required=True, type=Path)
    parser.add_argument("--broad-global", required=True, type=Path)
    parser.add_argument("--broad-segments", required=True, type=Path)
    parser.add_argument("--rfmix-q", type=Path)
    parser.add_argument("--rfmix-msp", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    models = []
    for model_id, display_name, global_path, segment_path in [
        ("flat_general", "FLARE flat HGDP general", args.flat_global, args.flat_segments),
        ("broad_first", "FLARE broad-first", args.broad_global, args.broad_segments),
    ]:
        global_probs = read_global(global_path)
        models.append({
            "id": model_id,
            "displayName": display_name,
            "globalTop": top_probs(global_probs),
            "globalProbabilities": {label: round(value * 100, 2) for label, value in sorted(global_probs.items())},
            "segments": summarize_segments(segment_path),
        })

    if args.rfmix_q and args.rfmix_msp and args.rfmix_q.exists() and args.rfmix_msp.exists():
        rfmix_probs = read_rfmix_q(args.rfmix_q)
        models.append({
            "id": "rfmix_general",
            "displayName": "RFMix HGDP general",
            "globalTop": top_probs(rfmix_probs),
            "globalProbabilities": {label: round(value * 100, 2) for label, value in sorted(rfmix_probs.items())},
            "segments": summarize_rfmix_msp(args.rfmix_msp),
        })

    result = {
        "schemaVersion": 1,
        "sample": "MY_SAMPLE",
        "chromosomesCovered": ["22"],
        "models": models,
        "metaModel": build_meta(models),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Wrote sample model outputs JSON: {args.out}", flush=True)


if __name__ == "__main__":
    main()
