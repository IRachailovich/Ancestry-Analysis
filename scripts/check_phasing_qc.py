#!/usr/bin/env python3
import argparse
import csv
import gzip
import json
from pathlib import Path


AUTOSOMES = [str(i) for i in range(1, 23)]


def open_vcf(path: Path):
    return gzip.open(path, "rt") if path.suffix == ".gz" else path.open()


def gt_kind(gt: str) -> tuple[bool, bool, bool]:
    gt = gt.split(":", 1)[0]
    if gt in {".", "./.", ".|."}:
        return False, False, True
    phased = "|" in gt
    alleles = gt.replace("|", "/").split("/")
    if len(alleles) != 2 or "." in alleles:
        return phased, False, True
    heterozygous = alleles[0] != alleles[1]
    return phased, heterozygous, False


def summarize_vcf(path: Path, sample_rows: int) -> dict:
    counts = {
        "variants": 0,
        "phasedVariants": 0,
        "unphasedVariants": 0,
        "heterozygousVariants": 0,
        "phasedHeterozygousVariants": 0,
        "unphasedHeterozygousVariants": 0,
        "missingVariants": 0,
        "hap1AltAlleles": 0,
        "hap2AltAlleles": 0,
    }
    examples = []
    sample_name = None

    with open_vcf(path) as handle:
        for line in handle:
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                sample_name = line.rstrip("\n").split("\t")[9]
                continue
            fields = line.rstrip("\n").split("\t")
            chrom, pos, rsid, ref, alt = fields[:5]
            gt = fields[9].split(":", 1)[0]
            phased, heterozygous, missing = gt_kind(gt)
            counts["variants"] += 1
            counts["missingVariants"] += int(missing)
            counts["phasedVariants"] += int(phased)
            counts["unphasedVariants"] += int(not phased and not missing)
            counts["heterozygousVariants"] += int(heterozygous)
            counts["phasedHeterozygousVariants"] += int(heterozygous and phased)
            counts["unphasedHeterozygousVariants"] += int(heterozygous and not phased)

            if phased and not missing:
                a1, a2 = gt.split("|")[:2]
                counts["hap1AltAlleles"] += int(a1 == "1")
                counts["hap2AltAlleles"] += int(a2 == "1")
                if heterozygous and len(examples) < sample_rows:
                    examples.append({
                        "chrom": chrom,
                        "pos": int(pos),
                        "id": rsid,
                        "ref": ref,
                        "alt": alt,
                        "gt": gt,
                        "haplotype1": alt if a1 == "1" else ref,
                        "haplotype2": alt if a2 == "1" else ref,
                    })

    counts["sampleName"] = sample_name
    counts["phasedHetRatePct"] = round((counts["phasedHeterozygousVariants"] / counts["heterozygousVariants"]) * 100, 4) if counts["heterozygousVariants"] else None
    return {"counts": counts, "examples": examples}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eagle-dir", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--sample-rows", type=int, default=20)
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    all_results = {}
    tsv_rows = []
    example_rows = []

    for dataset in ["hgdp", "1000genomes"]:
        dataset_results = {}
        for chrom in AUTOSOMES:
            path = args.eagle_dir / dataset / f"MY_SAMPLE.{dataset}.chr{chrom}.eagle2.vcf.gz"
            if not path.exists():
                continue
            summary = summarize_vcf(path, args.sample_rows)
            dataset_results[chrom] = summary["counts"]
            row = {"dataset": dataset, "chrom": chrom, **summary["counts"]}
            tsv_rows.append(row)
            for example in summary["examples"]:
                example_rows.append({"dataset": dataset, **example})
        all_results[dataset] = dataset_results

    json_path = args.outdir / "phasing_qc.json"
    json_path.write_text(json.dumps({"schemaVersion": 1, "datasets": all_results}, indent=2, sort_keys=True) + "\n")

    fields = [
        "dataset", "chrom", "sampleName", "variants", "phasedVariants", "unphasedVariants",
        "heterozygousVariants", "phasedHeterozygousVariants", "unphasedHeterozygousVariants",
        "phasedHetRatePct", "missingVariants", "hap1AltAlleles", "hap2AltAlleles",
    ]
    with (args.outdir / "phasing_qc.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(tsv_rows)

    example_fields = ["dataset", "chrom", "pos", "id", "ref", "alt", "gt", "haplotype1", "haplotype2"]
    with (args.outdir / "phased_heterozygote_examples.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=example_fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(example_rows)

    print(f"Wrote {json_path}", flush=True)
    print(f"Wrote {args.outdir / 'phasing_qc.tsv'}", flush=True)
    print(f"Wrote {args.outdir / 'phased_heterozygote_examples.tsv'}", flush=True)


if __name__ == "__main__":
    main()
