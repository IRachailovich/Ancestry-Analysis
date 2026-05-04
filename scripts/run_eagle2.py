#!/usr/bin/env python3
import argparse
import shutil
import subprocess
from pathlib import Path


AUTOSOMES = [str(i) for i in range(1, 23)]


def find_eagle(explicit: str | None) -> str:
    candidates = [explicit] if explicit else []
    candidates += ["eagle2", "/usr/local/bin/eagle2", "/opt/eagle2/Eagle_v2.4.1/eagle", "bio-eagle"]
    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if not resolved:
            continue
        help_text = subprocess.run([resolved, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False).stdout
        if "Eagle v2.4.1" not in help_text:
            raise SystemExit(f"{resolved} does not look like EAGLE2 v2.4.1.")
        if "--v1" not in help_text:
            raise SystemExit(f"{resolved} did not expose the expected Eagle1/Eagle2 option check.")
        return resolved
    raise SystemExit("EAGLE2 v2.4.1 executable was not found. Install it in WSL or pass --eagle-bin /path/to/eagle.")


def run_dataset(name: str, shared_dir: Path, outdir: Path, genetic_map: Path, eagle: str, threads: int, labels: Path | None, dry_run: bool):
    dataset_dir = shared_dir / name
    result_dir = outdir / name
    result_dir.mkdir(parents=True, exist_ok=True)
    if not genetic_map.exists():
        raise SystemExit(f"Genetic map file not found: {genetic_map}")
    if labels:
        (result_dir / "labels_used.tsv").write_text(labels.read_text())

    for chrom in AUTOSOMES:
        ref = dataset_dir / f"{name}.chr{chrom}.shared.reference.vcf.gz"
        target = dataset_dir / f"MY_SAMPLE.{name}.chr{chrom}.shared.target.vcf.gz"
        if not ref.exists() or not target.exists():
            raise SystemExit(f"Missing prepared VCFs for {name} chr{chrom}: {ref} / {target}")
        out_prefix = result_dir / f"MY_SAMPLE.{name}.chr{chrom}.eagle2"
        cmd = [
            eagle,
            f"--vcfRef={ref}",
            f"--vcfTarget={target}",
            f"--geneticMapFile={genetic_map}",
            f"--chrom={chrom}",
            f"--outPrefix={out_prefix}",
            f"--numThreads={threads}",
        ]
        print(" ".join(str(x) for x in cmd), flush=True)
        if not dry_run:
            subprocess.run([str(x) for x in cmd], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shared-dir", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--hgdp-genetic-map-file", type=Path, default=Path("/opt/eagle2/Eagle_v2.4.1/tables/genetic_map_hg38_withX.txt.gz"))
    parser.add_argument("--kgp-genetic-map-file", type=Path, default=Path("/opt/eagle2/Eagle_v2.4.1/tables/genetic_map_hg19_withX.txt.gz"))
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--eagle-bin")
    parser.add_argument("--hgdp-general-labels", type=Path)
    parser.add_argument("--kgp-labels", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    eagle = find_eagle(args.eagle_bin)
    run_dataset("hgdp", args.shared_dir, args.outdir, args.hgdp_genetic_map_file, eagle, args.threads, args.hgdp_general_labels, args.dry_run)
    run_dataset("1000genomes", args.shared_dir, args.outdir, args.kgp_genetic_map_file, eagle, args.threads, args.kgp_labels, args.dry_run)


if __name__ == "__main__":
    main()
