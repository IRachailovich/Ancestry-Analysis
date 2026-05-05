# Ancestry Analysis

Pipeline and lightweight report app for preparing 23andMe genotype data against reference panels, running EAGLE2, and publishing app-ready ancestry analysis outputs.

## What This Repository Contains

- WSL genetics pipeline for 23andMe, 1000 Genomes, and HGDP data
- shared-SNP extraction and reference-aligned VCF generation
- HGDP general/local population labeling
- 1000 Genomes population labeling
- EAGLE2 v2.4.1 runner
- FLARE local ancestry runner
- RFMix local ancestry comparator
- holdout validation, model-tournament, and synthetic-admixture calibration helpers
- optional HMM smoothing for FLARE local ancestry segments
- static report UI with Report, Sample models, Validation, and Quality tabs

## Main Workflow

From WSL:

```bash
cd /mnt/d/Python/Genetics
bash run_pipeline_wsl.sh
```

After shared-SNP extraction finishes, run EAGLE2:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_EAGLE=1 THREADS=8 bash run_pipeline_wsl.sh
```

After EAGLE2, run a chr22 FLARE smoke test:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_FLARE=1 FLARE_CHROMS=22 THREADS=4 FLARE_THREADS=4 FLARE_MEMORY_GB=6 bash run_pipeline_wsl.sh
```

Then run FLARE across all autosomes:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_FLARE=1 FLARE_CHROMS=all THREADS=8 FLARE_THREADS=4 FLARE_MEMORY_GB=6 bash run_pipeline_wsl.sh
```

Run an unbiased HGDP holdout validation before trusting the model:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_VALIDATE=1 VALIDATE_CHROMS=22 VALIDATION_SAMPLES_PER_LABEL=2 bash run_pipeline_wsl.sh
```

Run the first model tournament:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_TOURNAMENT=1 TOURNAMENT_CHROMS=22 VALIDATION_SAMPLES_PER_LABEL=2 bash run_pipeline_wsl.sh
```

Run the independent RFMix chr22 comparator:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_RFMIX=1 RFMIX_CHROMS=22 THREADS=4 FLARE_THREADS=4 bash run_pipeline_wsl.sh
```

Run RFMix validation and a small parameter check:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_RFMIX_VALIDATE=1 RFMIX_VALIDATE_CHROMS=22 VALIDATION_SAMPLES_PER_LABEL=2 bash run_pipeline_wsl.sh
SKIP_EXTRACTION=1 RUN_RFMIX_GRID=1 RFMIX_VALIDATE_CHROMS=22 RFMIX_GRID_PRESETS=default,shorter_windows bash run_pipeline_wsl.sh
```

Create synthetic admixed targets for validation/calibration only:

```bash
cd /mnt/d/Python/Genetics
SKIP_EXTRACTION=1 RUN_SIMULATIONS=1 SIMULATION_CHROMS=22 bash run_pipeline_wsl.sh
```

## Output Locations

Main generated outputs are written outside the repo:

```bash
/mnt/f/data/processed/genetics_eagle
```

App-facing JSON is also copied into:

```bash
data/
```

The chromosome view uses:

```bash
data/phasing_qc.json
data/chromosome_segments_hgdp.json
data/validation_hgdp_chr22.json
data/model_tournament_hgdp_chr22.json
data/validation_dashboard.json
data/sample_model_outputs.json
```

## Documentation

Detailed pipeline notes:

```text
README_pipeline.md
```

UI integration notes:

```text
UI_INTEGRATION_BRIEF.md
```

HGDP label grouping audit:

```text
docs/HGDP_LABEL_GROUPING.md
```

Lazaridis/EuropeFullyPublic modern-label audit and phasing decision:

```text
docs/LAZARIDIS_LABEL_AUDIT.md
docs/LAZARIDIS_STAGE_DECISION.md
```

## App

Run the static report app locally:

```bash
npm start
```

Then open:

```text
http://localhost:4173
```
