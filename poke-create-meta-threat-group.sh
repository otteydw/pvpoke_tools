#!/usr/bin/env bash
set -euo pipefail

# poke-create-meta-threat-group.sh
#
# Description:
# This script creates a "meta threat group" JSON file. It filters a large JSON
# file of Pokémon data to include only the Pokémon specified in a threat group text file.
# The output is sorted alphabetically by the Pokémon's speciesId.
#
# The resulting JSON is printed to standard output, allowing it to be redirected to a file.
#
# Usage:
#   ./poke-create-meta-threat_group.sh <threat_group_file> <pokemon_json_file>
#
# Arguments:
#   threat_group_file:  A path to a text file containing one Pokémon speciesId per line
#                       that defines the threat group.
#
#   pokemon_json_file:  A path to a JSON file containing an array of Pokémon data,
#                       such as the `pokemon.json` from the pvpoke Game Master file
#                       or a custom overrides file.
#
# Example:
#   ./poke-create-meta-threat-group.sh my_threats.txt master/pokemon.json > threat_group.json
#

# ---------------------------------------------
# Check for required commands
# ---------------------------------------------
command -v jq >/dev/null 2>&1 || {
  echo >&2 "I require jq but it's not installed.  Aborting."
  exit 1
}

# --- Input Validation ---

# Ensure exactly two arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <threat_group_file> <pokemon_json_file>" >&2
  exit 1
fi

THREAT_GROUP_FILE="$1"
POKEMON_JSON_FILE="$2"

# Check if the threat group file exists
if [ ! -f "$THREAT_GROUP_FILE" ]; then
  echo "Error: Threat group file not found at '$THREAT_GROUP_FILE'" >&2
  exit 1
fi

# Check if the JSON file exists
if [ ! -f "$POKEMON_JSON_FILE" ]; then
  echo "Error: Pokémon JSON file not found at '$POKEMON_JSON_FILE'" >&2
  exit 1
fi

# --- Core Logic ---

# Use jq to filter the Pokémon data.
#
# - `--rawfile wanted_list <(sort -u "$THREAT_GROUP_FILE")`: Reads the sorted, unique lines from the
#   threat group file into the $wanted_list variable. Using process substitution ` <(command)` allows
#   us to preprocess the file before jq sees it. `sort -u` sorts the names and removes duplicates.
#
# - `($wanted_list | split("\n") | map(select(. != ""))) as $wanted`: Creates a clean JSON
#   array of Pokémon names to filter by.
#
# - `map(select(.speciesId as $id | $wanted | index($id)))`: Iterates through the input
#   JSON and selects any Pokémon whose `speciesId` is present in the `$wanted` array.
#
# - `sort_by(.speciesId)`: Sorts the resulting array of Pokémon objects alphabetically
#   based on their `speciesId`.
jq --rawfile wanted_list <(sort -u "$THREAT_GROUP_FILE") '($wanted_list | split("\n") | map(select(. != ""))) as $wanted | map(select(.speciesId as $id | $wanted | index($id))) | sort_by(.speciesId)' "$POKEMON_JSON_FILE"
