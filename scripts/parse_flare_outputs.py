#!/usr/bin/env python3
import argparse
import csv
import gzip
import json
import re
from pathlib import Path


AUTOSOMES = [str(i) for i in range(1, 23)]


def parse_chroms(value: str) -> list[str]:
    if value.lower() in {"all", "autosomes"}:
        return AUTOSOMES
    return [item.strip().removeprefix("chr") for item in value.split(",") if item.strip()]


def open_text(path: Path):
    return gzip.open(path, "rt") if path.suffix == ".gz" else path.open()


def read_ancestries(path: Path) -> dict[str, str]:
    ancestries = {}
    legacy_pattern = re.compile(r"##ANCESTRY=<ID=([^,>]+),Description=\"?([^\">]+)\"?>")
    with open_text(path) as handle:
        for line in handle:
            if line.startswith("##ANCESTRY="):
                stripped = line.strip()
                match = legacy_pattern.match(stripped)
                if match:
                    ancestries[match.group(1)] = match.group(2)
                    continue
                if stripped.startswith("##ANCESTRY=<") and stripped.endswith(">"):
                    body = stripped.removeprefix("##ANCESTRY=<").removesuffix(">")
                    for item in body.split(","):
                        if "=" not in item:
                            continue
                        label, code = item.split("=", 1)
                        ancestries[code] = label
            if line.startswith("#CHROM"):
                break
    return ancestries


def prob_for_label(format_keys: list[str], sample_values: list[str], prob_key: str, ancestry_index: int) -> float | None:
    if prob_key not in format_keys:
        return None
    raw = sample_values[format_keys.index(prob_key)]
    if raw in {".", ""}:
        return None
    values = [float(value) for value in raw.split(",")]
    if ancestry_index >= len(values):
        return None
    return values[ancestry_index]


def flush_segment(rows: list[dict[str, object]], segment: dict[str, object] | None) -> None:
    if not segment:
        return
    count = int(segment["snp_count"])
    segment["confidence"] = f"{float(segment['confidence_sum']) / max(count, 1):.4f}"
    del segment["confidence_sum"]
    rows.append({key: str(value) for key, value in segment.items()})


def parse_flare_vcf(path: Path, source: str) -> list[dict[str, str]]:
    ancestries = read_ancestries(path)
    rows: list[dict[str, str]] = []
    active: dict[str, dict[str, object] | None] = {"1": None, "2": None}

    with open_text(path) as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            chrom, pos = fields[0], int(fields[1])
            format_keys = fields[8].split(":")
            sample_values = fields[9].split(":")
            for copy, an_key, prob_key in [("1", "AN1", "ANP1"), ("2", "AN2", "ANP2")]:
                if an_key not in format_keys:
                    raise SystemExit(f"{path} is missing FORMAT/{an_key}")
                ancestry_code = sample_values[format_keys.index(an_key)]
                label = ancestries.get(ancestry_code, ancestry_code)
                confidence = prob_for_label(format_keys, sample_values, prob_key, int(ancestry_code) if ancestry_code.isdigit() else 0)
                if confidence is None:
                    confidence = 0.85
                current = active[copy]
                if current and current["chrom"] == chrom.removeprefix("chr") and current["label"] == label:
                    current["end"] = pos
                    current["snp_count"] = int(current["snp_count"]) + 1
                    current["confidence_sum"] = float(current["confidence_sum"]) + confidence
                else:
                    flush_segment(rows, current)
                    active[copy] = {
                        "chrom": chrom.removeprefix("chr"),
                        "copy": copy,
                        "start": pos,
                        "end": pos,
                        "label": label,
                        "confidence_sum": confidence,
                        "snp_count": 1,
                        "source": source,
                    }

    for segment in active.values():
        flush_segment(rows, segment)
    return rows


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["chrom", "copy", "start", "end", "label", "confidence", "snp_count", "source"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert FLARE .anc.vcf.gz output into local ancestry segments.")
    parser.add_argument("--flare-dir", required=True, type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--chroms", default="all")
    parser.add_argument("--out-tsv", required=True, type=Path)
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    for chrom in parse_chroms(args.chroms):
        path = args.flare_dir / args.dataset / f"MY_SAMPLE.{args.dataset}.chr{chrom}.flare.anc.vcf.gz"
        if not path.exists():
            raise SystemExit(f"Missing FLARE ancestry VCF: {path}")
        rows.extend(parse_flare_vcf(path, f"flare_{args.dataset}"))

    write_tsv(args.out_tsv, rows)
    summary = {
        "schemaVersion": 1,
        "dataset": args.dataset,
        "segmentCount": len(rows),
        "outTsv": str(args.out_tsv),
    }
    if args.summary_json:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"Wrote FLARE segments: {args.out_tsv}", flush=True)


if __name__ == "__main__":
    main()
