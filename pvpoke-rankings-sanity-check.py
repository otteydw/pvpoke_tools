#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pandas"]
# ///
"""A tool to validate PvPoke CSV rankings against cup inclusion/exclusion rules."""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Set

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


def load_csv_moves(filepath: str, move_name_to_id_map: Dict[str, str]) -> Set[str]:
    """Loads moves from a CSV file and converts them to gamemaster moveIds.

    Returns a set of unique move IDs (uppercased) found in the CSV.
    """
    df = pd.read_csv(filepath)
    move_columns = ["Fast Move", "Charged Move 1", "Charged Move 2"]

    # Check if all move columns exist
    if not all(col in df.columns for col in move_columns):
        missing_cols = [col for col in move_columns if col not in df.columns]
        raise ValueError(
            f"CSV file '{filepath}' must contain all of the following columns: {move_columns}. Missing: {missing_cols}"
        )

    csv_moves_ids: Set[str] = set()
    for col in move_columns:
        for csv_move_name in df[col].dropna().astype(str).tolist():
            move_id = move_name_to_id_map.get(csv_move_name)
            if move_id:
                csv_moves_ids.add(move_id)
            else:
                print(
                    f"⚠️ WARNING: Could not correlate CSV move '{csv_move_name}' "
                    "to a moveId using gamemaster map. Skipping this entry."
                )

    return csv_moves_ids


def check_shadow_pokemon(
    ranked_pokemon_ids: Set[str], all_pokemon_data: List[Dict[str, Any]], shadow_check_mode: str
) -> bool:
    """Checks for missing released shadow Pokémon from the rankings."""
    print("\n--- Shadow Pokémon Check ---")
    passed = True
    missing_shadow_pokemon = []

    pokemon_data_map = {p["speciesId"]: p for p in all_pokemon_data}

    for species_id in ranked_pokemon_ids:
        if species_id.endswith("_shadow"):
            continue

        shadow_species_id = f"{species_id}_shadow"
        shadow_pokemon = pokemon_data_map.get(shadow_species_id)

        if shadow_pokemon and shadow_pokemon.get("released", False):
            if shadow_species_id not in ranked_pokemon_ids:
                passed = False
                missing_shadow_pokemon.append(shadow_species_id)

    if not passed:
        prefix_emoji = "❌" if shadow_check_mode == "strict" else "⚠️"
        prefix_text = "ERROR" if shadow_check_mode == "strict" else "WARNING"
        print(f"{prefix_emoji} {prefix_text}: The following released shadow Pokémon are MISSING from the CSV rankings:")
        for pokemon_id in sorted(missing_shadow_pokemon):
            print(f"   - {pokemon_id}")
    else:
        print("✅ All relevant released shadow Pokémon are present in the CSV rankings.")

    return passed


def main():
    """Main function to parse arguments and run the sanity checks."""
    parser = argparse.ArgumentParser(description="Validate PvPoke CSV rankings against a cup JSON file.")
    parser.add_argument(
        "csv_path", help="Path to the PvPoke CSV rankings file (e.g., cp1500_modifiedlove_overall_rankings.csv)."
    )
    parser.add_argument("cup_json_path", help="Path to the cup JSON file (e.g., modifiedlove.json).")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output for debugging.")
    parser.add_argument(
        "--shadow-check-mode",
        choices=["off", "warn", "strict"],
        default="strict",
        help=(
            "Mode for shadow Pokémon check: 'off' (disabled), 'warn' (show warnings but don't fail), "
            "or 'strict' (fail on discrepancies). Default is 'strict'."
        ),
    )

    args = parser.parse_args()

    pvpoke_src_root = os.environ.get("PVPOKE_SRC_ROOT")
    if not pvpoke_src_root:
        print("❌ ERROR: PVPOKE_SRC_ROOT environment variable is not set.", file=sys.stderr)
        print("Please set it to the absolute path of your pvpoke/src directory, e.g.:", file=sys.stderr)
        print("  export PVPOKE_SRC_ROOT=/Users/dottey/git/personal/pvpoke/src", file=sys.stderr)
        exit(1)

    gamemaster_json_path = os.path.join(pvpoke_src_root, "data", "gamemaster.json")
    moves_json_path = os.path.join(pvpoke_src_root, "data", "gamemaster", "moves.json")
    pokemon_json_path = os.path.join(pvpoke_src_root, "data", "gamemaster", "pokemon.json")

    # Load data
    gamemaster_data = load_json_file(gamemaster_json_path)
    cup_data = load_json_file(args.cup_json_path)
    all_pokemon_data = load_json_file(pokemon_json_path)

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
            f"at '{gamemaster_json_path}'. Aborting."
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

    # Load moves data
    moves_data = load_json_file(moves_json_path)

    # Create move_name_to_id_map from gamemaster
    move_name_to_id_map: Dict[str, str] = {}
    for move_entry in moves_data:
        move_id = move_entry.get("moveId")
        move_name = move_entry.get("name")
        if move_id and move_name:
            move_name_to_id_map[move_name] = move_id.upper()

    # Extract all valid moveIds from the gamemaster (uppercased for comparison)
    gamemaster_move_ids: Set[str] = set(move_name_to_id_map.values())

    # Extract all forbidden move IDs from cup JSON
    forbidden_moves_from_cup: Set[str] = set()
    for rule in cup_data.get("exclude", []):
        if isinstance(rule, dict) and rule.get("filterType") == "move" and "values" in rule:
            forbidden_moves_from_cup.update([move_id.upper() for move_id in rule["values"]])

    # Validate that all forbidden moves actually exist in the gamemaster
    unknown_forbidden_moves = forbidden_moves_from_cup - gamemaster_move_ids
    if unknown_forbidden_moves:
        all_passed = False
        print("\n--- Cup Configuration Warning (Moves) ---")
        print(
            f"⚠️ WARNING: The following excluded moves in '{args.cup_json_path}' are NOT found in the moves gamemaster:"
        )
        for move_id in sorted(list(unknown_forbidden_moves)):
            print(f"   - {move_id}")

    # Load moves from CSV
    csv_ranked_moves_ids = load_csv_moves(args.csv_path, move_name_to_id_map)

    if args.verbose:
        print(f"DEBUG: csv_ranked_moves: {csv_ranked_moves_ids}")
        print(f"DEBUG: forbidden_moves_from_cup: {forbidden_moves_from_cup}")

    print("\n--- Forbidden Move Check ---")
    unexpected_forbidden_moves_in_csv = forbidden_moves_from_cup.intersection(csv_ranked_moves_ids)

    if unexpected_forbidden_moves_in_csv:
        all_passed = False
        print("❌ ERROR: The following forbidden moves are UNEXPECTEDLY found in the CSV rankings:")
        for move_id in sorted(list(unexpected_forbidden_moves_in_csv)):
            print(f"   - {move_id}")
    else:
        print("✅ No forbidden moves are present in the CSV rankings.")

    if args.shadow_check_mode != "off":
        shadow_check_passed = check_shadow_pokemon(ranked_pokemon_ids, all_pokemon_data, args.shadow_check_mode)
        if args.shadow_check_mode == "strict" and not shadow_check_passed:
            all_passed = False

    print("\n--- Summary ---")
    if all_passed:
        print("✅ Sanity check PASSED: CSV rankings match cup inclusion/exclusion rules.")
        exit(0)
    else:
        print("❌ Sanity check FAILED: Discrepancies found.")
        exit(1)


if __name__ == "__main__":
    main()
