#!/usr/bin/env python3
import argparse
import gzip
from pathlib import Path


AUTOSOMES = [str(i) for i in range(1, 23)]


def open_text(path: Path):
    return gzip.open(path, "rt") if path.suffix == ".gz" else path.open()


def parse_chroms(value: str) -> list[str]:
    if value.lower() in {"all", "autosomes"}:
        return AUTOSOMES
    return [item.strip().removeprefix("chr") for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert EAGLE/HapMap maps to RFMix genetic map format.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--chroms", default="all")
    parser.add_argument("--vcf-chrom-prefix", choices=["none", "chr"], default="chr")
    args = parser.parse_args()

    chroms = set(parse_chroms(args.chroms))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open_text(args.input) as src, args.out.open("w") as out:
        header = next(src, "").strip().split()
        if len(header) < 4 or header[0] != "chr" or header[1] != "position":
            raise SystemExit(f"{args.input} does not look like an EAGLE genetic map.")
        for line in src:
            if not line.strip():
                continue
            chrom, pos, _rate, cm = line.split()[:4]
            if chrom not in chroms:
                continue
            vcf_chrom = f"chr{chrom}" if args.vcf_chrom_prefix == "chr" else chrom
            out.write(f"{vcf_chrom}\t{pos}\t{cm}\n")
    print(f"Wrote RFMix map: {args.out}", flush=True)


if __name__ == "__main__":
    main()
