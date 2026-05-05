#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


HGDP_GENERAL = {
    "Adygei": "Caucasus",
    "Balochi": "Greater_Iranian",
    "BantuKenya": "East_African",
    "BantuSouthAfrica": "Southern_African",
    "Basque": "Western_European",
    "Bedouin": "Middle_Eastern",
    "BergamoItalian": "Southern_European",
    "Biaka": "Central_African",
    "Bougainville": "Oceanian",
    "Brahui": "Greater_Iranian",
    "Burusho": "South_Asian",
    "Cambodian": "East_Asian",
    "Colombian": "Indigenous_American",
    "Dai": "East_Asian",
    "Daur": "East_Asian",
    "Druze": "Middle_Eastern",
    "French": "Western_European",
    "Han": "East_Asian",
    "Hazara": "Central_Asian",
    "Hezhen": "East_Asian",
    "Japanese": "East_Asian",
    "Kalash": "South_Asian",
    "Karitiana": "Indigenous_American",
    "Lahu": "East_Asian",
    "Makrani": "Greater_Iranian",
    "Mandenka": "West_African",
    "Maya": "Indigenous_American",
    "Mbuti": "Central_African",
    "Miao": "East_Asian",
    "Mongolian": "Northeast_Asian",
    "Mozabite": "North_African",
    "Naxi": "East_Asian",
    "NorthernHan": "East_Asian",
    "Orcadian": "Western_European",
    "Oroqen": "East_Asian",
    "Palestinian": "Middle_Eastern",
    "PapuanHighlands": "Oceanian",
    "PapuanSepik": "Oceanian",
    "Pathan": "Greater_Iranian",
    "Pima": "Indigenous_American",
    "Russian": "Eastern_European",
    "San": "Southern_African_Khoisan",
    "Sardinian": "Southern_European",
    "She": "East_Asian",
    "Sindhi": "South_Asian",
    "Surui": "Indigenous_American",
    "Tu": "East_Asian",
    "Tujia": "East_Asian",
    "Tuscan": "Southern_European",
    "Uygur": "Central_Asian",
    "Xibo": "East_Asian",
    "Yakut": "Siberian",
    "Yi": "East_Asian",
    "Yoruba": "West_African",
}

HGDP_LOCAL = {
    "BergamoItalian": "Italian_Bergamo",
    "NorthernHan": "Han_Northern",
    "PapuanHighlands": "Papuan_Highlands",
    "PapuanSepik": "Papuan_Sepik",
}

HGDP_BROAD = {
    "Caucasus": "West_Eurasian",
    "Central_African": "African",
    "Central_Asian": "Central_Asian",
    "East_African": "African",
    "East_Asian": "East_Asian",
    "Eastern_European": "European",
    "Greater_Iranian": "West_Eurasian",
    "Indigenous_American": "Indigenous_American",
    "Middle_Eastern": "Middle_Eastern",
    "North_African": "North_African",
    "Northeast_Asian": "East_Asian",
    "Oceanian": "Oceanian",
    "Siberian": "North_Asian",
    "South_Asian": "South_Asian",
    "Southern_African": "African",
    "Southern_African_Khoisan": "African",
    "Southern_European": "European",
    "West_African": "African",
    "Western_European": "European",
}

KGP_POP = {
    "ACB": "African_Caribbean_Barbados",
    "ASW": "African_Ancestry_SW_US",
    "BEB": "Bengali_Bangladesh",
    "CDX": "Chinese_Dai",
    "CEU": "Utah_NW_European",
    "CHB": "Han_Chinese_Beijing",
    "CHS": "Han_Chinese_South",
    "CLM": "Colombian_Medellin",
    "ESN": "Esan_Nigeria",
    "FIN": "Finnish",
    "GBR": "British",
    "GIH": "Gujarati_Indian_Houston",
    "GWD": "Gambian_Western_Division",
    "IBS": "Iberian_Spain",
    "ITU": "Indian_Telugu_UK",
    "JPT": "Japanese_Tokyo",
    "KHV": "Kinh_Vietnam",
    "LWK": "Luhya_Kenya",
    "MSL": "Mende_Sierra_Leone",
    "MXL": "Mexican_Ancestry_LA",
    "PEL": "Peruvian_Lima",
    "PJL": "Punjabi_Lahore",
    "PUR": "Puerto_Rican",
    "STU": "Sri_Lankan_Tamil_UK",
    "TSI": "Italian_Tuscany",
    "YRI": "Yoruba_Ibadan",
}

KGP_SUPER = {
    "AFR": "African",
    "AMR": "Admixed_American",
    "EAS": "East_Asian",
    "EUR": "European",
    "SAS": "South_Asian",
}


def local_label(population: str) -> str:
    return HGDP_LOCAL.get(population, population)


def write_hgdp_labels(metadata: Path, outdir: Path) -> None:
    general_path = outdir / "hgdp_labels_general.tsv"
    broad_path = outdir / "hgdp_labels_broad.tsv"
    local_path = outdir / "hgdp_labels_local.tsv"
    map_path = outdir / "hgdp_population_label_map.tsv"

    with (
        metadata.open(newline="") as handle,
        general_path.open("w", newline="") as gen_out,
        broad_path.open("w", newline="") as broad_out,
        local_path.open("w", newline="") as loc_out,
    ):
        reader = csv.DictReader(handle, delimiter="\t")
        gen = csv.writer(gen_out, delimiter="\t", lineterminator="\n")
        broad = csv.writer(broad_out, delimiter="\t", lineterminator="\n")
        loc = csv.writer(loc_out, delimiter="\t", lineterminator="\n")
        gen.writerow(["sample", "population", "region", "label"])
        broad.writerow(["sample", "population", "region", "label"])
        loc.writerow(["sample", "population", "region", "label"])
        seen = set()
        for row in reader:
            pop = row["population"]
            if pop not in HGDP_GENERAL:
                raise SystemExit(f"No HGDP general label for population: {pop}")
            sample = row["sample"]
            region = row["region"]
            general = HGDP_GENERAL[pop]
            gen.writerow([sample, pop, region, general])
            broad.writerow([sample, pop, region, HGDP_BROAD[general]])
            loc.writerow([sample, pop, region, local_label(pop)])
            seen.add(pop)

    with map_path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["population", "region_general_label", "local_label"])
        for pop in sorted(seen):
            writer.writerow([pop, HGDP_GENERAL[pop], local_label(pop)])


def write_kgp_labels(panel: Path, outdir: Path) -> None:
    out_path = outdir / "1000genomes_labels.tsv"
    with panel.open(newline="") as handle, out_path.open("w", newline="") as out:
        reader = csv.DictReader(handle, delimiter="\t")
        writer = csv.writer(out, delimiter="\t", lineterminator="\n")
        writer.writerow(["sample", "population", "super_population", "population_label", "general_label", "sex"])
        for row in reader:
            writer.writerow([
                row["sample"],
                row["pop"],
                row["super_pop"],
                KGP_POP.get(row["pop"], row["pop"]),
                KGP_SUPER.get(row["super_pop"], row["super_pop"]),
                row["gender"],
            ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hgdp-metadata", required=True, type=Path)
    parser.add_argument("--kgp-panel", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    write_hgdp_labels(args.hgdp_metadata, args.outdir)
    write_kgp_labels(args.kgp_panel, args.outdir)


if __name__ == "__main__":
    main()
