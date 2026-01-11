#!/usr/bin/env -S uv run --quiet --script
"""A script to generate moveset overrides for PvPoke cups based on gamemaster and ranking data."""
import argparse
import json
import os
import sys
from pathlib import Path


def generate_moveset_overrides(cup, league):
    """Generates a list of moveset overrides for eligible Pokemon in a given cup and league.

    Args:
        cup (str): The name of the cup (e.g., "all", "fossil").
        league (int): The league CP (e.g., 1500, 2500).

    This function reads the gamemaster and ranking data, filters eligible Pokemon
    based on the cup's include/exclude rules, and then generates moveset overrides
    in the required format. The result is printed to standard output as a JSON array.
    """
    # Determine the base path for pvpoke's src directory
    pvpoke_src_root = os.environ.get("PVPOKE_SRC_ROOT")

    if not pvpoke_src_root:
        print("Error: PVPOKE_SRC_ROOT environment variable is not set.", file=sys.stderr)
        print("Please set it to the absolute path of your pvpoke/src directory, e.g.:", file=sys.stderr)
        print("  export PVPOKE_SRC_ROOT=/Users/dottey/git/personal/pvpoke/src", file=sys.stderr)
        sys.exit(1)  # Exit with an error code

    base_path = Path(pvpoke_src_root)

    gamemaster_path = base_path / "data" / "gamemaster.json"
    rankings_path = base_path / "data" / "rankings" / cup / "overall" / f"rankings-{league}.json"

    # Load Game Master and ranking data
    try:
        with open(gamemaster_path, "r") as f:
            gamemaster = json.load(f)
        with open(rankings_path, "r") as f:
            rankings = json.load(f)
    except FileNotFoundError:
        print("Error: Required data not found.", file=sys.stderr)
        print(f"  - Gamemaster path: {gamemaster_path}", file=sys.stderr)
        print(f"  - Rankings path: {rankings_path}", file=sys.stderr)
        print("Please ensure PVPOKE_SRC_ROOT is correctly set and the data files exist.", file=sys.stderr)
        sys.exit(1)  # Exit with an error code

    # Find the cup definition
    cup_definition = next((c for c in gamemaster["cups"] if c["name"] == cup), None)
    if not cup_definition:
        print(f"Error: Cup '{cup}' not found in gamemaster.json.", file=sys.stderr)
        sys.exit(1)  # Exit with an error code

    # Generate the filtered list of eligible Pokemon for the cup
    eligible_pokemon_ids = set()

    # Process include rules
    if "include" in cup_definition:
        for rule in cup_definition["include"]:
            if rule.get("filterType") == "id":
                for speciesId in rule["values"]:
                    eligible_pokemon_ids.add(speciesId)

    # Process exclude rules
    if "exclude" in cup_definition:
        for p in cup_definition["exclude"]:
            if isinstance(p, str):
                if p in eligible_pokemon_ids:
                    eligible_pokemon_ids.remove(p)
            elif isinstance(p, dict) and "speciesId" in p:
                if p["speciesId"] in eligible_pokemon_ids:
                    eligible_pokemon_ids.remove(p["speciesId"])

    # Generate moveset overrides from rankings
    overrides = []
    for rank in rankings:
        if rank["speciesId"] in eligible_pokemon_ids:
            moveset = {
                "speciesId": rank["speciesId"],
                "fastMove": rank["moveset"][0],
                "chargedMoves": rank["moveset"][1:],
            }
            overrides.append(moveset)

    # Sort the overrides by speciesId alphabetically
    overrides.sort(key=lambda x: x["speciesId"])

    print(json.dumps(overrides, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import league movesets for a specific cup and league.")
    parser.add_argument("cup", type=str, help='The name of the cup (e.g., "all", "fossil").')
    parser.add_argument("league", type=int, help="The league CP (e.g., 1500, 2500).")
    args = parser.parse_args()

    generate_moveset_overrides(args.cup, args.league)
