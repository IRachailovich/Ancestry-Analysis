#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter
from pathlib import Path


COMPLEMENT = str.maketrans("ACGT", "TGCA")


def normalize_chrom(chrom: str) -> str:
    chrom = chrom.removeprefix("chr")
    return {"X": "23", "Y": "24", "MT": "90", "M": "90"}.get(chrom, chrom)


def read_23andme(path: Path) -> dict[tuple[str, int], dict[str, str]]:
    calls = {}
    with path.open(errors="ignore") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            rsid, chrom, pos, genotype = parts[:4]
            chrom = normalize_chrom(chrom)
            if not chrom.isdigit() or chrom in {"23", "24", "90"}:
                continue
            if len(genotype) != 2 or any(base not in "ACGT" for base in genotype):
                continue
            calls[(chrom, int(pos))] = {"id": rsid, "genotype": genotype}
    return calls


def compatible(genotype: str, a1: str, a2: str) -> bool:
    alleles = {a1, a2}
    gt = set(genotype)
    if gt <= alleles:
        return True
    comp_gt = set(genotype.translate(COMPLEMENT))
    return comp_gt <= alleles


def main() -> None:
    parser = argparse.ArgumentParser(description="Report 23andMe/Lazaridis shared SNP density by build37 position and allele compatibility.")
    parser.add_argument("--my-23andme", required=True, type=Path)
    parser.add_argument("--snp", required=True, type=Path)
    parser.add_argument("--out-tsv", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    args = parser.parse_args()

    calls = read_23andme(args.my_23andme)
    chrom_sites = Counter()
    matched = Counter()
    incompatible = Counter()
    rows = []

    with args.snp.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            snp_id, chrom, _genetic_pos, pos, a1, a2 = line.split()[:6]
            chrom = normalize_chrom(chrom)
            if not chrom.isdigit() or chrom in {"23", "24", "90"}:
                continue
            chrom_sites[chrom] += 1
            call = calls.get((chrom, int(pos)))
            if not call:
                continue
            if compatible(call["genotype"], a1, a2):
                matched[chrom] += 1
                rows.append({
                    "chrom": chrom,
                    "pos": pos,
                    "lazaridis_id": snp_id,
                    "my_id": call["id"],
                    "my_genotype": call["genotype"],
                    "allele1": a1,
                    "allele2": a2,
                })
            else:
                incompatible[chrom] += 1

    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_tsv.open("w", newline="") as handle:
        fields = ["chrom", "pos", "lazaridis_id", "my_id", "my_genotype", "allele1", "allele2"]
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    by_chrom = {}
    for chrom in [str(i) for i in range(1, 23)]:
        by_chrom[chrom] = {
            "lazaridisAutosomalSites": chrom_sites[chrom],
            "matchedCompatibleSites": matched[chrom],
            "matchedRatePct": round((matched[chrom] / chrom_sites[chrom]) * 100, 2) if chrom_sites[chrom] else 0,
            "incompatibleSites": incompatible[chrom],
        }

    total_sites = sum(chrom_sites.values())
    total_matched = sum(matched.values())
    result = {
        "schemaVersion": 1,
        "matchingBasis": "build37 chromosome/position plus allele compatibility; Lazaridis SNP IDs are Affymetrix IDs, not rsIDs",
        "total23andMeAutosomalUsableSites": len(calls),
        "totalLazaridisAutosomalSites": total_sites,
        "totalMatchedCompatibleSites": total_matched,
        "totalMatchedRatePct": round((total_matched / total_sites) * 100, 2) if total_sites else 0,
        "totalIncompatibleSites": sum(incompatible.values()),
        "byChrom": by_chrom,
    }
    args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
