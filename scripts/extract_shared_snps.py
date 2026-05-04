#!/usr/bin/env python3
import argparse
import csv
import gzip
import re
import shutil
import subprocess
from pathlib import Path


AUTOSOMES = [str(i) for i in range(1, 23)]
BASES = {"A", "C", "G", "T"}


def open_text(path: Path, mode: str = "rt"):
    if path.suffix == ".gz":
        return gzip.open(path, mode)
    return path.open(mode)


class BgzipWriter:
    def __init__(self, path: Path):
        self.path = path
        self.proc = None
        self.handle = None

    def __enter__(self):
        bgzip = shutil.which("bgzip")
        if bgzip:
            out = self.path.open("wb")
            self.proc = subprocess.Popen([bgzip, "-c"], stdin=subprocess.PIPE, stdout=out, text=True)
            self.handle = self.proc.stdin
            self.out = out
        else:
            self.handle = gzip.open(self.path, "wt")
        return self.handle

    def __exit__(self, exc_type, exc, tb):
        if self.proc:
            self.handle.close()
            self.out.close()
            if self.proc.wait() != 0:
                raise RuntimeError(f"bgzip failed while writing {self.path}")
        else:
            self.handle.close()


def index_vcf(path: Path):
    tabix = shutil.which("tabix")
    if tabix:
        subprocess.run([tabix, "-f", "-p", "vcf", str(path)], check=True)


def load_23andme(path: Path):
    calls = {}
    raw_positions = {}
    build = "unknown"
    build_re = re.compile(r"build\s+(\d+)", re.I)
    with path.open() as handle:
        for line in handle:
            if line.startswith("#"):
                match = build_re.search(line)
                if match:
                    build = match.group(1)
                continue
            if not line.strip():
                continue
            rsid, chrom, pos, genotype = line.rstrip("\n").split("\t")[:4]
            if not rsid.startswith("rs") or genotype == "--" or len(genotype) != 2:
                continue
            alleles = tuple(genotype.upper())
            if alleles[0] not in BASES or alleles[1] not in BASES:
                continue
            calls[rsid] = alleles
            raw_positions[rsid] = (chrom.replace("chr", ""), int(pos))
    return calls, raw_positions, build


def gt_for_call(call, ref: str, alt: str):
    a1, a2 = call
    if a1 not in {ref, alt} or a2 not in {ref, alt}:
        return None
    n_alt = int(a1 == alt) + int(a2 == alt)
    return ["0/0", "0/1", "1/1"][n_alt]


def vcf_for_chrom(pattern: str, chrom: str) -> Path:
    return Path(pattern.format(chrom=chrom))


def process_reference(name: str, pattern: str, calls, raw_positions, outdir: Path, sample_name: str):
    ref_outdir = outdir / name
    ref_outdir.mkdir(parents=True, exist_ok=True)
    summary_path = ref_outdir / "shared_snp_summary.tsv"
    all_ids_path = ref_outdir / "shared_compatible_ids.txt"
    position_to_rsid = {}
    duplicate_positions = set()
    for rsid, (chrom, pos) in raw_positions.items():
        if chrom not in AUTOSOMES:
            continue
        key = (chrom, pos)
        if key in position_to_rsid:
            duplicate_positions.add(key)
        else:
            position_to_rsid[key] = rsid
    for key in duplicate_positions:
        position_to_rsid.pop(key, None)

    with summary_path.open("w", newline="") as summary, all_ids_path.open("w") as all_ids:
        writer = csv.writer(summary, delimiter="\t", lineterminator="\n")
        writer.writerow([
            "chrom",
            "shared_id_count",
            "compatible_biallelic_snp_count",
            "same_coordinate_count",
            "different_coordinate_count",
            "incompatible_or_skipped_count",
        ])

        for chrom in AUTOSOMES:
            ref_vcf = vcf_for_chrom(pattern, chrom)
            target_vcf = ref_outdir / f"{sample_name}.{name}.chr{chrom}.shared.target.vcf.gz"
            subset_vcf = ref_outdir / f"{name}.chr{chrom}.shared.reference.vcf.gz"
            ids_path = ref_outdir / f"{name}.chr{chrom}.shared.compatible.ids"

            print(f"{name} chr{chrom}: scanning {ref_vcf}", flush=True)
            shared = 0
            compatible = 0
            same_pos = 0
            diff_pos = 0
            skipped = 0
            scanned = 0
            kept_ids = []

            with open_text(ref_vcf) as ref, BgzipWriter(target_vcf) as target, BgzipWriter(subset_vcf) as subset:
                target.write("##fileformat=VCFv4.2\n")
                target.write(f"##source=23andMe_shared_rsids_aligned_to_{name}\n")
                target.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
                target.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + sample_name + "\n")

                for line in ref:
                    if line.startswith("#"):
                        subset.write(line)
                        continue
                    scanned += 1
                    if scanned % 1_000_000 == 0:
                        print(
                            f"{name} chr{chrom}: scanned={scanned} shared={shared} compatible={compatible}",
                            flush=True,
                        )
                    fields = line.rstrip("\n").split("\t")
                    chrom_vcf, pos, ref_id, ref_allele, alt_alleles = fields[:5]
                    lookup_key = ref_id if ref_id in calls else None
                    if lookup_key is None:
                        lookup_key = position_to_rsid.get((chrom, int(pos)))
                    if lookup_key is None:
                        continue
                    shared += 1
                    alts = alt_alleles.split(",")
                    if len(ref_allele) != 1 or len(alts) != 1 or len(alts[0]) != 1:
                        skipped += 1
                        continue
                    alt = alts[0]
                    if ref_allele not in BASES or alt not in BASES:
                        skipped += 1
                        continue
                    gt = gt_for_call(calls[lookup_key], ref_allele, alt)
                    if gt is None:
                        skipped += 1
                        continue
                    compatible += 1
                    raw_chrom, raw_pos = raw_positions[lookup_key]
                    if raw_chrom == chrom and raw_pos == int(pos):
                        same_pos += 1
                    else:
                        diff_pos += 1
                    fields[2] = lookup_key
                    subset.write("\t".join(fields) + "\n")
                    target.write("\t".join([chrom_vcf, pos, lookup_key, ref_allele, alt, ".", "PASS", ".", "GT", gt]) + "\n")
                    kept_ids.append(lookup_key)

            with ids_path.open("w") as handle:
                for rsid in kept_ids:
                    handle.write(rsid + "\n")
                    all_ids.write(rsid + "\n")

            index_vcf(target_vcf)
            index_vcf(subset_vcf)

            writer.writerow([chrom, shared, compatible, same_pos, diff_pos, skipped])
            print(f"{name} chr{chrom}: shared={shared} compatible={compatible} same_pos={same_pos} diff_pos={diff_pos} skipped={skipped}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--my-23andme", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--sample-name", default="MY_SAMPLE")
    parser.add_argument("--kgp-pattern", default="/mnt/f/data/raw/1000genomes/ALL.chr{chrom}.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz")
    parser.add_argument("--hgdp-pattern", default="/mnt/f/data/raw/hgdp/hgdp_wgs.20190516.full.chr{chrom}.vcf.gz")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    calls, raw_positions, build = load_23andme(args.my_23andme)
    print(f"Loaded {len(calls)} usable 23andMe rsID calls from build {build}", flush=True)
    process_reference("1000genomes", args.kgp_pattern, calls, raw_positions, args.outdir, args.sample_name)
    process_reference("hgdp", args.hgdp_pattern, calls, raw_positions, args.outdir, args.sample_name)


if __name__ == "__main__":
    main()
