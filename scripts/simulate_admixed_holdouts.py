#!/usr/bin/env python3
import argparse
import csv
import gzip
import random
import subprocess
from collections import defaultdict
from pathlib import Path


def open_text(path: Path, mode: str = "rt"):
    return gzip.open(path, mode) if path.suffix == ".gz" else path.open(mode)


def read_labels(path: Path) -> dict[str, str]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return {row["sample"]: row["label"] for row in reader}


def choose_pairs(labels: dict[str, str], label_a: str, label_b: str, n: int, seed: int) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    by_label: dict[str, list[str]] = defaultdict(list)
    for sample, label in labels.items():
        by_label[label].append(sample)
    if not by_label[label_a] or not by_label[label_b]:
        raise SystemExit(f"Cannot simulate {label_a}+{label_b}: missing samples.")
    samples_a = sorted(by_label[label_a])
    samples_b = sorted(by_label[label_b])
    return [(rng.choice(samples_a), rng.choice(samples_b)) for _ in range(n)]


def hap_allele(gt: str, hap_index: int) -> str:
    base = gt.split(":", 1)[0].replace("/", "|")
    alleles = base.split("|")
    if len(alleles) != 2 or "." in alleles:
        return "."
    return alleles[hap_index]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create synthetic admixed targets for validation/calibration only.")
    parser.add_argument("--phased-reference-vcf", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--pair", action="append", required=True, help="Label pair like Western_European+Middle_Eastern.")
    parser.add_argument("--samples-per-pair", type=int, default=4)
    parser.add_argument("--out-vcf", required=True, type=Path)
    parser.add_argument("--truth-tsv", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=20260505)
    args = parser.parse_args()

    labels = read_labels(args.labels)
    synthetic_pairs: list[tuple[str, str, str, str]] = []
    for pair in args.pair:
        if "+" not in pair:
            raise SystemExit(f"Pair must look like LabelA+LabelB: {pair}")
        label_a, label_b = pair.split("+", 1)
        for idx, (sample_a, sample_b) in enumerate(choose_pairs(labels, label_a, label_b, args.samples_per_pair, args.seed + len(synthetic_pairs))):
            synthetic_pairs.append((f"SIM_{label_a}_{label_b}_{idx + 1}", sample_a, sample_b, pair))

    args.out_vcf.parent.mkdir(parents=True, exist_ok=True)
    args.truth_tsv.parent.mkdir(parents=True, exist_ok=True)

    with args.truth_tsv.open("w", newline="") as truth_handle:
        writer = csv.writer(truth_handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["sample", "source_sample_1", "source_sample_2", "true_mixture"])
        writer.writerows(synthetic_pairs)

    tmp_vcf = args.out_vcf.with_suffix("").with_suffix(".tmp.vcf")
    with open_text(args.phased_reference_vcf) as src, tmp_vcf.open("w") as out:
        sample_indices = {}
        for line in src:
            if line.startswith("##"):
                out.write(line)
                continue
            if line.startswith("#CHROM"):
                header = line.rstrip("\n").split("\t")
                sample_indices = {sample: idx for idx, sample in enumerate(header[9:], start=9)}
                out.write("\t".join(header[:9] + [item[0] for item in synthetic_pairs]) + "\n")
                continue
            fields = line.rstrip("\n").split("\t")
            calls = []
            for _synthetic, sample_a, sample_b, _pair in synthetic_pairs:
                gt_a = fields[sample_indices[sample_a]]
                gt_b = fields[sample_indices[sample_b]]
                calls.append(f"{hap_allele(gt_a, 0)}|{hap_allele(gt_b, 1)}")
            out.write("\t".join(fields[:9] + calls) + "\n")

    with args.out_vcf.open("wb") as out_handle:
        subprocess.run(["bgzip", "-c", str(tmp_vcf)], stdout=out_handle, check=True)
    tmp_vcf.unlink()
    print(f"Wrote synthetic admixed VCF: {args.out_vcf}", flush=True)
    print(f"Wrote synthetic truth table: {args.truth_tsv}", flush=True)


if __name__ == "__main__":
    main()
