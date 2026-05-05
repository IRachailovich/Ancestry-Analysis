#!/usr/bin/env python3
import argparse
import shutil
import subprocess
from pathlib import Path


AUTOSOMES = [str(i) for i in range(1, 23)]


def parse_chroms(value: str) -> list[str]:
    if value.lower() in {"all", "autosomes"}:
        return AUTOSOMES
    return [item.strip().removeprefix("chr") for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RFMix v2 as an independent local ancestry comparator.")
    parser.add_argument("--reference-vcf", required=True, type=Path, help="Reference VCF path or template containing {chrom}.")
    parser.add_argument("--target-template", required=True, type=Path, help="Template containing {chrom}, e.g. MY_SAMPLE.hgdp.chr{chrom}.eagle2.vcf.gz")
    parser.add_argument("--sample-map", required=True, type=Path)
    parser.add_argument("--genetic-map", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--chroms", default="22")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--rfmix-bin", default="rfmix")
    parser.add_argument("--em-iterations", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rfmix = shutil.which(args.rfmix_bin) or args.rfmix_bin
    if not Path(rfmix).exists() and shutil.which(rfmix) is None:
        raise SystemExit("RFMix executable was not found.")

    args.outdir.mkdir(parents=True, exist_ok=True)
    for chrom in parse_chroms(args.chroms):
        target = Path(str(args.target_template).format(chrom=chrom))
        reference = Path(str(args.reference_vcf).format(chrom=chrom))
        if not target.exists():
            raise SystemExit(f"Missing RFMix target VCF: {target}")
        if not reference.exists():
            raise SystemExit(f"Missing RFMix reference VCF: {reference}")
        out_prefix = args.outdir / f"MY_SAMPLE.hgdp.chr{chrom}.rfmix"
        msp = Path(f"{out_prefix}.msp.tsv")
        if msp.exists() and not args.force:
            print(f"RFMix chr{chrom}: existing output found: {msp}", flush=True)
            continue
        cmd = [
            rfmix,
            "-f",
            str(target),
            "-r",
            str(reference),
            "-m",
            str(args.sample_map),
            "-g",
            str(args.genetic_map),
            "-o",
            str(out_prefix),
            f"--chromosome=chr{chrom}",
            f"--n-threads={args.threads}",
        ]
        if args.em_iterations > 0:
            cmd.extend(["-e", str(args.em_iterations)])
        print(" ".join(cmd), flush=True)
        if not args.dry_run:
            subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
