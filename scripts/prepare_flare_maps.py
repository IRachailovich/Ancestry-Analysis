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
    parser = argparse.ArgumentParser(description="Convert EAGLE/HapMap maps to per-chromosome PLINK cM maps for FLARE.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--prefix", required=True, help="Output file prefix, e.g. hg38 or hg19.")
    parser.add_argument("--chroms", default="all")
    parser.add_argument("--vcf-chrom-prefix", choices=["none", "chr"], default="none")
    args = parser.parse_args()

    chroms = set(parse_chroms(args.chroms))
    args.outdir.mkdir(parents=True, exist_ok=True)
    handles = {}

    try:
        with open_text(args.input) as handle:
            header = next(handle, "").strip().split()
            if len(header) < 4 or header[0] != "chr" or header[1] != "position":
                raise SystemExit(f"{args.input} does not look like an EAGLE genetic map.")
            for line in handle:
                if not line.strip():
                    continue
                chrom, pos, _rate, cm = line.split()[:4]
                if chrom not in chroms:
                    continue
                vcf_chrom = f"chr{chrom}" if args.vcf_chrom_prefix == "chr" else chrom
                if chrom not in handles:
                    path = args.outdir / f"{args.prefix}.chr{chrom}.flare.map"
                    handles[chrom] = path.open("w")
                marker_id = f"{vcf_chrom}:{pos}"
                handles[chrom].write(f"{vcf_chrom}\t{marker_id}\t{cm}\t{pos}\n")
    finally:
        for handle in handles.values():
            handle.close()

    missing = sorted(chroms - set(handles), key=int)
    if missing:
        raise SystemExit(f"No map rows were written for chromosome(s): {', '.join(missing)}")

    print(f"Wrote FLARE PLINK maps to {args.outdir}", flush=True)


if __name__ == "__main__":
    main()
