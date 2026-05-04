#!/usr/bin/env python3
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATASETS = {
    "hgdp": {
        "display_name": "HGDP",
        "labels": "hgdp_labels_general.tsv",
        "label_kind": "general",
    },
    "1000genomes": {
        "display_name": "1000 Genomes",
        "labels": "1000genomes_labels.tsv",
        "label_kind": "super_population",
    },
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def as_int(value: str | None) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def percent(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round((numerator / denominator) * 100, 2)


def load_reference_labels(metadata_dir: Path) -> dict[str, Any]:
    datasets: dict[str, Any] = {}
    for dataset, config in DATASETS.items():
        rows = read_tsv(metadata_dir / config["labels"])
        label_counts: Counter[str] = Counter()
        population_counts: Counter[str] = Counter()
        region_counts: Counter[str] = Counter()

        for row in rows:
            if dataset == "hgdp":
                label = row.get("label", "")
                region = row.get("region", "")
            else:
                label = row.get("general_label", "")
                region = row.get("super_population", "")
            population = row.get("population", "")
            if label:
                label_counts[label] += 1
            if population:
                population_counts[population] += 1
            if region:
                region_counts[region] += 1

        datasets[dataset] = {
            "displayName": config["display_name"],
            "labelKind": config["label_kind"],
            "sampleCount": len(rows),
            "labelCounts": dict(sorted(label_counts.items())),
            "populationCounts": dict(sorted(population_counts.items())),
            "regionCounts": dict(sorted(region_counts.items())),
        }

    population_map = read_tsv(metadata_dir / "hgdp_population_label_map.tsv")
    return {
        "datasets": datasets,
        "hgdpPopulationLabelMap": population_map,
    }


def load_shared_snp_quality(shared_dir: Path, log_path: Path | None) -> dict[str, Any]:
    datasets: dict[str, Any] = {}
    for dataset, config in DATASETS.items():
        rows = read_tsv(shared_dir / dataset / "shared_snp_summary.tsv")
        chromosomes: list[dict[str, Any]] = []
        totals: defaultdict[str, int] = defaultdict(int)

        for row in rows:
            chrom = row["chrom"]
            shared = as_int(row.get("shared_id_count"))
            compatible = as_int(row.get("compatible_biallelic_snp_count"))
            same_coordinate = as_int(row.get("same_coordinate_count"))
            different_coordinate = as_int(row.get("different_coordinate_count"))
            skipped = as_int(row.get("incompatible_or_skipped_count"))

            chromosomes.append({
                "chrom": chrom,
                "sharedIdCount": shared,
                "compatibleBiallelicSnpCount": compatible,
                "sameCoordinateCount": same_coordinate,
                "differentCoordinateCount": different_coordinate,
                "incompatibleOrSkippedCount": skipped,
                "compatibleRatePct": percent(compatible, shared),
                "coordinateMatchRatePct": percent(same_coordinate, compatible),
            })
            totals["sharedIdCount"] += shared
            totals["compatibleBiallelicSnpCount"] += compatible
            totals["sameCoordinateCount"] += same_coordinate
            totals["differentCoordinateCount"] += different_coordinate
            totals["incompatibleOrSkippedCount"] += skipped

        total_shared = totals["sharedIdCount"]
        total_compatible = totals["compatibleBiallelicSnpCount"]
        datasets[dataset] = {
            "displayName": config["display_name"],
            "chromosomes": chromosomes,
            "totals": {
                **dict(totals),
                "compatibleRatePct": percent(total_compatible, total_shared),
                "coordinateMatchRatePct": percent(totals["sameCoordinateCount"], total_compatible),
            },
        }

    extraction = {"usable23andmeRsidCalls": None, "build": None}
    if log_path and log_path.exists():
        text = log_path.read_text(errors="replace")
        match = re.search(r"Loaded\s+(\d+)\s+usable 23andMe rsID calls from build\s+(\S+)", text)
        if match:
            extraction = {
                "usable23andmeRsidCalls": int(match.group(1)),
                "build": match.group(2),
            }

    return {
        "extraction": extraction,
        "datasets": datasets,
    }


def inspect_eagle_results(eagle_dir: Path) -> dict[str, Any]:
    datasets: dict[str, Any] = {}
    for dataset, config in DATASETS.items():
        result_dir = eagle_dir / dataset
        labels_used = result_dir / "labels_used.tsv"
        files = sorted(path.name for path in result_dir.glob("*") if path.is_file()) if result_dir.exists() else []
        chromosome_prefixes = sorted({
            match.group(1)
            for name in files
            if (match := re.search(r"\.chr(\d+)\.eagle2", name))
        }, key=lambda value: int(value))

        datasets[dataset] = {
            "displayName": config["display_name"],
            "resultDir": str(result_dir),
            "exists": result_dir.exists(),
            "labelsUsed": labels_used.exists(),
            "fileCount": len(files),
            "chromosomesWithResultFiles": chromosome_prefixes,
        }
    return {"datasets": datasets}


def build_report_summary(reference_labels: dict[str, Any], quality: dict[str, Any], eagle: dict[str, Any], sample_name: str) -> dict[str, Any]:
    dataset_summaries = []
    for dataset, config in DATASETS.items():
        label_info = reference_labels["datasets"].get(dataset, {})
        quality_info = quality["datasets"].get(dataset, {})
        eagle_info = eagle["datasets"].get(dataset, {})
        totals = quality_info.get("totals", {})
        dataset_summaries.append({
            "id": dataset,
            "displayName": config["display_name"],
            "referenceSampleCount": label_info.get("sampleCount", 0),
            "referenceLabelCount": len(label_info.get("labelCounts", {})),
            "compatibleSnpCount": totals.get("compatibleBiallelicSnpCount", 0),
            "compatibleRatePct": totals.get("compatibleRatePct"),
            "coordinateMatchRatePct": totals.get("coordinateMatchRatePct"),
            "eagleResultFileCount": eagle_info.get("fileCount", 0),
            "status": "eagle_results_detected" if eagle_info.get("fileCount", 0) else "prepared_for_eagle",
        })

    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sampleName": sample_name,
        "uiDirection": {
            "primary": "Option 5 consumer-friendly ancestry report",
            "secondary": "Option 2 explore map",
        },
        "extraction": quality.get("extraction", {}),
        "datasets": dataset_summaries,
        "recommendedViews": [
            "report_dashboard",
            "chromosome_view",
            "explore_map",
            "analysis_quality",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-dir", required=True, type=Path)
    parser.add_argument("--shared-dir", required=True, type=Path)
    parser.add_argument("--eagle-dir", required=True, type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--sample-name", default="MY_SAMPLE")
    args = parser.parse_args()

    reference_labels = load_reference_labels(args.metadata_dir)
    quality = load_shared_snp_quality(args.shared_dir, args.log)
    eagle = inspect_eagle_results(args.eagle_dir)
    report_summary = build_report_summary(reference_labels, quality, eagle, args.sample_name)

    write_json(args.outdir / "reference_labels.json", reference_labels)
    write_json(args.outdir / "shared_snp_quality.json", quality)
    write_json(args.outdir / "eagle_results_index.json", eagle)
    write_json(args.outdir / "report_summary.json", report_summary)
    print(f"Wrote app report JSON files to {args.outdir}", flush=True)


if __name__ == "__main__":
    main()
