# Genetics EAGLE2 WSL Pipeline

This workflow reads the raw data in `/mnt/f/data/raw` and writes derived files to `/mnt/f/data/processed/genetics_eagle`.

Steps:

1. Create HGDP general and local labels plus 1000 Genomes labels.
2. Load the 23andMe build 37 raw file.
3. Stream each reference VCF by chromosome and keep the maximum set of shared compatible `rsID` SNPs.
4. Align the target VCF coordinates to the reference VCF coordinates by copying `CHROM/POS/REF/ALT` from the matching reference `rsID`.
5. Write app-facing JSON summaries for the ancestry report UI.
6. Optionally run EAGLE2 twice: once with HGDP reference plus generalized HGDP labels, once with 1000 Genomes reference.
7. Optionally phase the HGDP reference panel itself with EAGLE2 so FLARE has a phased reference.
8. Optionally run FLARE for probabilistic local ancestry, using phased target haplotypes and phased reference haplotypes.
9. Smooth FLARE local ancestry segments with an HMM and publish chromosome-painting JSON.
10. Optionally run RFMix as an independent local ancestry comparator.
11. Optionally create synthetic admixed targets for validation/calibration only; these are never used as reference samples by default.

Run from WSL:

```bash
cd /mnt/d/Python/Genetics
bash run_pipeline_wsl.sh
```

The extraction step can take a long time, especially for HGDP. The script writes BGZF-compressed, tabix-indexed VCFs when `bgzip` and `tabix` are available.

The default run now produces UI-ready JSON even before EAGLE2 runs. It writes the canonical generated files to `/mnt/f/data/processed/genetics_eagle/results/app/` and also publishes copies into the repo `data/` folder for the app workflow:

- `/mnt/f/data/processed/genetics_eagle/results/app/report_summary.json`
- `/mnt/f/data/processed/genetics_eagle/results/app/shared_snp_quality.json`
- `/mnt/f/data/processed/genetics_eagle/results/app/reference_labels.json`
- `/mnt/f/data/processed/genetics_eagle/results/app/eagle_results_index.json`
- `/mnt/f/data/processed/genetics_eagle/results/phasing_qc/phasing_qc.json`
- `/mnt/d/Python/Genetics/data/report_summary.json`
- `/mnt/d/Python/Genetics/data/shared_snp_quality.json`
- `/mnt/d/Python/Genetics/data/reference_labels.json`
- `/mnt/d/Python/Genetics/data/eagle_results_index.json`
- `/mnt/d/Python/Genetics/data/phasing_qc.json`
- `/mnt/d/Python/Genetics/data/validation_dashboard.json`
- `/mnt/d/Python/Genetics/data/sample_model_outputs.json`

EAGLE2 is installed at `/usr/local/bin/eagle2` from the official Broad/AlkesGroup v2.4.1 bundle. Eagle2 is the default algorithm; the pipeline never passes `--v1`.

To run EAGLE2:

```bash
cd /mnt/d/Python/Genetics
export SKIP_EXTRACTION=1
export RUN_EAGLE=1
export THREADS=8
bash run_pipeline_wsl.sh
```

Default EAGLE2 maps:

- HGDP-aligned data: `/opt/eagle2/Eagle_v2.4.1/tables/genetic_map_hg38_withX.txt.gz`
- 1000 Genomes/build 37 data: `/opt/eagle2/Eagle_v2.4.1/tables/genetic_map_hg19_withX.txt.gz`

## FLARE Local Ancestry

FLARE runs after EAGLE2. EAGLE2 does the phasing; FLARE does the ancestry classification.

The HGDP target phasing step does not phase the HGDP reference VCF itself, so the FLARE path first phases HGDP shared reference VCFs with EAGLE2 non-reference mode:

```bash
/mnt/f/data/processed/genetics_eagle/results/phased_reference/hgdp/
```

