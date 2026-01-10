#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["requests", "pandas"]
# ///
"""A tool to validate PvPoke CSV rankings against cup inclusion/exclusion rules."""

import argparse
import json
from typing import Any, Dict, List

import pandas as pd


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Loads a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv_pokemon_ids(filepath: str, species_name_to_id_map: Dict[str, str]) -> List[str]:
    """Loads Pokémon names from a CSV, correlates them with speciesIds using the gamemaster map.

    Returns a list of speciesIds found in the CSV.
    """
    df = pd.read_csv(filepath)
    if "Pokemon" not in df.columns:
        raise ValueError(f"CSV file '{filepath}' must contain a 'Pokemon' column.")

    correlated_ids = []
    for csv_pokemon_name in df["Pokemon"].tolist():
        # Direct, case-sensitive lookup only, as per new assumption
        species_id = species_name_to_id_map.get(csv_pokemon_name)

        if species_id:
            correlated_ids.append(species_id)
        else:
            print(
                f"⚠️ WARNING: Could not correlate CSV Pokémon '{csv_pokemon_name}' "
                "to a speciesId using gamemaster map. Skipping this entry."
            )

    return correlated_ids


def main():
    """Main function to parse arguments and run the sanity checks."""
    parser = argparse.ArgumentParser(description="Validate PvPoke CSV rankings against a cup JSON file.")
    parser.add_argument(
        "csv_path", help="Path to the PvPoke CSV rankings file (e.g., cp1500_modifiedlove_overall_rankings.csv)."
    )
    parser.add_argument("cup_json_path", help="Path to the cup JSON file (e.g., modifiedlove.json).")
    parser.add_argument(
        "gamemaster_json_path",
        help="Path to the gamemaster JSON file (e.g., gamemaster.json).",
        # Not strictly used in this simplest form, but required by prompt.
    )

    args = parser.parse_args()

    # Load data
    gamemaster_data = load_json_file(args.gamemaster_json_path)
    cup_data = load_json_file(args.cup_json_path)

    # Create species_name_to_id_map from gamemaster
    species_name_to_id_map = {}
    pokemon_entries = []
    if isinstance(gamemaster_data, dict) and "pokemon" in gamemaster_data:
        pokemon_entries = gamemaster_data.get("pokemon", [])
    elif isinstance(gamemaster_data, list):
        pokemon_entries = gamemaster_data

    if not pokemon_entries:
        print(
            f"❌ ERROR: Could not find 'pokemon' array or valid entries in gamemaster JSON "
            f"at '{args.gamemaster_json_path}'. Aborting."
        )
        exit(1)

    for entry in pokemon_entries:
        species_id = entry.get("speciesId")
        species_name = entry.get("speciesName")
        if species_id and species_name:
            # Store original speciesName as key, as per new assumption of exact match
            species_name_to_id_map[species_name] = species_id

    ranked_pokemon_ids = set(load_csv_pokemon_ids(args.csv_path, species_name_to_id_map))

    # Extract required and forbidden pokemon IDs from cup JSON
    required_pokemon_ids = set()
    forbidden_pokemon_ids = set()

    for rule in cup_data.get("include", []):
        if rule.get("filterType") == "id" and "values" in rule:
            for pokemon_id in rule["values"]:
                required_pokemon_ids.add(pokemon_id)

    # Simple direct exclusion, assuming 'exclude' values are speciesIds
    for pokemon_id in cup_data.get("exclude", []):
        if isinstance(pokemon_id, str):  # Direct string exclusion
            forbidden_pokemon_ids.add(pokemon_id)
        elif isinstance(pokemon_id, dict) and pokemon_id.get("filterType") == "id" and "values" in pokemon_id:
            for val in pokemon_id["values"]:
                forbidden_pokemon_ids.add(val)

    # Perform sanity checks
    all_passed = True

    print("\n--- Inclusion Check ---")
    missing_required = required_pokemon_ids - ranked_pokemon_ids
    if missing_required:
        all_passed = False
        print("❌ ERROR: The following required Pokémon are MISSING from the CSV rankings:")
        for pokemon_id in sorted(list(missing_required)):
            print(f"   - {pokemon_id}")
    else:
        print("✅ All required Pokémon are present in the CSV rankings.")

    print("\n--- Exclusion Check ---")
    unexpected_forbidden = forbidden_pokemon_ids.intersection(ranked_pokemon_ids)
    if unexpected_forbidden:
        all_passed = False
        print("❌ ERROR: The following forbidden Pokémon are UNEXPECTEDLY found in the CSV rankings:")
        for pokemon_id in sorted(list(unexpected_forbidden)):
            print(f"   - {pokemon_id}")
    else:
        print("✅ No forbidden Pokémon are present in the CSV rankings.")

    print("\n--- Summary ---")
    if all_passed:
        print("✅ Sanity check PASSED: CSV rankings match cup inclusion/exclusion rules.")
        exit(0)
    else:
        print("❌ Sanity check FAILED: Discrepancies found.")
        exit(1)


if __name__ == "__main__":
    main()
