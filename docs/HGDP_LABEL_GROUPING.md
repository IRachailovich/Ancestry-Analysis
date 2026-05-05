# HGDP Label Grouping Audit

This file documents the current HGDP population labels used by the pipeline. It is generated from the raw HGDP metadata plus the grouping rules in `scripts/make_labels.py`.

Important caveat: these are analysis labels, not claims about identity. They are only reference-panel categories used by FLARE/RFMix. The grouping should be treated as provisional until autosome-wide validation supports it.

## Critical Coverage Gaps

- HGDP does not contain German, Dutch, Danish, or Yemeni reference populations in the current panel.
- Current `Western_European` is represented only by Basque, French, and Orcadian.
- Current `Southern_European` is represented only by Bergamo Italian, Sardinian, and Tuscan.
- Current `Middle_Eastern` is represented only by Bedouin, Druze, and Palestinian.
- Because the true source labels of interest are not directly represented, West-Eurasian models can use nearby proxy labels. This can inflate `Southern_European` even when the real ancestry is not Italian/Sardinian/Tuscan.

## Broad Label Groups

- **African**: BantuKenya (n=11), BantuSouthAfrica (n=8), Biaka (n=22), Mandenka (n=22), Mbuti (n=13), San (n=6), Yoruba (n=22)
- **Central_Asian**: Hazara (n=19), Uygur (n=10)
- **East_Asian**: Cambodian (n=9), Dai (n=9), Daur (n=9), Han (n=33), Hezhen (n=9), Japanese (n=27), Lahu (n=8), Miao (n=10), Mongolian (n=9), Naxi (n=8), NorthernHan (n=10), Oroqen (n=9), She (n=10), Tu (n=10), Tujia (n=9), Xibo (n=9), Yi (n=10)
- **European**: Basque (n=23), BergamoItalian (n=12), French (n=28), Orcadian (n=15), Russian (n=25), Sardinian (n=28), Tuscan (n=8)
- **Indigenous_American**: Colombian (n=7), Karitiana (n=12), Maya (n=21), Pima (n=13), Surui (n=8)
- **Middle_Eastern**: Bedouin (n=46), Druze (n=42), Palestinian (n=46)
- **North_African**: Mozabite (n=27)
- **North_Asian**: Yakut (n=25)
- **Oceanian**: Bougainville (n=11), PapuanHighlands (n=9), PapuanSepik (n=8)
- **South_Asian**: Burusho (n=24), Kalash (n=22), Sindhi (n=24)
- **West_Eurasian**: Adygei (n=16), Balochi (n=24), Brahui (n=25), Makrani (n=25), Pathan (n=24)

## General Label Groups

### Caucasus (n=16)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Adygei | EUROPE | 16 | Adygei | West_Eurasian |

### Central_African (n=35)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Biaka | AFRICA | 22 | Biaka | African |
| Mbuti | AFRICA | 13 | Mbuti | African |

### Central_Asian (n=29)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Hazara | CENTRAL_SOUTH_ASIA | 19 | Hazara | Central_Asian |
| Uygur | CENTRAL_SOUTH_ASIA | 10 | Uygur | Central_Asian |

### East_African (n=11)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| BantuKenya | AFRICA | 11 | BantuKenya | African |

### East_Asian (n=189)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Cambodian | EAST_ASIA | 9 | Cambodian | East_Asian |
| Dai | EAST_ASIA | 9 | Dai | East_Asian |
| Daur | EAST_ASIA | 9 | Daur | East_Asian |
| Han | EAST_ASIA | 33 | Han | East_Asian |
| Hezhen | EAST_ASIA | 9 | Hezhen | East_Asian |
| Japanese | EAST_ASIA | 27 | Japanese | East_Asian |
| Lahu | EAST_ASIA | 8 | Lahu | East_Asian |
| Miao | EAST_ASIA | 10 | Miao | East_Asian |
| Naxi | EAST_ASIA | 8 | Naxi | East_Asian |
| NorthernHan | EAST_ASIA | 10 | Han_Northern | East_Asian |
| Oroqen | EAST_ASIA | 9 | Oroqen | East_Asian |
| She | EAST_ASIA | 10 | She | East_Asian |
| Tu | EAST_ASIA | 10 | Tu | East_Asian |
| Tujia | EAST_ASIA | 9 | Tujia | East_Asian |
| Xibo | EAST_ASIA | 9 | Xibo | East_Asian |
| Yi | EAST_ASIA | 10 | Yi | East_Asian |

