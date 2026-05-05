# Ancestry Analysis

Pipeline and lightweight report app for preparing 23andMe genotype data against reference panels, running EAGLE2, and publishing app-ready ancestry analysis outputs.

## What This Repository Contains

- WSL genetics pipeline for 23andMe, 1000 Genomes, and HGDP data
- shared-SNP extraction and reference-aligned VCF generation
- HGDP general/local population labeling
- 1000 Genomes population labeling
- EAGLE2 v2.4.1 runner
- optional HMM smoothing for local ancestry segments
- static report UI that reads generated JSON from `data/`

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

## App

Run the static report app locally:

```bash
npm start
```

Then open:

```text
http://localhost:4173
```
