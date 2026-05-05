# Lazaridis Stage 1-6 Decision

This document records the result of the staged Lazaridis / EuropeFullyPublic evaluation before running any ancestry model.

## Stage 1: Audit Labels

Dataset audited:

```text
/mnt/f/data/raw/lazaridis_correct/EuropeFullyPublic/vdata.ind
```

Output:

```text
docs/LAZARIDIS_LABEL_AUDIT.md
/mnt/f/data/processed/genetics_eagle/metadata/lazaridis_vdata_labels.tsv
```

The curated modern/reference subset currently includes 909 samples across 9 provisional general labels.

## Stage 2: Exclude Ancient / Outlier / Non-Modeled Labels

Excluded:

- `Ignore_*` labels
- ancient labels
- archaic hominin labels
- primates
- single ancient reference genomes
- labels currently mapped to `Other`

This keeps the Lazaridis panel in the present-day reference role. Ancient samples remain for a later ancient-ancestry stage.

## Stage 3: Provisional Label Hierarchy

Important anti-bias rule:

`Yemen` and `Yemenite_Jew` are grouped inside `Arabian_Levantine`; they are not split into a special target-specific label.

Current general-label counts:

| General label | Samples |
|---|---:|
| Arabian_Levantine | 168 |
| Central_European | 30 |
| Iranian_Caucasus_Anatolian | 269 |
| North_African | 82 |
| Northeast_European | 68 |
| Northwest_North_European | 50 |
| Southeast_European | 26 |
| Southern_European | 95 |
| Southwest_European | 121 |

## Stage 4: Check Sample Counts

The label counts are adequate for broad exploratory work but not perfect for fine-scale Germanic classification.

Useful improvements relative to HGDP:

- `Northwest_North_European` exists, unlike HGDP.
- `Arabian_Levantine` includes Bedouin, Saudi, Yemen, Yemenite Jewish, Jordanian, Syrian, Lebanese, Palestinian, and Druze.
- Southern and Southwest European controls are stronger than HGDP.

Remaining problem:

- Still no true modern German, Dutch, or Danish label.
- Northwest/North European is represented by English, Scottish, Norwegian, Icelandic, and Orcadian proxies.

## Stage 5: Extract Shared SNPs / Density Check

Lazaridis SNP IDs are Affymetrix IDs, not rsIDs, so matching was done by build37 chromosome/position plus allele compatibility.

Output:

```text
/mnt/f/data/processed/genetics_eagle/work/lazaridis_shared_snps/my_lazaridis_vdata_shared_sites.tsv
/mnt/f/data/processed/genetics_eagle/work/lazaridis_shared_snps/my_lazaridis_vdata_shared_summary.json
```

Summary:

| Metric | Value |
|---|---:|
| 23andMe usable autosomal sites | 603,749 |
| Lazaridis autosomal sites | 594,924 |
| Matched compatible sites | 52,955 |
| Matched rate vs Lazaridis | 8.90% |
| Incompatible matched sites | 1 |

Selected chromosomes:

| Chromosome | Matched compatible sites |
|---|---:|
| 1 | 4,630 |
| 2 | 4,454 |
| 6 | 3,631 |
| 10 | 2,953 |
| 17 | 1,654 |
| 21 | 807 |
| 22 | 822 |

## Stage 6: EAGLE2 / Phasing Decision

Decision: do not run EAGLE2 local-ancestry phasing on the Lazaridis intersection yet.

Reason:

- The intersection with 23andMe v5 is only 52,955 autosomal SNPs total.
- Chromosome 22 has only 822 matched SNPs.
- This density is too sparse for reliable haplotype phasing and local ancestry painting with EAGLE2 -> FLARE/RFMix.
- Running EAGLE2 here would produce a phased file, but the phase would likely be unstable and would create another misleading local-ancestry result.

Recommended use of Lazaridis at this stage:

- PCA / projection
- ADMIXTURE-style global ancestry
- qpAdm / f-statistics style tests where appropriate
- global probabilistic classification on genotype likelihood/features, not local ancestry painting

Recommended next move:

Use Lazaridis as the better-balanced modern West-Eurasian **global ancestry reference**, not yet as a haplotype/local-ancestry reference. For local ancestry, we still need denser genotype overlap or a better modern panel in VCF/WGS format.
