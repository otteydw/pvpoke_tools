#!/usr/bin/env -S uv run --quiet --script
# /// script
# ///
"""A tool to validate PvPoke cup data within a zip archive against cup rules."""

import argparse
import json
import os
import tempfile
import zipfile
from typing import Any, Dict, Set


def load_json_file(filepath: str) -> Any:
    """Loads a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_cup_data_from_json(cup_data: Dict[str, Any]) -> tuple[Set[str], Set[str], Set[str], Set[str]]:
    """Extracts required/forbidden species and moves from cup JSON data.

    Returns (required_species, forbidden_species, required_moves, forbidden_moves).
    """
    required_species_ids: Set[str] = set()
    forbidden_species_ids: Set[str] = set()
    forbidden_move_ids: Set[str] = set()
    required_move_ids: Set[str] = set()  # This is not strictly required by the prompt, but good to have a placeholder

    for rule in cup_data.get("include", []):
        if rule.get("filterType") == "id" and "values" in rule:
            required_species_ids.update(rule["values"])
        if rule.get("filterType") == "move" and "values" in rule:
            required_move_ids.update(move_id.upper() for move_id in rule["values"])

    for rule in cup_data.get("exclude", []):
        if isinstance(rule, str):  # Direct string exclusion for species
            forbidden_species_ids.add(rule)
        elif isinstance(rule, dict):
            if rule.get("filterType") == "id" and "values" in rule:
                forbidden_species_ids.update(rule["values"])
            if rule.get("filterType") == "move" and "values" in rule:
                forbidden_move_ids.update(move_id.upper() for move_id in rule["values"])

    return required_species_ids, forbidden_species_ids, required_move_ids, forbidden_move_ids


def get_pokemon_and_moves_from_data_file(data: Any) -> tuple[Set[str], Set[str]]:
    """Extracts species IDs and moves from a list of Pokemon data (e.g., overrides or rankings).

    Returns (pokemon_ids, move_ids).
    """
    pokemon_ids: Set[str] = set()
    move_ids: Set[str] = set()

    for entry in data:
        species_id = entry.get("speciesId")
        if species_id:
            pokemon_ids.add(species_id)

        fast_move = entry.get("fastMove")
        if fast_move:
            move_ids.add(fast_move.upper())

        charged_moves = entry.get("chargedMoves", [])
        for cm in charged_moves:
            move_ids.add(cm.upper())

    return pokemon_ids, move_ids


def main():
    """Main function to parse arguments and run the validation process."""
    parser = argparse.ArgumentParser(description="Validate PvPoke cup data within a zip archive against cup rules.")
    parser.add_argument("zip_file", help="Path to the zip archive containing cup data.")

    args = parser.parse_args()

    pvpoke_src_root = os.environ.get("PVPOKE_SRC_ROOT")

    if not pvpoke_src_root:
        print(
            "Error: PVPOKE_SRC_ROOT environment variable is not set. \n"
            "            Please set it to the root directory of your PvPoke source files "
            "(e.g., /var/www/builder.devon.gg/public_html/pvpoke/src)."
        )
        exit(1)

    gamemaster_pokemon_path = os.path.join(pvpoke_src_root, "data", "gamemaster", "pokemon.json")
    gamemaster_moves_path = os.path.join(pvpoke_src_root, "data", "gamemaster", "moves.json")

    # Validate that gamemaster files exist
    if not os.path.exists(gamemaster_pokemon_path):
        print(
            f"Error: Gamemaster pokemon.json not found at '{gamemaster_pokemon_path}'. "
            "Please ensure PVPOKE_SRC_ROOT is correctly set and the file exists."
        )
        exit(1)
    if not os.path.exists(gamemaster_moves_path):
        print(
            f"Error: Gamemaster moves.json not found at '{gamemaster_moves_path}'. "
            "Please ensure PVPOKE_SRC_ROOT is correctly set and the file exists."
        )
        exit(1)

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Unzipping {args.zip_file} to temporary directory: {temp_dir}")

        # 1. Unzip the file
        with zipfile.ZipFile(args.zip_file, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # 2. Dynamically determine the cup shortname
        # Assumes zip contains a single root directory named after the cup
        cup_shortname = ""
        for item in os.listdir(temp_dir):
            if os.path.isdir(os.path.join(temp_dir, item)):
                cup_shortname = item
                break

        if not cup_shortname:
            print("Error: Could not determine cup shortname from zip archive structure.")
            exit(1)

        print(f"Detected cup shortname: {cup_shortname}")

        # Construct paths to relevant files
        cup_file_path = os.path.join(temp_dir, cup_shortname, "cupfile", f"{cup_shortname}.json")
        overrides_base_path = os.path.join(temp_dir, cup_shortname, "overrides", cup_shortname)
        rankings_base_path = os.path.join(temp_dir, cup_shortname, "rankings", cup_shortname)

        # Ensure paths exist
        if not os.path.exists(cup_file_path):
            print(f"Error: Cup definition file not found at {cup_file_path}")
            exit(1)

        # Load gamemaster data for full validation
        gamemaster_pokemon_data = load_json_file(gamemaster_pokemon_path)
        gamemaster_moves_data = load_json_file(gamemaster_moves_path)

        # Create gamemaster species and move ID sets
        gamemaster_species_ids: Set[str] = set()
        for entry in gamemaster_pokemon_data:
            species_id = entry.get("speciesId")
            if species_id:
                gamemaster_species_ids.add(species_id)

        gamemaster_all_move_ids: Set[str] = set()
        for entry in gamemaster_moves_data:
            move_id = entry.get("moveId")
            if move_id:
                gamemaster_all_move_ids.add(move_id.upper())  # Ensure uppercase for consistent comparison

        # Load cup definition
        cup_definition = load_json_file(cup_file_path)

        required_species, forbidden_species, required_moves, forbidden_moves = extract_cup_data_from_json(
            cup_definition
        )

        all_valid = True

        # Validate overrides file
        print(f"\n--- Validating Overrides for {cup_shortname} ---")
        overrides_files = [
            os.path.join(overrides_base_path, f) for f in os.listdir(overrides_base_path) if f.endswith(".json")
        ]

        for ov_file in overrides_files:
            print(f"  Processing {os.path.basename(ov_file)}")
            overrides_data = load_json_file(ov_file)
            override_pokemon_ids, override_move_ids = get_pokemon_and_moves_from_data_file(overrides_data)

            # Species validation
            unknown_override_species = override_pokemon_ids - gamemaster_species_ids
            if unknown_override_species:
                all_valid = False
                print(f"    ❌ ERROR: Unknown species in {os.path.basename(ov_file)}:")
                for species_id in sorted(list(unknown_override_species)):
                    print(f"       - {species_id}")

            # Move validation
            unknown_override_moves = override_move_ids - gamemaster_all_move_ids
            if unknown_override_moves:
                all_valid = False
                print(f"    ❌ ERROR: Unknown moves in {os.path.basename(ov_file)}:")
                for move_id in sorted(list(unknown_override_moves)):
                    print(f"       - {move_id}")

            # Forbidden species check
            forbidden_ov_species_found = forbidden_species.intersection(override_pokemon_ids)
            if forbidden_ov_species_found:
                all_valid = False
                print(f"    ❌ ERROR: Forbidden species found in {os.path.basename(ov_file)}:")
                for species_id in sorted(list(forbidden_ov_species_found)):
                    print(f"       - {species_id}")

            # Forbidden move check
            forbidden_ov_moves_found = forbidden_moves.intersection(override_move_ids)
            if forbidden_ov_moves_found:
                all_valid = False
                print(f"    ❌ ERROR: Forbidden moves found in {os.path.basename(ov_file)}:")
                for move_id in sorted(list(forbidden_ov_moves_found)):
                    print(f"       - {move_id}")

        # Validate rankings files
        print(f"\n--- Validating Rankings for {cup_shortname} ---")
        for root, dirs, files in os.walk(rankings_base_path):
            for file in files:
                if file.endswith(".json"):
                    ranking_file_path = os.path.join(root, file)
                    print(f"  Processing {os.path.relpath(ranking_file_path, rankings_base_path)}")

                    ranking_data = load_json_file(ranking_file_path)
                    ranked_pokemon_ids, ranked_move_ids = get_pokemon_and_moves_from_data_file(ranking_data)

                    # Species validation
                    unknown_ranked_species = ranked_pokemon_ids - gamemaster_species_ids
                    if unknown_ranked_species:
                        all_valid = False
                        ranking_file_rel_path = os.path.relpath(ranking_file_path, rankings_base_path)
                        print(f"    ❌ ERROR: Unknown species in {ranking_file_rel_path}:")
                        for species_id in sorted(list(unknown_ranked_species)):
                            print(f"       - {species_id}")

                    # Move validation
                    unknown_ranked_moves = ranked_move_ids - gamemaster_all_move_ids
                    if unknown_ranked_moves:
                        all_valid = False
                        print(
                            f"    ❌ ERROR: Unknown moves in {os.path.relpath(ranking_file_path, rankings_base_path)}:"
                        )
                        for move_id in sorted(list(unknown_ranked_moves)):
                            print(f"       - {move_id}")

                    # Forbidden species check
                    forbidden_ranked_species_found = forbidden_species.intersection(ranked_pokemon_ids)
                    if forbidden_ranked_species_found:
                        all_valid = False
                        print(f"    ❌ ERROR: Forbidden species found in {ranking_file_rel_path}:")
                        for species_id in sorted(list(forbidden_ranked_species_found)):
                            print(f"       - {species_id}")

                    # Forbidden move check
                    forbidden_ranked_moves_found = forbidden_moves.intersection(ranked_move_ids)
                    if forbidden_ranked_moves_found:
                        all_valid = False
                        print(f"    ❌ ERROR: Forbidden moves found in {ranking_file_rel_path}:")
                        for move_id in sorted(list(forbidden_ranked_moves_found)):
                            print(f"       - {move_id}")

        print("\n--- Summary ---")
        if all_valid:
            print("✅ Zip archive validation PASSED: All cup data is valid.")
            exit(0)
        else:
            print("❌ Zip archive validation FAILED: Discrepancies found.")
            exit(1)


if __name__ == "__main__":
    main()
