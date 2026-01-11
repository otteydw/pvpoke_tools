#!/usr/bin/env -S uv run --quiet --script
"""A script to generate moveset overrides for PvPoke cups based on gamemaster and ranking data."""
import argparse
import json
import os
import sys
from pathlib import Path


def generate_moveset_overrides(cup, league, predefined_overrides, newly_chosen_overrides):
    """Generates a list of moveset overrides for eligible Pokemon in a given cup and league.

    Args:
        cup (str): The name of the cup (e.g., "all", "fossil").
        league (int): The league CP (e.g., 1500, 2500).
        predefined_overrides (dict): A dictionary of pre-defined move overrides {species_id: move_name}.
        newly_chosen_overrides (dict): A dictionary to store newly made choices.

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
    pokemon_path = base_path / "data" / "gamemaster" / "pokemon.json"
    rankings_path = base_path / "data" / "rankings" / cup / "overall" / f"rankings-{league}.json"

    # Load Game Master and ranking data
    try:
        with open(gamemaster_path, "r") as f:
            gamemaster = json.load(f)
        with open(pokemon_path, "r") as f:
            pokemon_data_list = json.load(f)
        with open(rankings_path, "r") as f:
            rankings = json.load(f)
    except FileNotFoundError:
        print("Error: Required data not found.", file=sys.stderr)
        print(f"  - Gamemaster path: {gamemaster_path}", file=sys.stderr)
        print(f"  - Pokemon path: {pokemon_path}", file=sys.stderr)
        print(f"  - Rankings path: {rankings_path}", file=sys.stderr)
        print("Please ensure PVPOKE_SRC_ROOT is correctly set and the data files exist.", file=sys.stderr)
        sys.exit(1)  # Exit with an error code

    # Create a lookup for pokemon data by speciesId
    pokemon_data = {p["speciesId"]: p for p in pokemon_data_list}

    # Find the cup definition
    cup_definition = next((c for c in gamemaster["cups"] if c["name"] == cup), None)
    if not cup_definition:
        print(f"Error: Cup '{cup}' not found in gamemaster.json.", file=sys.stderr)
        sys.exit(1)  # Exit with an error code

    # Extract banned moves from the cup definition
    banned_moves = set()
    if "exclude" in cup_definition:
        for rule in cup_definition["exclude"]:
            if rule.get("filterType") == "move":
                banned_moves.update([move.upper() for move in rule.get("values", [])])

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
            species_id = rank["speciesId"]
            fast_move = rank["moveset"][0].upper()  # Convert to uppercase

            # --- Fast Move Handling ---
            if fast_move in banned_moves:
                pokemon = pokemon_data.get(species_id)
                if not pokemon:
                    print(
                        f"Warning: {species_id} not found in pokemon.json. Cannot find alternative moves.",
                        file=sys.stderr,
                    )
                    continue

                all_fast_moves = [m.upper() for m in pokemon.get("fastMoves", [])]
                valid_alternatives = [m for m in all_fast_moves if m not in banned_moves]

                if len(valid_alternatives) == 1:
                    new_move = valid_alternatives[0]
                    print(
                        f"Info: Auto-replacing banned move {fast_move} with {new_move} for {species_id}.",
                        file=sys.stderr,
                    )
                    fast_move = new_move
                    if species_id.lower() not in predefined_overrides:
                        if species_id.lower() not in newly_chosen_overrides:
                            newly_chosen_overrides[species_id.lower()] = {"speciesId": species_id}
                        newly_chosen_overrides[species_id.lower()]["fastMove"] = fast_move

                elif len(valid_alternatives) > 1:
                    chosen_move = None
                    override_data = predefined_overrides.get(species_id.lower())
                    if override_data and "fastMove" in override_data:
                        predefined_move = override_data["fastMove"].upper()
                        if predefined_move in valid_alternatives:
                            print(
                                f"Info: Using predefined override for {species_id}: {predefined_move}",
                                file=sys.stderr,
                            )
                            chosen_move = predefined_move
                        else:
                            print(
                                f"Warning: Predefined move {predefined_move} for {species_id} is invalid. "
                                f"Falling back to interactive prompt.",
                                file=sys.stderr,
                            )

                    if not chosen_move:
                        print(
                            f"Info: {species_id} has a banned fast move ({fast_move}). Please choose a replacement:",
                            file=sys.stderr,
                        )
                        for i, move in enumerate(valid_alternatives):
                            print(f"  {i + 1}: {move}", file=sys.stderr)

                        choice = -1
                        while choice < 1 or choice > len(valid_alternatives):
                            try:
                                user_input = input(f"Enter number (1-{len(valid_alternatives)}): ")
                                choice = int(user_input)
                            except (ValueError, EOFError):
                                print("Invalid input. Please enter a number.", file=sys.stderr)
                                continue
                        chosen_move = valid_alternatives[choice - 1]
                    fast_move = chosen_move
                    if species_id.lower() not in predefined_overrides:
                        if species_id.lower() not in newly_chosen_overrides:
                            newly_chosen_overrides[species_id.lower()] = {"speciesId": species_id}
                        newly_chosen_overrides[species_id.lower()]["fastMove"] = fast_move

                else:
                    print(
                        f"Warning: No valid alternative fast moves for {species_id} to replace {fast_move}. Skipping.",
                        file=sys.stderr,
                    )
                    continue

            # --- Charged Move Handling ---
            final_charged_moves = []
            current_charged_moves = [cm.upper() for cm in rank["moveset"][1:]]

            override_data = predefined_overrides.get(species_id.lower())
            # Check for a complete "chargedMoves" override first
            if override_data and "chargedMoves" in override_data:
                predefined_cms = [cm.upper() for cm in override_data["chargedMoves"]]
                # Validate that the predefined moves are not banned
                if all(cm not in banned_moves for cm in predefined_cms):
                    print(f"Info: Using predefined charged moves for {species_id}: {predefined_cms}", file=sys.stderr)
                    final_charged_moves = predefined_cms
                else:
                    print(
                        f"Warning: Predefined charged moves for {species_id} are banned.",
                        "Ignoring override.",
                        file=sys.stderr,
                    )

            # If no valid override was used, proceed with conflict resolution
            if not final_charged_moves:
                for i, charged_move in enumerate(current_charged_moves):
                    if charged_move in banned_moves:
                        pokemon = pokemon_data.get(species_id)
                        if not pokemon:
                            print(f"Warning: {species_id} not found in pokemon.json.", file=sys.stderr)
                            continue

                        all_charged_moves = [m.upper() for m in pokemon.get("chargedMoves", [])]
                        valid_alternatives = [
                            m for m in all_charged_moves if m not in banned_moves and m not in final_charged_moves
                        ]

                        chosen_move = None
                        if len(valid_alternatives) == 1:
                            chosen_move = valid_alternatives[0]
                            print(
                                f"Info: Auto-replacing banned charged move {charged_move}",
                                f"with {chosen_move} for {species_id}.",
                                file=sys.stderr,
                            )
                        elif len(valid_alternatives) > 1:
                            print(
                                f"Info: {species_id} has banned charged move {charged_move}.",
                                "Please choose a replacement:",
                                file=sys.stderr,
                            )
                            for j, move in enumerate(valid_alternatives):
                                print(f"  {j + 1}: {move}", file=sys.stderr)

                            choice = -1
                            while choice < 1 or choice > len(valid_alternatives):
                                try:
                                    user_input = input(f"Enter number (1-{len(valid_alternatives)}): ")
                                    choice = int(user_input)
                                except (ValueError, EOFError):
                                    print("Invalid input. Please enter a number.", file=sys.stderr)
                                    continue
                            chosen_move = valid_alternatives[choice - 1]

                        if chosen_move:
                            final_charged_moves.append(chosen_move)
                        else:
                            print(
                                f"Warning: No valid alternative for banned charged move {charged_move}",
                                f"on {species_id}.",
                                file=sys.stderr,
                            )
                    else:
                        final_charged_moves.append(charged_move)

            # Track newly chosen charged moves
            original_charged_moves = {cm.upper() for cm in rank["moveset"][1:]}
            if set(final_charged_moves) != original_charged_moves:
                # Only track if the final moveset is different and not from a predefined full override
                override_data = predefined_overrides.get(species_id.lower())
                if not (override_data and "chargedMoves" in override_data):
                    if species_id.lower() not in newly_chosen_overrides:
                        newly_chosen_overrides[species_id.lower()] = {"speciesId": species_id}
                    newly_chosen_overrides[species_id.lower()]["chargedMoves"] = final_charged_moves

            weight = 1
            override_data = predefined_overrides.get(species_id.lower())
            if override_data and "weight" in override_data:
                weight = override_data["weight"]

            moveset = {
                "speciesId": species_id,
                "fastMove": fast_move,
                "chargedMoves": final_charged_moves,
                "weight": weight,
            }
            overrides.append(moveset)

    # Sort the overrides by speciesId alphabetically
    overrides.sort(key=lambda x: x["speciesId"])

    print(json.dumps(overrides, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import league movesets for a specific cup and league.")
    parser.add_argument("cup", type=str, help='The name of the cup (e.g., "all", "fossil").')
    parser.add_argument("league", type=int, help="The league CP (e.g., 1500, 2500).")
    parser.add_argument(
        "--override-file",
        type=str,
        help="Optional: Path to a file containing move override decisions (e.g., 'turtonator ember').",
    )
    args = parser.parse_args()

    predefined_overrides = {}
    if args.override_file:
        try:
            with open(args.override_file, "r") as f:
                overrides_list = json.load(f)
                for override in overrides_list:
                    if "speciesId" in override:
                        predefined_overrides[override["speciesId"].lower()] = override
                    else:
                        print(
                            f"Warning: Skipping invalid entry in override file (missing 'speciesId'): {override}",
                            file=sys.stderr,
                        )
        except FileNotFoundError:
            print(f"Error: Override file not found at {args.override_file}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from override file at {args.override_file}", file=sys.stderr)
            sys.exit(1)

    newly_chosen_overrides: dict = {}
    generate_moveset_overrides(args.cup, args.league, predefined_overrides, newly_chosen_overrides)

    if newly_chosen_overrides:
        print("\nNew move selections were made during this session.", file=sys.stderr)
        save_choice = ""
        while save_choice not in ["y", "n"]:
            save_choice = input("Do you want to save these choices to an override file? (y/n): ").lower()

        if save_choice == "y":
            default_filename = args.override_file or "new_overrides.json"
            output_filename_prompt = f"Enter filename to save to [{default_filename}]: "
            output_filename = input(output_filename_prompt).strip()
            if not output_filename:
                output_filename = default_filename

            # Merge old and new overrides, with new ones taking precedence
            final_overrides_dict = predefined_overrides.copy()
            final_overrides_dict.update(newly_chosen_overrides)

            # Convert dictionary values to a list and sort by speciesId
            final_overrides_list = sorted(final_overrides_dict.values(), key=lambda x: x["speciesId"])

            try:
                with open(output_filename, "w") as f:
                    json.dump(final_overrides_list, f, indent=4)
                print(f"Successfully saved overrides to {output_filename}", file=sys.stderr)
            except IOError as e:
                print(f"Error: Could not write to file {output_filename}: {e}", file=sys.stderr)