### Eastern_European (n=25)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Russian | EUROPE | 25 | Russian | European |

### Greater_Iranian (n=98)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Balochi | CENTRAL_SOUTH_ASIA | 24 | Balochi | West_Eurasian |
| Brahui | CENTRAL_SOUTH_ASIA | 25 | Brahui | West_Eurasian |
| Makrani | CENTRAL_SOUTH_ASIA | 25 | Makrani | West_Eurasian |
| Pathan | CENTRAL_SOUTH_ASIA | 24 | Pathan | West_Eurasian |

### Indigenous_American (n=61)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Colombian | AMERICA | 7 | Colombian | Indigenous_American |
| Karitiana | AMERICA | 12 | Karitiana | Indigenous_American |
| Maya | AMERICA | 21 | Maya | Indigenous_American |
| Pima | AMERICA | 13 | Pima | Indigenous_American |
| Surui | AMERICA | 8 | Surui | Indigenous_American |

### Middle_Eastern (n=134)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Bedouin | MIDDLE_EAST | 46 | Bedouin | Middle_Eastern |
| Druze | MIDDLE_EAST | 42 | Druze | Middle_Eastern |
| Palestinian | MIDDLE_EAST | 46 | Palestinian | Middle_Eastern |

### North_African (n=27)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Mozabite | MIDDLE_EAST | 27 | Mozabite | North_African |

### Northeast_Asian (n=9)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Mongolian | EAST_ASIA | 9 | Mongolian | East_Asian |

### Oceanian (n=28)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Bougainville | OCEANIA | 11 | Bougainville | Oceanian |
| PapuanHighlands | OCEANIA | 9 | Papuan_Highlands | Oceanian |
| PapuanSepik | OCEANIA | 8 | Papuan_Sepik | Oceanian |

### Siberian (n=25)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Yakut | EAST_ASIA | 25 | Yakut | North_Asian |

### South_Asian (n=70)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Burusho | CENTRAL_SOUTH_ASIA | 24 | Burusho | South_Asian |
| Kalash | CENTRAL_SOUTH_ASIA | 22 | Kalash | South_Asian |
| Sindhi | CENTRAL_SOUTH_ASIA | 24 | Sindhi | South_Asian |

### Southern_African (n=8)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| BantuSouthAfrica | AFRICA | 8 | BantuSouthAfrica | African |

### Southern_African_Khoisan (n=6)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| San | AFRICA | 6 | San | African |

### Southern_European (n=48)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| BergamoItalian | EUROPE | 12 | Italian_Bergamo | European |
| Sardinian | EUROPE | 28 | Sardinian | European |
| Tuscan | EUROPE | 8 | Tuscan | European |

### West_African (n=44)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Mandenka | AFRICA | 22 | Mandenka | African |
| Yoruba | AFRICA | 22 | Yoruba | African |

### Western_European (n=66)

| Original HGDP population | HGDP region | Samples | Local label | Broad label |
|---|---:|---:|---|---|
| Basque | EUROPE | 23 | Basque | European |
| French | EUROPE | 28 | French | European |
| Orcadian | EUROPE | 15 | Orcadian | European |

## Full Population Mapping

