#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ARABIAN_LEVANTINE = {
    "BedouinA", "BedouinB", "Druze", "Palestinian", "Jordanian", "Syrian",
    "Lebanese", "Saudi", "Yemen", "Yemenite_Jew",
}

NORTHWEST_NORTH_EUROPEAN = {
    "English_Kent_GBR", "English_Cornwall_GBR", "Scottish_Argyll_Bute_GBR",
    "Orcadian", "Norwegian", "Icelandic",
}

NORTHEAST_EUROPEAN = {"Finnish_FIN", "Estonian", "Lithuanian", "Belarusian", "Russian", "Ukrainian_East", "Ukrainian_West"}
CENTRAL_EUROPEAN = {"Czech", "Hungarian_Coriell", "Hungarian_Metspalu"}
SOUTHERN_EUROPEAN = {
    "Italian_Bergamo", "Italian_Tuscan", "Italian_EastSicilian", "Italian_WestSicilian",
    "Italian_South", "Sardinian", "Greek_Comas", "Greek_Coriell", "Maltese", "Cypriot",
}
SOUTHWEST_EUROPEAN = {
    "Basque_French", "Basque_Spanish", "French", "French_South",
    "Spanish_Andalucia_IBS", "Spanish_Aragon_IBS", "Spanish_Baleares_IBS",
    "Spanish_Canarias_IBS", "Spanish_Cantabria_IBS", "Spanish_Castilla_la_Mancha_IBS",
    "Spanish_Castilla_y_Leon_IBS", "Spanish_Cataluna_IBS", "Spanish_Extremadura_IBS",
    "Spanish_Galicia_IBS", "Spanish_Murcia_IBS", "Spanish_Pais_Vasco_IBS",
    "Spanish_Valencia_IBS",
}
SOUTHEAST_EUROPEAN = {"Albanian", "Bulgarian", "Croatian"}
IRANIAN_CAUCASUS_ANATOLIAN = {
    "Adygei", "Armenian", "Balkar", "Chechen", "Abkhasian", "Lezgin", "Nogai",
    "Georgian_Megrels", "Georgian_Jew", "North_Ossetian", "Kumyk", "Turkish",
    "Turkish_Adana", "Turkish_Aydin", "Turkish_Balikesir", "Turkish_Istanbul",
    "Turkish_Kayseri", "Turkish_Trabzon", "Turkish_Jew", "Iranian", "Iranian_Jew",
    "Balochi", "Brahui", "Makrani", "Pathan", "Kurd_WGA",
}
NORTH_AFRICAN = {
    "Egyptian_Comas", "Egyptian_Metspalu", "Mozabite", "Algerian", "Tunisian",
    "Tunisian_Jew", "Libyan_Jew", "Moroccan_Jew", "Saharawi",
}

EXCLUDE_PREFIXES = (
    "Ignore_", "Primate_", "Ancient_", "Neandertal", "Denisovan", "Luxembourg_Mesolithic",
    "GermanStuttgart_LBK", "Tyrolean_Iceman", "Greenland_Saqqaq", "Siberian_Upper_Paleolithic",
    "Siberian_Ice_Age", "Swedish_HunterGatherer", "Swedish_Farmer", "Swedish_Motala", "LaBrana",
    "hg19_reference_sequence",
)


def general_label(label: str) -> str:
    if label in ARABIAN_LEVANTINE:
        return "Arabian_Levantine"
    if label in NORTHWEST_NORTH_EUROPEAN:
        return "Northwest_North_European"
    if label in NORTHEAST_EUROPEAN:
        return "Northeast_European"
    if label in CENTRAL_EUROPEAN:
        return "Central_European"
    if label in SOUTHERN_EUROPEAN:
        return "Southern_European"
    if label in SOUTHWEST_EUROPEAN:
        return "Southwest_European"
    if label in SOUTHEAST_EUROPEAN:
        return "Southeast_European"
    if label in IRANIAN_CAUCASUS_ANATOLIAN:
        return "Iranian_Caucasus_Anatolian"
    if label in NORTH_AFRICAN:
        return "North_African"
    return "Other"


def is_present_day(label: str) -> bool:
    return not any(label.startswith(prefix) for prefix in EXCLUDE_PREFIXES)


def read_ind(path: Path) -> list[dict[str, str]]:
    rows = []
    with path.open(errors="ignore") as handle:
        for index, line in enumerate(handle):
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            sample, sex, label = parts[0], parts[1], parts[-1]
            rows.append({
                "index": str(index),
                "sample": sample,
                "sex": sex,
                "local_label": label,
                "general_label": general_label(label),
                "include": str(is_present_day(label) and general_label(label) != "Other").lower(),
            })
    return rows


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["index", "sample", "sex", "local_label", "general_label", "include"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], dataset_name: str) -> None:
    included = [row for row in rows if row["include"] == "true"]
    local_counts = Counter(row["local_label"] for row in included)
    general_counts = Counter(row["general_label"] for row in included)
    by_general: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for local, count in sorted(local_counts.items()):
        by_general[general_label(local)].append((local, count))

    lines = [
        "# Lazaridis / EuropeFullyPublic Label Audit",
        "",
        f"Dataset audited: `{dataset_name}`",
        "",
        "This audit selects present-day labels from the curated Lazaridis Human Origins panel and proposes unbiased analysis groups before any ancestry model is run.",
        "",
        "Important correction: `Yemen` and `Yemenite_Jew` are grouped inside `Arabian_Levantine`; they are not treated as a special target-specific label.",
        "",
        "## Included General Labels",
        "",
        "| General label | Samples | Local labels |",
        "|---|---:|---|",
    ]
    for label, count in sorted(general_counts.items()):
        locals_text = ", ".join(f"{local} (n={n})" for local, n in sorted(by_general[label]))
        lines.append(f"| {label} | {count} | {locals_text} |")

    lines.extend([
        "",
        "## Excluded / Not Yet Modeled Labels",
        "",
        "Labels marked `Other`, ancient labels, primate labels, archaic hominins, `Ignore_*` outliers, and single ancient reference genomes are excluded from this modern-reference stage.",
        "",
        "## Full Included Local Labels",
        "",
        "| Local label | General label | Samples |",
        "|---|---|---:|",
    ])
    for local, count in sorted(local_counts.items()):
        lines.append(f"| {local} | {general_label(local)} | {count} |")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Lazaridis EuropeFullyPublic present-day labels.")
    parser.add_argument("--ind", required=True, type=Path)
    parser.add_argument("--out-tsv", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args()

    rows = read_ind(args.ind)
    write_tsv(args.out_tsv, rows)
    write_markdown(args.out_md, rows, args.ind.name)
    counts = Counter(row["general_label"] for row in rows if row["include"] == "true")
    print(json.dumps({"includedSamples": sum(counts.values()), "generalCounts": dict(sorted(counts.items()))}, indent=2), flush=True)


if __name__ == "__main__":
    main()
