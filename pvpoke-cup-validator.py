#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///
"""A tool to validate a PvPoke cup JSON file against the gamemaster data."""

import argparse
import json
import os
import sys
from typing import Any, Dict, Set


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Loads a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    """Main function to parse arguments and run the cup JSON validation."""
    parser = argparse.ArgumentParser(description="Validate a PvPoke cup JSON file against the gamemaster data.")
    parser.add_argument("cup_json_path", help="Path to the cup JSON file (e.g., modifiedlove.json).")

    args = parser.parse_args()

    pvpoke_src_root = os.environ.get("PVPOKE_SRC_ROOT")
    if not pvpoke_src_root:
        print("❌ ERROR: PVPOKE_SRC_ROOT environment variable is not set.", file=sys.stderr)
        print("Please set it to the absolute path of your pvpoke/src directory, e.g.:", file=sys.stderr)
        print("  export PVPOKE_SRC_ROOT=/Users/dottey/git/personal/pvpoke/src", file=sys.stderr)
        exit(1)

    gamemaster_json_path = os.path.join(pvpoke_src_root, "data", "gamemaster.json")
    moves_json_path = os.path.join(pvpoke_src_root, "data", "gamemaster", "moves.json")

    # Load data
    cup_data = load_json_file(args.cup_json_path)
    gamemaster_data = load_json_file(gamemaster_json_path)

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
            f"at '{gamemaster_json_path}'. Aborting."
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

    # Load moves data and extract valid moveIds
    moves_data = load_json_file(moves_json_path)
    gamemaster_move_ids: Set[str] = set()

    for move_entry in moves_data:
        move_id = move_entry.get("moveId")
        if move_id:
            gamemaster_move_ids.add(move_id)

    # Extract all moveIds mentioned in the cup JSON
    cup_mentioned_move_ids: Set[str] = set()

    for section in ["include", "exclude"]:
        for rule in cup_data.get(section, []):
            if isinstance(rule, dict) and rule.get("filterType") == "move" and "values" in rule:
                cup_mentioned_move_ids.update([move_id.upper() for move_id in rule["values"]])

    unknown_moves = cup_mentioned_move_ids - gamemaster_move_ids

    if unknown_moves:
        all_valid = False
        print("\n--- Move Validation Check ---")
        print(
            f"❌ ERROR: The following moveIds from the cup JSON file "
            f"'{args.cup_json_path}' are NOT found in the moves JSON file "
            f"'{moves_json_path}':"
        )
        for move_id in sorted(list(unknown_moves)):
            print(f"   - {move_id}")
    else:
        print(f"✅ All moveIds mentioned in '{args.cup_json_path}' are found in the moves gamemaster.")

    print("\n--- Summary ---")
    if all_valid:
        print("✅ Cup JSON validation PASSED: All mentioned species and moves exist in gamemaster.")
        exit(0)
    else:
        print("❌ Cup JSON validation FAILED: Discrepancies found.")
        exit(1)


if __name__ == "__main__":
    main()
