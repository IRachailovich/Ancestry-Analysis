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
FLARE_CHROMS="${FLARE_CHROMS:-all}"
FLARE_DATASETS="${FLARE_DATASETS:-hgdp}"
FLARE_THREADS="${FLARE_THREADS:-$THREADS}"
FLARE_MEMORY_GB="${FLARE_MEMORY_GB:-6}"
PHASE_HGDP_REF="${PHASE_HGDP_REF:-1}"
VALIDATE_CHROMS="${VALIDATE_CHROMS:-22}"
VALIDATION_SAMPLES_PER_LABEL="${VALIDATION_SAMPLES_PER_LABEL:-2}"

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

  python3 "$REPO/scripts/check_phasing_qc.py" \
    --eagle-dir "$OUT/results/eagle2" \
    --outdir "$OUT/results/phasing_qc"

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
  cp "$OUT/results/phasing_qc/phasing_qc.json" "$APP_DATA_DIR/"
else
  echo "Prepared labels, shared-SNP VCFs, and app JSON. Published app JSON to $APP_DATA_DIR. Set RUN_EAGLE=1 to run EAGLE2." >&2
fi

if [[ "${RUN_FLARE:-0}" == "1" ]]; then
  python3 "$REPO/scripts/make_flare_ref_panel.py" \
    --labels "$OUT/metadata/hgdp_labels_general.tsv" \
    --out "$OUT/metadata/hgdp_flare_ref_panel_general.tsv" \
    --summary-json "$OUT/metadata/hgdp_flare_ref_panel_general.json"

  python3 "$REPO/scripts/make_flare_ref_panel.py" \
    --labels "$OUT/metadata/1000genomes_labels.tsv" \
    --label-column general_label \
    --out "$OUT/metadata/1000genomes_flare_ref_panel_general.tsv" \
    --summary-json "$OUT/metadata/1000genomes_flare_ref_panel_general.json"

  python3 "$REPO/scripts/prepare_flare_maps.py" \
    --input "${HGDP_EAGLE_MAP:-/opt/eagle2/Eagle_v2.4.1/tables/genetic_map_hg38_withX.txt.gz}" \
    --outdir "$OUT/work/flare_maps" \
    --prefix hg38 \
    --chroms "$FLARE_CHROMS" \
    --vcf-chrom-prefix chr

  python3 "$REPO/scripts/prepare_flare_maps.py" \
    --input "${KGP_EAGLE_MAP:-/opt/eagle2/Eagle_v2.4.1/tables/genetic_map_hg19_withX.txt.gz}" \
    --outdir "$OUT/work/flare_maps" \
    --prefix hg19 \
    --chroms "$FLARE_CHROMS" \
    --vcf-chrom-prefix none

  if [[ "$PHASE_HGDP_REF" == "1" && " $FLARE_DATASETS " == *" hgdp "* ]]; then
    python3 "$REPO/scripts/phase_hgdp_reference.py" \
      --shared-dir "$OUT/work/shared_snps" \
      --outdir "$OUT/results/phased_reference/hgdp" \
      --genetic-map-file "${HGDP_EAGLE_MAP:-/opt/eagle2/Eagle_v2.4.1/tables/genetic_map_hg38_withX.txt.gz}" \
      --threads "$THREADS" \
      --chroms "$FLARE_CHROMS"
  fi

  for dataset in $FLARE_DATASETS; do
    if [[ "$dataset" == "hgdp" ]]; then
      panel="$OUT/metadata/hgdp_flare_ref_panel_general.tsv"
    elif [[ "$dataset" == "1000genomes" ]]; then
      panel="$OUT/metadata/1000genomes_flare_ref_panel_general.tsv"
    else
      echo "Unsupported FLARE dataset: $dataset" >&2
      exit 1
    fi

    python3 "$REPO/scripts/run_flare.py" \
      --dataset "$dataset" \
      --shared-dir "$OUT/work/shared_snps" \
      --eagle-dir "$OUT/results/eagle2" \
      --phased-ref-dir "$OUT/results/phased_reference/hgdp" \
      --map-dir "$OUT/work/flare_maps" \
      --ref-panel "$panel" \
      --outdir "$OUT/results/flare" \
      --chroms "$FLARE_CHROMS" \
      --threads "$FLARE_THREADS" \
      --memory-gb "$FLARE_MEMORY_GB"

    python3 "$REPO/scripts/parse_flare_outputs.py" \
      --flare-dir "$OUT/results/flare" \
      --dataset "$dataset" \
      --chroms "$FLARE_CHROMS" \
      --out-tsv "$SEGMENTS_DIR/raw_segments_${dataset}.tsv" \
      --summary-json "$OUT/results/flare/${dataset}_segments_summary.json"

    python3 "$REPO/scripts/smooth_ancestry_hmm.py" \
      --input "$SEGMENTS_DIR/raw_segments_${dataset}.tsv" \
      --out-tsv "$SEGMENTS_DIR/segments_${dataset}_raw_no_hmm.tsv" \
      --out-json "$OUT/results/app/chromosome_segments_${dataset}_raw_no_hmm.json" \
      --no-smooth \
      --profile-name raw_no_hmm

    python3 "$REPO/scripts/smooth_ancestry_hmm.py" \
      --input "$SEGMENTS_DIR/raw_segments_${dataset}.tsv" \
      --out-tsv "$SEGMENTS_DIR/smoothed_segments_${dataset}_light.tsv" \
      --out-json "$OUT/results/app/chromosome_segments_${dataset}_light.json" \
      --stay-prob 0.9 \
      --profile-name hmm_light_0.90

    python3 "$REPO/scripts/smooth_ancestry_hmm.py" \
      --input "$SEGMENTS_DIR/raw_segments_${dataset}.tsv" \
      --out-tsv "$SEGMENTS_DIR/smoothed_segments_${dataset}_medium.tsv" \
      --out-json "$OUT/results/app/chromosome_segments_${dataset}_medium.json" \
      --stay-prob 0.97 \
      --profile-name hmm_medium_0.97

    python3 "$REPO/scripts/smooth_ancestry_hmm.py" \
      --input "$SEGMENTS_DIR/raw_segments_${dataset}.tsv" \
      --out-tsv "$SEGMENTS_DIR/smoothed_segments_${dataset}.tsv" \
      --out-json "$OUT/results/app/chromosome_segments_${dataset}_strong.json" \
      --stay-prob 0.995 \
      --profile-name hmm_strong_0.995

    cp "$OUT/results/app/chromosome_segments_${dataset}_raw_no_hmm.json" "$OUT/results/app/chromosome_segments_${dataset}.json"
  done

  if [[ -s "$OUT/results/app/chromosome_segments_hgdp.json" ]]; then
    cp "$OUT/results/app/chromosome_segments_hgdp.json" "$OUT/results/app/chromosome_segments.json"
  fi

  cp "$OUT/results/app/"*.json "$APP_DATA_DIR/"