| Original HGDP population | HGDP region | Samples | General label | Broad label | Local label |
|---|---:|---:|---|---|---|
| Adygei | EUROPE | 16 | Caucasus | West_Eurasian | Adygei |
| Balochi | CENTRAL_SOUTH_ASIA | 24 | Greater_Iranian | West_Eurasian | Balochi |
| BantuKenya | AFRICA | 11 | East_African | African | BantuKenya |
| BantuSouthAfrica | AFRICA | 8 | Southern_African | African | BantuSouthAfrica |
| Basque | EUROPE | 23 | Western_European | European | Basque |
| Bedouin | MIDDLE_EAST | 46 | Middle_Eastern | Middle_Eastern | Bedouin |
| BergamoItalian | EUROPE | 12 | Southern_European | European | Italian_Bergamo |
| Biaka | AFRICA | 22 | Central_African | African | Biaka |
| Bougainville | OCEANIA | 11 | Oceanian | Oceanian | Bougainville |
| Brahui | CENTRAL_SOUTH_ASIA | 25 | Greater_Iranian | West_Eurasian | Brahui |
| Burusho | CENTRAL_SOUTH_ASIA | 24 | South_Asian | South_Asian | Burusho |
| Cambodian | EAST_ASIA | 9 | East_Asian | East_Asian | Cambodian |
| Colombian | AMERICA | 7 | Indigenous_American | Indigenous_American | Colombian |
| Dai | EAST_ASIA | 9 | East_Asian | East_Asian | Dai |
| Daur | EAST_ASIA | 9 | East_Asian | East_Asian | Daur |
| Druze | MIDDLE_EAST | 42 | Middle_Eastern | Middle_Eastern | Druze |
| French | EUROPE | 28 | Western_European | European | French |
| Han | EAST_ASIA | 33 | East_Asian | East_Asian | Han |
| Hazara | CENTRAL_SOUTH_ASIA | 19 | Central_Asian | Central_Asian | Hazara |
| Hezhen | EAST_ASIA | 9 | East_Asian | East_Asian | Hezhen |
| Japanese | EAST_ASIA | 27 | East_Asian | East_Asian | Japanese |
| Kalash | CENTRAL_SOUTH_ASIA | 22 | South_Asian | South_Asian | Kalash |
| Karitiana | AMERICA | 12 | Indigenous_American | Indigenous_American | Karitiana |
| Lahu | EAST_ASIA | 8 | East_Asian | East_Asian | Lahu |
| Makrani | CENTRAL_SOUTH_ASIA | 25 | Greater_Iranian | West_Eurasian | Makrani |
| Mandenka | AFRICA | 22 | West_African | African | Mandenka |
| Maya | AMERICA | 21 | Indigenous_American | Indigenous_American | Maya |
| Mbuti | AFRICA | 13 | Central_African | African | Mbuti |
| Miao | EAST_ASIA | 10 | East_Asian | East_Asian | Miao |
| Mongolian | EAST_ASIA | 9 | Northeast_Asian | East_Asian | Mongolian |
| Mozabite | MIDDLE_EAST | 27 | North_African | North_African | Mozabite |
| Naxi | EAST_ASIA | 8 | East_Asian | East_Asian | Naxi |
| NorthernHan | EAST_ASIA | 10 | East_Asian | East_Asian | Han_Northern |
| Orcadian | EUROPE | 15 | Western_European | European | Orcadian |
| Oroqen | EAST_ASIA | 9 | East_Asian | East_Asian | Oroqen |
| Palestinian | MIDDLE_EAST | 46 | Middle_Eastern | Middle_Eastern | Palestinian |
| PapuanHighlands | OCEANIA | 9 | Oceanian | Oceanian | Papuan_Highlands |
| PapuanSepik | OCEANIA | 8 | Oceanian | Oceanian | Papuan_Sepik |
| Pathan | CENTRAL_SOUTH_ASIA | 24 | Greater_Iranian | West_Eurasian | Pathan |
| Pima | AMERICA | 13 | Indigenous_American | Indigenous_American | Pima |
| Russian | EUROPE | 25 | Eastern_European | European | Russian |
| San | AFRICA | 6 | Southern_African_Khoisan | African | San |
| Sardinian | EUROPE | 28 | Southern_European | European | Sardinian |
| She | EAST_ASIA | 10 | East_Asian | East_Asian | She |
| Sindhi | CENTRAL_SOUTH_ASIA | 24 | South_Asian | South_Asian | Sindhi |
| Surui | AMERICA | 8 | Indigenous_American | Indigenous_American | Surui |
| Tu | EAST_ASIA | 10 | East_Asian | East_Asian | Tu |
| Tujia | EAST_ASIA | 9 | East_Asian | East_Asian | Tujia |
| Tuscan | EUROPE | 8 | Southern_European | European | Tuscan |
| Uygur | CENTRAL_SOUTH_ASIA | 10 | Central_Asian | Central_Asian | Uygur |
| Xibo | EAST_ASIA | 9 | East_Asian | East_Asian | Xibo |
| Yakut | EAST_ASIA | 25 | Siberian | North_Asian | Yakut |
| Yi | EAST_ASIA | 10 | East_Asian | East_Asian | Yi |
| Yoruba | AFRICA | 22 | West_African | African | Yoruba |

