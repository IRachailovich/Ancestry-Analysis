#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


AUTOSOMES = [str(i) for i in range(1, 23)]
DATASETS = {"hgdp", "1000genomes"}


def parse_chroms(value: str) -> list[str]:
    if value.lower() in {"all", "autosomes"}:
        return AUTOSOMES
    return [item.strip().removeprefix("chr") for item in value.split(",") if item.strip()]


def ref_vcf(dataset: str, chrom: str, shared_dir: Path, phased_ref_dir: Path) -> Path:
    if dataset == "hgdp":
        return phased_ref_dir / f"hgdp.chr{chrom}.shared.reference.phased.vcf.gz"
    return shared_dir / "1000genomes" / f"1000genomes.chr{chrom}.shared.reference.vcf.gz"


def map_file(dataset: str, chrom: str, map_dir: Path) -> Path:
    prefix = "hg38" if dataset == "hgdp" else "hg19"
    return map_dir / f"{prefix}.chr{chrom}.flare.map"


def target_vcf(dataset: str, chrom: str, eagle_dir: Path) -> Path:
    return eagle_dir / dataset / f"MY_SAMPLE.{dataset}.chr{chrom}.eagle2.vcf.gz"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FLARE local ancestry inference on phased target data.")
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--shared-dir", required=True, type=Path)
    parser.add_argument("--eagle-dir", required=True, type=Path)
    parser.add_argument("--phased-ref-dir", required=True, type=Path)
    parser.add_argument("--map-dir", required=True, type=Path)
    parser.add_argument("--ref-panel", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--chroms", default="all")
    parser.add_argument("--flare-jar", type=Path, default=Path("/opt/flare/flare.jar"))
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--memory-gb", type=int, default=6)
    parser.add_argument("--seed", default="20260505")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    first_model: Path | None = None

    for index, chrom in enumerate(parse_chroms(args.chroms)):
        ref = ref_vcf(args.dataset, chrom, args.shared_dir, args.phased_ref_dir)
        gt = target_vcf(args.dataset, chrom, args.eagle_dir)
        genetic_map = map_file(args.dataset, chrom, args.map_dir)
        for path in [ref, gt, genetic_map, args.ref_panel, args.flare_jar]:
            if not path.exists():
                raise SystemExit(f"Missing FLARE input: {path}")

        out_prefix = args.outdir / args.dataset / f"MY_SAMPLE.{args.dataset}.chr{chrom}.flare"
        out_prefix.parent.mkdir(parents=True, exist_ok=True)
        anc_vcf = Path(f"{out_prefix}.anc.vcf.gz")
        if anc_vcf.exists() and not args.force:
            print(f"FLARE {args.dataset} chr{chrom}: existing output found: {anc_vcf}", flush=True)
            if first_model is None:
                first_model = Path(f"{out_prefix}.model")
            continue

        cmd = [
            "java",
            f"-Xmx{args.memory_gb}g",
            "-jar",
            str(args.flare_jar),
            f"ref={ref}",
            f"ref-panel={args.ref_panel}",
            f"gt={gt}",
            f"map={genetic_map}",
            f"out={out_prefix}",
            "probs=true",
            "array=true",
            f"nthreads={args.threads}",
            f"seed={args.seed}",
        ]
        if index > 0 and first_model and first_model.exists():
            cmd += [f"model={first_model}", "em=false"]

        print(" ".join(str(part) for part in cmd), flush=True)
        if not args.dry_run:
            subprocess.run([str(part) for part in cmd], check=True)
            model_path = Path(f"{out_prefix}.model")
            if first_model is None and model_path.exists():
                first_model = model_path


if __name__ == "__main__":
    main()