fi

if [[ "${RUN_VALIDATE:-0}" == "1" ]]; then
  python3 "$REPO/scripts/prepare_flare_maps.py" \
    --input "${HGDP_EAGLE_MAP:-/opt/eagle2/Eagle_v2.4.1/tables/genetic_map_hg38_withX.txt.gz}" \
    --outdir "$OUT/work/flare_maps" \
    --prefix hg38 \
    --chroms "$VALIDATE_CHROMS" \
    --vcf-chrom-prefix chr

  if [[ "$VALIDATE_CHROMS" == "all" ]]; then
    validate_chroms="$(seq 1 22)"
  else
    validate_chroms="${VALIDATE_CHROMS//,/ }"
  fi

  for chrom in $validate_chroms; do
    chrom="${chrom#chr}"
    if [[ ! -s "$OUT/results/phased_reference/hgdp/hgdp.chr${chrom}.shared.reference.phased.vcf.gz" ]]; then
      python3 "$REPO/scripts/phase_hgdp_reference.py" \
        --shared-dir "$OUT/work/shared_snps" \
        --outdir "$OUT/results/phased_reference/hgdp" \
        --genetic-map-file "${HGDP_EAGLE_MAP:-/opt/eagle2/Eagle_v2.4.1/tables/genetic_map_hg38_withX.txt.gz}" \
        --threads "$THREADS" \
        --chroms "$chrom"
    fi

    python3 "$REPO/scripts/run_flare_holdout_validation.py" \
      --phased-reference-vcf "$OUT/results/phased_reference/hgdp/hgdp.chr${chrom}.shared.reference.phased.vcf.gz" \
      --labels "$OUT/metadata/hgdp_labels_general.tsv" \
      --map "$OUT/work/flare_maps/hg38.chr${chrom}.flare.map" \
      --outdir "$OUT/results/validation/hgdp/chr${chrom}" \
      --samples-per-label "$VALIDATION_SAMPLES_PER_LABEL" \
      --threads "$FLARE_THREADS" \
      --memory-gb "$FLARE_MEMORY_GB"

    cp "$OUT/results/validation/hgdp/chr${chrom}/summary.json" "$APP_DATA_DIR/validation_hgdp_chr${chrom}.json"
  done
fi