## 1000 Genomes Label Grouping Audit

This section documents the current 1000 Genomes labels used by the pipeline. It is generated from `/mnt/f/data/processed/genetics_eagle/metadata/1000genomes_labels.tsv`, which is created from the 1000 Genomes sample panel and the grouping rules in `scripts/make_labels.py`.

Important caveat: 1000 Genomes has much better modern European anchors than HGDP for this project, but it still does not contain explicit German, Dutch, or Danish populations.

### 1000 Genomes Coverage Gaps and Strengths

- Stronger than HGDP for the European half because it includes `CEU`, `GBR`, and `FIN`.
- `CEU` is currently labeled `Utah_NW_European`; this is the closest local proxy for North/West European ancestry.
- `GBR` is currently labeled `British`; useful as a Northwest-European proxy.
- `FIN` is currently labeled `Finnish`; useful for North/Northeast European structure, but not Germanic mainland.
- `TSI` is currently labeled `Italian_Tuscany`; useful as a Southern-European control.
- `IBS` is currently labeled `Iberian_Spain`; useful as a Southwest-European control.
- Still missing: explicit German, Dutch, Danish, Austrian, Swedish, Norwegian labels.
- Also weak for Middle Eastern / Arabian ancestry: 1000 Genomes does not include Bedouin, Palestinian, Druze, Yemeni, or similar Arabian/Levantine populations.

### 1000 Genomes Superpopulation Counts

| Original superpopulation code | Pipeline general label | Samples |
|---|---|---:|
| AFR | African | 661 |
| AMR | Admixed_American | 347 |
| EAS | East_Asian | 504 |
| EUR | European | 503 |
| SAS | South_Asian | 489 |

### 1000 Genomes General Label Groups

#### Admixed_American (n=347)

| Population code | Population label used by pipeline | 1000G superpopulation | Samples |
|---|---|---|---:|
| CLM | Colombian_Medellin | AMR | 94 |
| MXL | Mexican_Ancestry_LA | AMR | 64 |
| PEL | Peruvian_Lima | AMR | 85 |
| PUR | Puerto_Rican | AMR | 104 |

#### African (n=661)

| Population code | Population label used by pipeline | 1000G superpopulation | Samples |
|---|---|---|---:|
| ACB | African_Caribbean_Barbados | AFR | 96 |
| ASW | African_Ancestry_SW_US | AFR | 61 |
| ESN | Esan_Nigeria | AFR | 99 |
| GWD | Gambian_Western_Division | AFR | 113 |
| LWK | Luhya_Kenya | AFR | 99 |
| MSL | Mende_Sierra_Leone | AFR | 85 |
| YRI | Yoruba_Ibadan | AFR | 108 |

#### East_Asian (n=504)

| Population code | Population label used by pipeline | 1000G superpopulation | Samples |
|---|---|---|---:|
| CDX | Chinese_Dai | EAS | 93 |
| CHB | Han_Chinese_Beijing | EAS | 103 |
| CHS | Han_Chinese_South | EAS | 105 |
| JPT | Japanese_Tokyo | EAS | 104 |
| KHV | Kinh_Vietnam | EAS | 99 |

#### European (n=503)

| Population code | Population label used by pipeline | 1000G superpopulation | Samples |
|---|---|---|---:|
| CEU | Utah_NW_European | EUR | 99 |
| FIN | Finnish | EUR | 99 |
| GBR | British | EUR | 91 |
| IBS | Iberian_Spain | EUR | 107 |
| TSI | Italian_Tuscany | EUR | 107 |

