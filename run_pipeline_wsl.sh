#!/usr/bin/env bash
set -euo pipefail

RAW=/mnt/f/data/raw
OUT=/mnt/f/data/processed/genetics_eagle
REPO=/mnt/d/Python/Genetics
APP_DATA_DIR="$REPO/data"
SAMPLE_NAME=MY_SAMPLE
THREADS="${THREADS:-4}"
SEGMENTS_DIR="$OUT/results/segments"
SKIP_EXTRACTION="${SKIP_EXTRACTION:-0}"

mkdir -p "$OUT"/{metadata,work,logs,results}
mkdir -p "$APP_DATA_DIR"

python3 "$REPO/scripts/make_labels.py" \
  --hgdp-metadata "$RAW/hgdp/hgdp_wgs.20190516.metadata.txt" \
  --kgp-panel "$RAW/1000genomes/integrated_call_samples_v3.20130502.ALL.panel" \
  --outdir "$OUT/metadata"

if [[ "$SKIP_EXTRACTION" == "1" ]]; then
  echo "Skipping shared-SNP extraction; using existing files in $OUT/work/shared_snps" >&2
else
  python3 "$REPO/scripts/extract_shared_snps.py" \
    --my-23andme "$RAW/my_23andme_data/genome_Itamar_Rachailovich_v5_Full_20260117221330.txt" \
    --sample-name "$SAMPLE_NAME" \
    --outdir "$OUT/work/shared_snps" \
    2>&1 | tee "$OUT/logs/extract_shared_snps.log"
fi

python3 "$REPO/scripts/build_report_json.py" \
  --metadata-dir "$OUT/metadata" \
  --shared-dir "$OUT/work/shared_snps" \
  --eagle-dir "$OUT/results/eagle2" \
  --log "$OUT/logs/extract_shared_snps.log" \
  --outdir "$OUT/results/app" \
  --sample-name "$SAMPLE_NAME"

cp "$OUT/results/app/"*.json "$APP_DATA_DIR/"

if [[ "${RUN_EAGLE:-0}" == "1" ]]; then
  python3 "$REPO/scripts/run_eagle2.py" \
    --shared-dir "$OUT/work/shared_snps" \
    --outdir "$OUT/results/eagle2" \
    --hgdp-genetic-map-file "${HGDP_EAGLE_MAP:-/opt/eagle2/Eagle_v2.4.1/tables/genetic_map_hg38_withX.txt.gz}" \
    --kgp-genetic-map-file "${KGP_EAGLE_MAP:-/opt/eagle2/Eagle_v2.4.1/tables/genetic_map_hg19_withX.txt.gz}" \
    --threads "$THREADS" \
    --hgdp-general-labels "$OUT/metadata/hgdp_labels_general.tsv" \
    --kgp-labels "$OUT/metadata/1000genomes_labels.tsv"

  python3 "$REPO/scripts/build_report_json.py" \
    --metadata-dir "$OUT/metadata" \
    --shared-dir "$OUT/work/shared_snps" \
    --eagle-dir "$OUT/results/eagle2" \
    --log "$OUT/logs/extract_shared_snps.log" \
    --outdir "$OUT/results/app" \
    --sample-name "$SAMPLE_NAME"

  if [[ -s "$SEGMENTS_DIR/raw_segments.tsv" ]]; then
    python3 "$REPO/scripts/smooth_ancestry_hmm.py" \
      --input "$SEGMENTS_DIR/raw_segments.tsv" \
      --out-tsv "$SEGMENTS_DIR/smoothed_segments.tsv" \
      --out-json "$OUT/results/app/chromosome_segments.json"
  fi

  cp "$OUT/results/app/"*.json "$APP_DATA_DIR/"
else
  echo "Prepared labels, shared-SNP VCFs, and app JSON. Published app JSON to $APP_DATA_DIR. Set RUN_EAGLE=1 to run EAGLE2." >&2
fi
