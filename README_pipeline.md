# Genetics EAGLE2 WSL Pipeline

This workflow reads the raw data in `/mnt/f/data/raw` and writes derived files to `/mnt/f/data/processed/genetics_eagle`.

Steps:

1. Create HGDP general and local labels plus 1000 Genomes labels.
2. Load the 23andMe build 37 raw file.
3. Stream each reference VCF by chromosome and keep the maximum set of shared compatible `rsID` SNPs.
4. Align the target VCF coordinates to the reference VCF coordinates by copying `CHROM/POS/REF/ALT` from the matching reference `rsID`.
5. Write app-facing JSON summaries for the ancestry report UI.
6. Optionally run EAGLE2 twice: once with HGDP reference plus generalized HGDP labels, once with 1000 Genomes reference.
7. If `results/segments/raw_segments.tsv` exists, smooth local ancestry calls with an HMM and publish chromosome-painting JSON.

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

## HMM Smoothing

The smoothing stage is optional and runs after EAGLE2 if this file exists:

```bash
/mnt/f/data/processed/genetics_eagle/results/segments/raw_segments.tsv
```

Required columns:

```text
chrom	start	end	label
```

Recommended optional columns:

```text
confidence	snp_count	source
```

Alternatively, raw segment rows may include probability columns such as `prob_Western_European`, `prob_Middle_Eastern`, and `prob_South_Asian`; the HMM uses those as emissions.

Outputs:

```bash
/mnt/f/data/processed/genetics_eagle/results/segments/smoothed_segments.tsv
/mnt/f/data/processed/genetics_eagle/results/app/chromosome_segments.json
/mnt/d/Python/Genetics/data/chromosome_segments.json
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