#### South_Asian (n=489)

| Population code | Population label used by pipeline | 1000G superpopulation | Samples |
|---|---|---|---:|
| BEB | Bengali_Bangladesh | SAS | 86 |
| GIH | Gujarati_Indian_Houston | SAS | 103 |
| ITU | Indian_Telugu_UK | SAS | 102 |
| PJL | Punjabi_Lahore | SAS | 96 |
| STU | Sri_Lankan_Tamil_UK | SAS | 102 |

### Full 1000 Genomes Population Mapping

| Population code | Population label used by pipeline | 1000G superpopulation | Pipeline general label | Samples |
|---|---|---|---|---:|
| ACB | African_Caribbean_Barbados | AFR | African | 96 |
| ASW | African_Ancestry_SW_US | AFR | African | 61 |
| BEB | Bengali_Bangladesh | SAS | South_Asian | 86 |
| CDX | Chinese_Dai | EAS | East_Asian | 93 |
| CEU | Utah_NW_European | EUR | European | 99 |
| CHB | Han_Chinese_Beijing | EAS | East_Asian | 103 |
| CHS | Han_Chinese_South | EAS | East_Asian | 105 |
| CLM | Colombian_Medellin | AMR | Admixed_American | 94 |
| ESN | Esan_Nigeria | AFR | African | 99 |
| FIN | Finnish | EUR | European | 99 |
| GBR | British | EUR | European | 91 |
| GIH | Gujarati_Indian_Houston | SAS | South_Asian | 103 |
| GWD | Gambian_Western_Division | AFR | African | 113 |
| IBS | Iberian_Spain | EUR | European | 107 |
| ITU | Indian_Telugu_UK | SAS | South_Asian | 102 |
| JPT | Japanese_Tokyo | EAS | East_Asian | 104 |
| KHV | Kinh_Vietnam | EAS | East_Asian | 99 |
| LWK | Luhya_Kenya | AFR | African | 99 |
| MSL | Mende_Sierra_Leone | AFR | African | 85 |
| MXL | Mexican_Ancestry_LA | AMR | Admixed_American | 64 |
| PEL | Peruvian_Lima | AMR | Admixed_American | 85 |
| PJL | Punjabi_Lahore | SAS | South_Asian | 96 |
| PUR | Puerto_Rican | AMR | Admixed_American | 104 |
| STU | Sri_Lankan_Tamil_UK | SAS | South_Asian | 102 |
| TSI | Italian_Tuscany | EUR | European | 107 |
| YRI | Yoruba_Ibadan | AFR | African | 108 |

### Immediate Modeling Implication for 1000 Genomes

For the phasing-sensitivity test, 1000 Genomes is a better ancestry reference than HGDP for the European half because it provides `CEU`, `GBR`, and `FIN`. However, 1000 Genomes alone cannot model the Middle Eastern/Yemeni half well, because it lacks Arabian/Levantine reference populations. Therefore, 1000G is useful for testing whether the inflated `Southern_European` signal is caused by missing Northwest-European anchors, but it is not a complete final ancestry panel.

## Immediate Modeling Implication

The inflated `Southern_European` result should not be interpreted literally until we validate a reference panel that contains the missing target populations or redesign the West-Eurasian label hierarchy. In the current HGDP-only setup, `Southern_European` may be acting as a proxy/attractor inside the West-Eurasian space rather than as a reliable Italian-specific assignment.

## Files Used

- Raw metadata: `/mnt/f/data/raw/hgdp/hgdp_wgs.20190516.metadata.txt`
- General labels: `/mnt/f/data/processed/genetics_eagle/metadata/hgdp_labels_general.tsv`
- Broad labels: `/mnt/f/data/processed/genetics_eagle/metadata/hgdp_labels_broad.tsv`
- Local labels: `/mnt/f/data/processed/genetics_eagle/metadata/hgdp_labels_local.tsv`
- Labeling code: `scripts/make_labels.py`
