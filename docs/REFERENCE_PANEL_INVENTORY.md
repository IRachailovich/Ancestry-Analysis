# Reference Panel Inventory for Modern Ancestry Modeling

This note summarizes the local datasets currently present under `/mnt/f/data/raw` and whether they can help fix the missing Germanic / Northwest-European reference problem.

## Bottom Line

The current HGDP-only reference is not adequate for Germanic / Northwest-European ancestry. HGDP has Basque, French, and Orcadian as `Western_European`, but no German, Dutch, Danish, or strong North-Central European panel.

The best local improvement is `lazaridis_correct/EuropeFullyPublic`, because it contains present-day Northwest/Northern European labels. However, it still does not contain a real modern German/Dutch/Danish group. It is useful, but it is not the final answer.

## Local Datasets

### `/mnt/f/data/raw/hgdp`

Modern WGS panel already used in the pipeline.

Useful labels:

- French: 28
- Basque: 23
- Orcadian: 15
- Bedouin: 46
- Druze: 42
- Palestinian: 46
- Sardinian: 28
- Bergamo Italian: 12
- Tuscan: 8

Problem:

- No German
- No Dutch
- No Danish
- No modern Scandinavian beyond Orcadian proxy
- `Southern_European` can become a West-Eurasian proxy/attractor

### `/mnt/f/data/raw/1000genomes`

Modern phased/WGS VCFs. This is technically the easiest clean reference source because it is already chromosome VCF data.

Relevant populations:

- CEU: Utah residents with Northern/Western European ancestry
- GBR: British in England and Scotland
- FIN: Finnish
- IBS: Iberian Spanish
- TSI: Toscani/Italian Tuscan

Problem:

- No German
- No Dutch
- No Danish
- No explicit Northwest-European mainland labels

Use:

- Strong scaffold for broad modern European vs Middle Eastern/global structure.
- Good immediate replacement for HGDP-only European anchors.
- Not enough for fine German/Dutch/Danish resolution.

### `/mnt/f/data/raw/lazaridis_correct/EuropeFullyPublic`

EIGENSTRAT data with present-day populations. This is not just ancient data.

Useful present-day labels in `data.ind`:

- English: 10
- Scottish: 4
- Norwegian: 11
- Icelandic: 12
- Finnish: 7
- Czech: 10
- Lithuanian: 10
- Belarusian: 10
- Estonian: 10
- French: 25
- French South: 7
- Basque: 29
- Orcadian: 13
- Sardinian: 27
- Tuscan: 8
- BedouinA: 25
- BedouinB: 19
- Druze: 39
- Palestinian: 38
- Yemen: 6
- Yemenite Jew: 8

Useful labels in `release.ind` / `vdata.ind`:

- English Cornwall GBR: 5
- English Kent GBR: 5
- Scottish Argyll Bute GBR: 4
- Norwegian: 11
- Icelandic: 12
- Finnish FIN: 7-8
- GermanStuttgart LBK: 1, but this is ancient LBK, not modern German

Problem:

- Still no real modern German panel
- Still no Dutch
- Still no Danish
- EIGENSTRAT format needs conversion/alignment before FLARE/RFMix local ancestry workflows

Use:

- Very useful for PCA/admixture/global model testing.
- Useful as a medium-term source for better Northwest/Northern European anchors.
- Not sufficient by itself for high-confidence Germanic fine labeling.

### `/mnt/f/data/raw/aadr`

Allen Ancient DNA Resource, mostly ancient, with some present-day `.DG` labels.

Relevant modern-ish labels in `v54.1_1240K_public.ind`:

- CEU.DG: 99
- GBR.DG: 91
- FIN.DG: 97
- Basque.DG: 23
- French.DG: 28
- Italian_North.DG: 20
- TSI.DG: 107
- IBS.DG: 103
- BedouinA.DG: 25
- BedouinB.DG: 21
- Druze.DG: 41
- Palestinian.DG: 38
- Norwegian.DG: 1
- English.DG: 2
- Icelandic.DG: 2
- Orcadian.DG: 17

Important warning:

Most German/Denmark/Sweden labels in AADR are ancient or medieval, not present-day reference populations. They should not be used as modern ancestry labels in this stage.

Use:

- Useful for ancient-stage analysis later.
- Present-day `.DG` labels can help global ancestry checks, but AADR does not solve modern German/Dutch/Danish.

### `/mnt/f/data/raw/sgdp`

Only metadata is currently local, not the full genotypes.

Relevant labels:

- Norwegian: 1
- English: 2
- Icelandic: 2
- Finnish: 3
- French: 3
- Basque: 2
- Orcadian: 2
- Palestinian: 3
- Yemenite Jew: 2

Problem:

- Too small for fine ancestry classification.
- Full genotype data is not present locally.

Use:

- Not enough as a primary reference.

### `/mnt/f/data/raw/reich_recent`

Mostly ancient/specialized publication datasets. Some contain modern or recent populations, but none appear to be a large modern German/Dutch/Danish reference panel from the current inventory.

Use:

- Keep for later ancient ancestry stage.
- Do not use ancient Germanic/Saxon/Viking/medieval samples as modern German/Dutch/Danish references in the current model.

## Best Next Reference Strategy

1. Keep HGDP for broad global coverage.
2. Add 1000 Genomes as the modern WGS scaffold, especially CEU, GBR, FIN, IBS, TSI.
3. Add Lazaridis `EuropeFullyPublic` for exploratory present-day European labels after conversion/alignment.
4. Do not treat ancient Germanic/Saxon/Viking/Medieval samples as modern labels.
5. Seek a real modern European dataset with German, Dutch, Danish, Swedish, Norwegian, British/Irish, and regional European labels.

## External Dataset Wish List

The ideal external panel would include:

- German
- Dutch
- Danish
- Norwegian
- Swedish
- British / English / Scottish / Irish
- Austrian / Swiss German if possible
- French, North Italian, Iberian, Balkan, Greek for neighboring controls
- Yemen / Arabian Peninsula, Bedouin, Palestinian, Druze, Levantine controls

The most promising known direction is a modern European population dataset such as POPRES or a similar controlled-access European cohort. Public datasets like 1000 Genomes and SGDP are useful but do not fully solve the German/Dutch/Danish gap.
