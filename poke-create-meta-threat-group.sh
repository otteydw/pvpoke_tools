#!/usr/bin/env bash
set -euo pipefail

# Usage function
usage() {
  echo "Usage: $(basename "$0") [-h|--help] <threat_group_file> <cup_overrides_json_file>"
  echo ""
  echo "This script creates a 'meta threat group' JSON file by filtering Pokémon data."
  echo "It extracts Pokémon specified in a threat group text file from a larger JSON file."
  echo "The output is sorted alphabetically by speciesId and printed to standard output."
  echo ""
  echo "Arguments:"
  echo "  <threat_group_file>       A path to a text file with one Pokémon speciesId per line."
  echo "  <cup_overrides_json_file> A path to a JSON file containing an array of Pokémon data with optimal moves"
  echo "                            (e.g., 'src/data/overrides/<cup_name>/<cp>.json')."
  echo ""
  echo "Options:"
  echo "  -h, --help                Display this help message and exit."
  echo ""
  echo "Example:"
  echo "  ./poke-create-meta-threat-group.sh my_threats.txt src/data/overrides/modifiedlove/1500.json > threat_group.json"
}

# ---------------------------------------------
# Check for required commands
# ---------------------------------------------
command -v jq >/dev/null 2>&1 || {
  echo >&2 "I require jq but it's not installed.  Aborting."
  exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
  -h | --help)
    usage
    exit 0
    ;;
  *)
    # All remaining arguments are positional
    break
    ;;
  esac
done

# --- Input Validation ---

# Ensure exactly two arguments are provided
if [ "$#" -ne 2 ]; then
  usage >&2
  exit 1
fi

THREAT_GROUP_FILE="$1"
CUP_OVERRIDES_JSON_FILE="$2"

# Check if the threat group file exists
if [ ! -f "$THREAT_GROUP_FILE" ]; then
  echo "Error: Threat group file not found at '$THREAT_GROUP_FILE'" >&2
  exit 1
fi

# Check if the JSON file exists
if [ ! -f "$CUP_OVERRIDES_JSON_FILE" ]; then
  echo "Error: Cup overrides JSON file not found at '$CUP_OVERRIDES_JSON_FILE'" >&2
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
jq --rawfile wanted_list <(sort -u "$THREAT_GROUP_FILE") '($wanted_list | split("\n") | map(select(. != ""))) as $wanted | map(select(.speciesId as $id | $wanted | index($id))) | sort_by(.speciesId)' "$CUP_OVERRIDES_JSON_FILE"
