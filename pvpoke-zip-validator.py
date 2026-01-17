#!/usr/bin/env -S uv run --quiet --script
# /// script
# ///
"""A tool to validate PvPoke cup data within a zip archive against cup rules."""

import argparse
import json
import os
import tempfile
import zipfile
from functools import partial
from typing import Any, Dict, Set


def load_json_file(filepath: str) -> Any:
    """Loads a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_cup_data_from_json(cup_data: Dict[str, Any]) -> tuple[Set[str], Set[str], Set[str]]:
    """Extracts required/forbidden species and moves from cup JSON data.

    Returns (required_species, forbidden_species, forbidden_moves).
    """
    required_species_ids: Set[str] = set()
    forbidden_species_ids: Set[str] = set()
    forbidden_move_ids: Set[str] = set()

    for rule in cup_data.get("include", []):
        if rule.get("filterType") == "id" and "values" in rule:
            required_species_ids.update(rule["values"])

    for rule in cup_data.get("exclude", []):
        if isinstance(rule, str):  # Direct string exclusion for species
            forbidden_species_ids.add(rule)
        elif isinstance(rule, dict):
            if rule.get("filterType") == "id" and "values" in rule:
                forbidden_species_ids.update(rule["values"])
            if rule.get("filterType") == "move" and "values" in rule:
                forbidden_move_ids.update(move_id.upper() for move_id in rule["values"])

    return required_species_ids, forbidden_species_ids, forbidden_move_ids


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


def _validate_data_file(
    file_path: str,
    base_path: str,
    gamemaster_species_ids: Set[str],
    gamemaster_all_move_ids: Set[str],
    required_species: Set[str],
    forbidden_species: Set[str],
    forbidden_moves: Set[str],
) -> bool:
    """Validates a single data file (override or ranking) against all rules.

    Returns True if the file is valid, False otherwise.
    """
    display_path = os.path.relpath(file_path, base_path)
    print(f"  Processing {display_path}")

    data = load_json_file(file_path)
    pokemon_ids, move_ids = get_pokemon_and_moves_from_data_file(data)

    # Required species check
    if required_species:
        missing_species = required_species - pokemon_ids
        if missing_species:
            print(f"    ❌ ERROR: Missing required species in {display_path}:")
            for species_id in sorted(list(missing_species)):
                print(f"       - {species_id}")
            return False

    # Species validation
    unknown_species = pokemon_ids - gamemaster_species_ids
    if unknown_species:
        print(f"    ❌ ERROR: Unknown species in {display_path}:")
        for species_id in sorted(list(unknown_species)):
            print(f"       - {species_id}")
        return False

    # Move validation
    unknown_moves = move_ids - gamemaster_all_move_ids
    if unknown_moves:
        print(f"    ❌ ERROR: Unknown moves in {display_path}:")
        for move_id in sorted(list(unknown_moves)):
            print(f"       - {move_id}")
        return False

    # Forbidden species check
    forbidden_species_found = forbidden_species.intersection(pokemon_ids)
    if forbidden_species_found:
        print(f"    ❌ ERROR: Forbidden species found in {display_path}:")
        for species_id in sorted(list(forbidden_species_found)):
            print(f"       - {species_id}")
        return False

    # Forbidden move check
    forbidden_moves_found = forbidden_moves.intersection(move_ids)
    if forbidden_moves_found:
        print(f"    ❌ ERROR: Forbidden moves found in {display_path}:")
        for move_id in sorted(list(forbidden_moves_found)):
            print(f"       - {move_id}")
        return False

    return True


def _validate_overrides(
    cup_shortname: str,
    overrides_base_path: str,
    gamemaster_species_ids: Set[str],
    gamemaster_all_move_ids: Set[str],
    required_species: Set[str],
    forbidden_species: Set[str],
    forbidden_moves: Set[str],
) -> bool:
    """Validates all override files for a given cup.

    Returns True if all overrides are valid, False otherwise.
    """
    all_valid = True
    print(f"\n--- Validating Overrides for {cup_shortname} ---")
    if not os.path.exists(overrides_base_path):
        return True  # No overrides to validate

    overrides_files = [
        os.path.join(overrides_base_path, f) for f in os.listdir(overrides_base_path) if f.endswith(".json")
    ]

    validator = partial(
        _validate_data_file,
        base_path=overrides_base_path,
        gamemaster_species_ids=gamemaster_species_ids,
        gamemaster_all_move_ids=gamemaster_all_move_ids,
        required_species=required_species,
        forbidden_species=forbidden_species,
        forbidden_moves=forbidden_moves,
    )

    for ov_file in overrides_files:
        if not validator(file_path=ov_file):
            all_valid = False

    return all_valid


def _validate_rankings(
    cup_shortname: str,
    rankings_base_path: str,
    gamemaster_species_ids: Set[str],
    gamemaster_all_move_ids: Set[str],
    required_species: Set[str],
    forbidden_species: Set[str],
    forbidden_moves: Set[str],
) -> bool:
    """Validates all ranking files for a given cup.

    Returns True if all rankings are valid, False otherwise.
    """
    all_valid = True
    print(f"\n--- Validating Rankings for {cup_shortname} ---")

    validator = partial(
        _validate_data_file,
        base_path=rankings_base_path,
        gamemaster_species_ids=gamemaster_species_ids,
        gamemaster_all_move_ids=gamemaster_all_move_ids,
        required_species=required_species,
        forbidden_species=forbidden_species,
        forbidden_moves=forbidden_moves,
    )

    for root, _, files in os.walk(rankings_base_path):
        for file in files:
            if file.endswith(".json"):
                ranking_file_path = os.path.join(root, file)
                if not validator(file_path=ranking_file_path):
                    all_valid = False
    return all_valid


def _validate_file_structure(
    cup_file_path: str,
    overrides_base_path: str,
    rankings_base_path: str,
) -> bool:
    """Validates the file structure of the cup.

    Returns True if the file structure is valid, False otherwise.
    """
    all_valid = True
    print("\n--- Validating File Structure ---")

    cup_definition = load_json_file(cup_file_path)
    league = cup_definition.get("league")
    if not league:
        print("    ❌ ERROR: `league` not found in cup definition file.")
        return False

    # Validate override file
    expected_override_file = os.path.join(overrides_base_path, f"{league}.json")
    if not os.path.exists(expected_override_file):
        print(f"    ❌ ERROR: Expected override file not found at {expected_override_file}")
        all_valid = False

    # Validate ranking files
    expected_ranking_categories = {
        "attackers",
        "chargers",
        "closers",
        "consistency",
        "leads",
        "overall",
        "switches",
    }
    found_ranking_categories = set(os.listdir(rankings_base_path))

    missing_categories = expected_ranking_categories - found_ranking_categories
    if missing_categories:
        for category in sorted(list(missing_categories)):
            print(f"    ❌ ERROR: Missing ranking category: {category}")
        all_valid = False

    extra_categories = found_ranking_categories - expected_ranking_categories
    if extra_categories:
        for category in sorted(list(extra_categories)):
            print(f"    ⚠️ WARNING: Extra ranking category found: {category}")

    for category in found_ranking_categories.intersection(expected_ranking_categories):
        expected_ranking_file = os.path.join(rankings_base_path, category, f"rankings-{league}.json")
        if not os.path.exists(expected_ranking_file):
            print(f"    ❌ ERROR: Expected ranking file not found at {expected_ranking_file}")
            all_valid = False

    return all_valid


def _run_validation_process(args: argparse.Namespace, pvpoke_src_root: str) -> bool:
    """Runs the entire validation process for a given zip file.

    Returns True if the validation passes, False otherwise.
    """
    gamemaster_pokemon_path = os.path.join(pvpoke_src_root, "data", "gamemaster", "pokemon.json")
    gamemaster_moves_path = os.path.join(pvpoke_src_root, "data", "gamemaster", "moves.json")

    # Validate that gamemaster files exist
    if not os.path.exists(gamemaster_pokemon_path):
        print(
            f"Error: Gamemaster pokemon.json not found at '{gamemaster_pokemon_path}'. "
            "Please ensure PVPOKE_SRC_ROOT is correctly set and the file exists."
        )
        return False
    if not os.path.exists(gamemaster_moves_path):
        print(
            f"Error: Gamemaster moves.json not found at '{gamemaster_moves_path}'. "
            "Please ensure PVPOKE_SRC_ROOT is correctly set and the file exists."
        )
        return False

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Unzipping {args.zip_file} to temporary directory: {temp_dir}")

        with zipfile.ZipFile(args.zip_file, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        cup_shortname = ""
        for item in os.listdir(temp_dir):
            if os.path.isdir(os.path.join(temp_dir, item)):
                cup_shortname = item
                break

        if not cup_shortname:
            print("Error: Could not determine cup shortname from zip archive structure.")
            return False

        print(f"Detected cup shortname: {cup_shortname}")

        cup_file_path = os.path.join(temp_dir, cup_shortname, "cupfile", f"{cup_shortname}.json")
        overrides_base_path = os.path.join(temp_dir, cup_shortname, "overrides", cup_shortname)
        rankings_base_path = os.path.join(temp_dir, cup_shortname, "rankings", cup_shortname)

        if not os.path.exists(cup_file_path):
            print(f"Error: Cup definition file not found at {cup_file_path}")
            return False

        structure_valid = _validate_file_structure(
            cup_file_path,
            overrides_base_path,
            rankings_base_path,
        )

        gamemaster_pokemon_data = load_json_file(gamemaster_pokemon_path)
        gamemaster_moves_data = load_json_file(gamemaster_moves_path)

        gamemaster_species_ids: Set[str] = {
            entry["speciesId"] for entry in gamemaster_pokemon_data if "speciesId" in entry
        }
        gamemaster_all_move_ids: Set[str] = {
            entry["moveId"].upper() for entry in gamemaster_moves_data if "moveId" in entry
        }

        cup_definition = load_json_file(cup_file_path)
        required_species, forbidden_species, forbidden_moves = extract_cup_data_from_json(cup_definition)

        overrides_valid = _validate_overrides(
            cup_shortname,
            overrides_base_path,
            gamemaster_species_ids,
            gamemaster_all_move_ids,
            required_species,
            forbidden_species,
            forbidden_moves,
        )

        rankings_valid = _validate_rankings(
            cup_shortname,
            rankings_base_path,
            gamemaster_species_ids,
            gamemaster_all_move_ids,
            required_species,
            forbidden_species,
            forbidden_moves,
        )

        return structure_valid and overrides_valid and rankings_valid


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

    all_valid = _run_validation_process(args, pvpoke_src_root)

    print("\n--- Summary ---")
    if all_valid:
        print("✅ Zip archive validation PASSED: All cup data is valid.")
        exit(0)
    else:
        print("❌ Zip archive validation FAILED: Discrepancies found.")
        exit(1)


if __name__ == "__main__":
    main()
