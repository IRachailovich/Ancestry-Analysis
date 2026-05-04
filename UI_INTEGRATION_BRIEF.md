# Genetic Ancestry App UI Integration Brief

## Chosen Direction

Use **Option 5** as the main app experience: a consumer-friendly ancestry report that turns the pipeline outputs into clear, confidence-aware results. Use **Option 2** as a secondary "Explore Map" view for geographic context and migration-style exploration.

Concept image:

`assets/ui-concepts/ancestry-ui-options.png`

## How This Fits The Current Pipeline

The current repo is building the computation layer:

- `scripts/make_labels.py` creates HGDP and 1000 Genomes population labels.
- `scripts/extract_shared_snps.py` converts 23andMe calls into reference-aligned shared SNP VCFs.
- `scripts/run_eagle2.py` runs EAGLE2 against HGDP and 1000 Genomes references.
- `run_pipeline_wsl.sh` orchestrates the full WSL pipeline.

The UI should not talk directly to raw VCFs first. Add a small result-normalization layer that converts pipeline outputs into app-friendly JSON files.

## Recommended Product Structure

### 1. Report Dashboard

Main Option 5 screen.

Show:

- ancestry composition cards
- confidence ranges
- top reference matches
- cohort/reference source used, such as HGDP or 1000 Genomes
- data quality summary from shared SNP counts

Suggested inputs:

- `metadata/hgdp_labels_general.tsv`
- `metadata/1000genomes_labels.tsv`
- `work/shared_snps/*/shared_snp_summary.tsv`
- future ancestry-inference summaries derived from EAGLE2 results

### 2. Chromosome View

Use chromosome painting as the technical drilldown screen.

Show:

- chromosomes 1-22
- ancestry segments
- per-segment confidence
- reference population label
- source dataset toggle: HGDP / 1000 Genomes

Suggested inputs:

- parsed EAGLE2 output per chromosome
- labels copied into `results/eagle2/*/labels_used.tsv`

### 3. Explore Map

Use Option 2 here, not as the homepage.

Show:

- region-level ancestry percentages
- map markers for matched reference populations
- broad regional grouping first, local population second
- dataset/source filters

Suggested inputs:

- population label maps from `metadata/`
- a curated population-to-coordinate lookup added later

### 4. Analysis Quality

Keep this visible but calm.

Show:

- usable 23andMe rsID count
- compatible SNPs by chromosome
- same-coordinate vs lifted/reference-aligned SNP counts
- skipped/incompatible variants

Suggested inputs:

- `shared_snp_summary.tsv`
- extraction log in `logs/extract_shared_snps.log`

## Next Engineering Step

Use `scripts/build_report_json.py`, which writes:

- `results/app/report_summary.json`
- `results/app/shared_snp_quality.json`
- `results/app/reference_labels.json`
- `results/app/eagle_results_index.json`
- later, `results/app/chromosome_segments.json` after the exact EAGLE2 output format is finalized

That gives the future frontend a stable contract while the genetics pipeline keeps evolving.
