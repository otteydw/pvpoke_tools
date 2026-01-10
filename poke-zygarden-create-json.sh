#!/usr/bin/env bash
set -euo pipefail

# Usage function
usage() {
  echo "Usage: $(basename "$0") [-h|--help] <cupname>"
  echo ""
  echo "This script generates a JSON configuration for Zygarde-related features"
  echo "based on an existing PvPoke cup's data."
  echo "The output JSON is printed to standard output."
  echo ""
  echo "Arguments:"
  echo "  <cupname>   The codename of the PvPoke cup to use (e.g., december2025)."
  echo ""
  echo "Options:"
  echo "  -h, --help  Display this help message and exit."
  echo ""
  echo "Environment Variables:"
  echo "  PVPOKE_SRC_ROOT (Optional) Override the default root path for PvPoke source files."
  echo "                  Default: /var/www/builder.devon.gg/public_html/pvpoke/src"
}

webrt="${PVPOKE_SRC_ROOT:-/var/www/builder.devon.gg/public_html/pvpoke/src}"

# Ensure jq is installed
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is not installed. Please install jq to run this script."
  exit 1
fi

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

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

cup="$1"
cupfile="${webrt}/data/gamemaster/cups/${cup}.json"

if [[ ! -f $cupfile ]]; then
  echo "Error: cup file not found: $cupfile"
  exit 1
fi

# Extract league and title from cup file
league=$(jq -r '.league // empty' "$cupfile")
title=$(jq -r '.title // empty' "$cupfile")

# Validate required fields
if [ -z "$league" ]; then
  echo "ERROR: Missing or empty 'league' in $cupfile" >&2
  exit 1
fi

if [ -z "$title" ]; then
  echo "ERROR: Missing or empty 'title' in $cupfile" >&2
  exit 1
fi

# Map league numbers to names
case "$league" in
1500) league_name="Great" ;;
2500) league_name="Ultra" ;;
10000) league_name="Master" ;;
*) league_name="Custom(${league})" ;;
esac

# Locate overall rankings file
rankings="${webrt}/data/rankings/${cup}/overall/rankings-${league}.json"
if [[ ! -f $rankings ]]; then
  echo "Error: rankings file not found: $rankings"
  exit 1
fi

# -- Output useful info to stderr
pokemon_count=$(jq 'length' "$rankings")
echo "INFO: Using cup file: ${cupfile}" >&2
echo "INFO: Using rankings file: ${rankings}" >&2
echo "INFO: Found ${pokemon_count} Pokémon in rankings." >&2
# --

# Extract speciesIds and join into comma-separated list
allowedMons=$(jq -r 'map(.speciesId) | sort | join(", ")' "$rankings")

# Build output JSON
cat <<EOF
{
  "allowedMons": "$allowedMons",
  "name": "${title} (Devon)",
  "league": "${league_name}",
  "rulesUri": "",
  "uniquenessRule": "DexNumberAndType",
  "slots": 6
}
EOF