Run a chr22 smoke test:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_FLARE=1 FLARE_CHROMS=22 THREADS=4 FLARE_THREADS=4 FLARE_MEMORY_GB=6 bash run_pipeline_wsl.sh
```

Run all autosomes:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_FLARE=1 FLARE_CHROMS=all THREADS=8 FLARE_THREADS=4 FLARE_MEMORY_GB=6 bash run_pipeline_wsl.sh
```

FLARE inputs and outputs:

- Ref panel labels: `/mnt/f/data/processed/genetics_eagle/metadata/hgdp_flare_ref_panel_general.tsv`
- FLARE maps: `/mnt/f/data/processed/genetics_eagle/work/flare_maps/`
- FLARE ancestry VCFs: `/mnt/f/data/processed/genetics_eagle/results/flare/hgdp/`
- Raw segments: `/mnt/f/data/processed/genetics_eagle/results/segments/raw_segments_hgdp.tsv`
- Smoothed segments: `/mnt/f/data/processed/genetics_eagle/results/segments/smoothed_segments_hgdp.tsv`
- App JSON: `/mnt/d/Python/Genetics/data/chromosome_segments_hgdp.json`

The pipeline writes several segment profiles so the HMM cannot hide bridge mistakes:

- Raw/no-HMM: `/mnt/f/data/processed/genetics_eagle/results/app/chromosome_segments_hgdp_raw_no_hmm.json`
- Light HMM: `/mnt/f/data/processed/genetics_eagle/results/app/chromosome_segments_hgdp_light.json`
- Medium HMM: `/mnt/f/data/processed/genetics_eagle/results/app/chromosome_segments_hgdp_medium.json`
- Strong HMM: `/mnt/f/data/processed/genetics_eagle/results/app/chromosome_segments_hgdp_strong.json`
- App default: raw/no-HMM until validation says smoothing is trustworthy.

## Holdout Validation

Before interpreting the target sample, run known-reference holdout validation. The validator removes known HGDP samples from the reference panel, classifies them as unknown targets, and writes predictions plus a confusion matrix.

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_VALIDATE=1 VALIDATE_CHROMS=22 VALIDATION_SAMPLES_PER_LABEL=2 bash run_pipeline_wsl.sh
```

Outputs:

- `/mnt/f/data/processed/genetics_eagle/results/validation/hgdp/chr22/predictions.tsv`
- `/mnt/f/data/processed/genetics_eagle/results/validation/hgdp/chr22/confusion_matrix.tsv`
- `/mnt/f/data/processed/genetics_eagle/results/validation/hgdp/chr22/summary.json`
- `/mnt/d/Python/Genetics/data/validation_hgdp_chr22.json`

## Model Tournament

The tournament runs multiple model configurations against the same held-out reference samples. Current candidates include flat FLARE parameter variants and a broad-first FLARE baseline.

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_TOURNAMENT=1 TOURNAMENT_CHROMS=22 VALIDATION_SAMPLES_PER_LABEL=2 bash run_pipeline_wsl.sh
```

Output:

```bash
/mnt/f/data/processed/genetics_eagle/results/model_tournament/hgdp/chr22/model_tournament_summary.json
/mnt/d/Python/Genetics/data/model_tournament_hgdp_chr22.json
```

## RFMix Comparator

RFMix is available as an independent local ancestry model. It should be interpreted as a comparator until it passes the same holdout validation standard as FLARE. RFMix v2 has non-commercial academic research licensing terms, so check those terms before any other use.

Run a chr22 comparator:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_RFMIX=1 RFMIX_CHROMS=22 THREADS=4 FLARE_THREADS=4 bash run_pipeline_wsl.sh
```

Outputs:

```bash
/mnt/f/data/processed/genetics_eagle/results/rfmix/hgdp_general/MY_SAMPLE.hgdp.chr22.rfmix.rfmix.Q
/mnt/f/data/processed/genetics_eagle/results/rfmix/hgdp_general/MY_SAMPLE.hgdp.chr22.rfmix.msp.tsv
/mnt/d/Python/Genetics/data/sample_model_outputs.json
```

Run RFMix holdout validation:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_RFMIX_VALIDATE=1 RFMIX_VALIDATE_CHROMS=22 VALIDATION_SAMPLES_PER_LABEL=2 bash run_pipeline_wsl.sh
```

