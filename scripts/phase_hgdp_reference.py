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


def find_eagle(explicit: str | None) -> str:
    candidates = [explicit] if explicit else []
    candidates += ["eagle2", "/usr/local/bin/eagle2", "/opt/eagle2/Eagle_v2.4.1/eagle"]
    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if resolved:
            return resolved
    raise SystemExit("EAGLE2 executable was not found.")


def ensure_index(vcf: Path) -> None:
    if not Path(f"{vcf}.tbi").exists():
        subprocess.run(["tabix", "-f", "-p", "vcf", str(vcf)], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase the HGDP shared reference panel for FLARE.")
    parser.add_argument("--shared-dir", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--genetic-map-file", required=True, type=Path)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--chroms", default="all")
    parser.add_argument("--eagle-bin")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    eagle = find_eagle(args.eagle_bin)
    dataset_dir = args.shared_dir / "hgdp"
    args.outdir.mkdir(parents=True, exist_ok=True)

    for chrom in parse_chroms(args.chroms):
        ref = dataset_dir / f"hgdp.chr{chrom}.shared.reference.vcf.gz"
        if not ref.exists():
            raise SystemExit(f"Missing HGDP shared reference VCF: {ref}")
        out_prefix = args.outdir / f"hgdp.chr{chrom}.shared.reference.phased"
        out_vcf = Path(f"{out_prefix}.vcf.gz")
        if out_vcf.exists() and not args.force:
            print(f"HGDP chr{chrom}: existing phased reference found: {out_vcf}", flush=True)
            ensure_index(out_vcf)
            continue

        cmd = [
            eagle,
            f"--vcf={ref}",
            f"--geneticMapFile={args.genetic_map_file}",
            f"--chrom={chrom}",
            f"--outPrefix={out_prefix}",
            "--vcfOutFormat=z",
            f"--numThreads={args.threads}",
        ]
        print(" ".join(str(part) for part in cmd), flush=True)
        if not args.dry_run:
            subprocess.run([str(part) for part in cmd], check=True)
            ensure_index(out_vcf)


if __name__ == "__main__":
    main()
