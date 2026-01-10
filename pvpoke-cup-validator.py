#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["requests", "pandas"]
# ///
"""A tool to validate a PvPoke cup JSON file against the gamemaster data."""

import argparse
import json
from typing import Any, Dict, Set


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Loads a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    """Main function to parse arguments and run the cup JSON validation."""
    parser = argparse.ArgumentParser(description="Validate a PvPoke cup JSON file against the gamemaster data.")
    parser.add_argument("cup_json_path", help="Path to the cup JSON file (e.g., modifiedlove.json).")
    parser.add_argument("gamemaster_json_path", help="Path to the gamemaster JSON file (e.g., gamemaster.json).")

    args = parser.parse_args()

    # Load data
    cup_data = load_json_file(args.cup_json_path)
    gamemaster_data = load_json_file(args.gamemaster_json_path)

    # Extract all valid speciesIds from the gamemaster
    gamemaster_species_ids: Set[str] = set()
    pokemon_entries = []
    if isinstance(gamemaster_data, dict) and "pokemon" in gamemaster_data:
        pokemon_entries = gamemaster_data.get("pokemon", [])
    elif isinstance(gamemaster_data, list):
        # Assume it's a list of pokemon if not an object with 'pokemon' key
        pokemon_entries = gamemaster_data

    if not pokemon_entries:
        print(
            f"❌ ERROR: Could not find 'pokemon' array or valid entries in gamemaster JSON "
            f"at '{args.gamemaster_json_path}'. Aborting."
        )
        exit(1)

    for entry in pokemon_entries:
        species_id = entry.get("speciesId")
        if species_id:
            gamemaster_species_ids.add(species_id)

    # Extract all speciesIds mentioned in the cup JSON
    cup_mentioned_species_ids: Set[str] = set()

    for rule in cup_data.get("include", []):
        if rule.get("filterType") == "id" and "values" in rule:
            cup_mentioned_species_ids.update(rule["values"])

    for rule in cup_data.get("exclude", []):
        if isinstance(rule, str):  # Direct string exclusion
            cup_mentioned_species_ids.add(rule)
        elif isinstance(rule, dict) and rule.get("filterType") == "id" and "values" in rule:
            cup_mentioned_species_ids.update(rule["values"])

    # Perform validation
    all_valid = True
    unknown_species = cup_mentioned_species_ids - gamemaster_species_ids

    if unknown_species:
        all_valid = False
        print("\n--- Validation Check ---")
        print(
            f"❌ ERROR: The following Pokémon speciesIds from the cup JSON file "
            f"'{args.cup_json_path}' are NOT found in the gamemaster JSON file "
            f"'{args.gamemaster_json_path}':"
        )
        for species_id in sorted(list(unknown_species)):
            print(f"   - {species_id}")
    else:
        print(f"✅ All Pokémon speciesIds mentioned in '{args.cup_json_path}' are found in the gamemaster.")

    print("\n--- Summary ---")
    if all_valid:
        print("✅ Cup JSON validation PASSED: All mentioned species exist in gamemaster.")
        exit(0)
    else:
        print("❌ Cup JSON validation FAILED: Discrepancies found.")
        exit(1)


if __name__ == "__main__":
    main()