Run a small RFMix parameter grid. The grid compares holdout accuracy, tracked bridge errors, and synthetic-mixture calibration:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_RFMIX_GRID=1 RFMIX_VALIDATE_CHROMS=22 RFMIX_GRID_PRESETS=default,shorter_windows bash run_pipeline_wsl.sh
```

Current chr22 diagnostic results:

- RFMix default holdout: 72.97% accuracy, 1 tracked bridge error.
- RFMix shorter windows: 62.16% accuracy, 2 tracked bridge errors.
- Strict synthetic mixtures exclude the synthetic source parents from the reference panel; this avoids parent recognition and is the valid calibration mode.

## Synthetic Admixed Validation Targets

Synthetic mixtures are for validation and calibration only. They are deliberately not added to the reference panel by the pipeline.

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_SIMULATIONS=1 SIMULATION_CHROMS=22 bash run_pipeline_wsl.sh
```

Outputs:

```bash
/mnt/f/data/processed/genetics_eagle/results/simulations/hgdp/chr22/synthetic_admixed_chr22.vcf.gz
/mnt/f/data/processed/genetics_eagle/results/simulations/hgdp/chr22/synthetic_admixed_truth.tsv
```

## App Tabs

The app now separates interpretation from validation:

- Sample models: FLARE flat, FLARE broad-first, RFMix, probability-level meta-model, and haplotype-copy diagnostics.
- Validation: holdout accuracy, bridge-error counts, attractor errors, and model tournament results.
- Quality: shared SNP compatibility and build/reference checks.

Fine ancestry labels are not considered final until they pass autosome-wide validation. Current chr22 outputs are diagnostic.

## HMM Smoothing

The smoothing stage runs after FLARE. It keeps haplotype copy 1 and copy 2 separate when the input has a `copy` column.

```bash
/mnt/f/data/processed/genetics_eagle/results/segments/raw_segments_hgdp.tsv
```

Required columns:

```text
chrom	start	end	label
```

Recommended optional columns:

```text
copy	confidence	snp_count	source
```

Alternatively, raw segment rows may include probability columns such as `prob_Western_European`, `prob_Middle_Eastern`, and `prob_South_Asian`; the HMM uses those as emissions.

Outputs:

```bash
/mnt/f/data/processed/genetics_eagle/results/segments/smoothed_segments_hgdp.tsv
/mnt/f/data/processed/genetics_eagle/results/app/chromosome_segments.json
/mnt/f/data/processed/genetics_eagle/results/app/chromosome_segments_hgdp.json
/mnt/d/Python/Genetics/data/chromosome_segments.json
/mnt/d/Python/Genetics/data/chromosome_segments_hgdp.json
```

Important outputs:

- `/mnt/f/data/processed/genetics_eagle/metadata/hgdp_labels_general.tsv`
- `/mnt/f/data/processed/genetics_eagle/metadata/hgdp_labels_local.tsv`
- `/mnt/f/data/processed/genetics_eagle/metadata/hgdp_population_label_map.tsv`
- `/mnt/f/data/processed/genetics_eagle/metadata/1000genomes_labels.tsv`
- `/mnt/f/data/processed/genetics_eagle/work/shared_snps/1000genomes/shared_snp_summary.tsv`
- `/mnt/f/data/processed/genetics_eagle/work/shared_snps/hgdp/shared_snp_summary.tsv`
- `/mnt/f/data/processed/genetics_eagle/results/eagle2/`
- `/mnt/f/data/processed/genetics_eagle/results/app/report_summary.json`

## Vercel App

The repository root also contains a static Vercel app shell:

- `index.html`
- `styles.css`
- `app.js`
- `vercel.json`

The pipeline now publishes generated app JSON into `data/` automatically. If those JSON files are absent, the deployed app shows a preview shell with pending values.

Deploy from the repository root:

```bash
npx vercel@latest deploy
```

For production:

```bash
npx vercel@latest deploy --prod
```
