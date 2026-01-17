#!/usr/bin/env bash
set -euo pipefail

# Usage function
usage() {
  echo "Usage: $(basename "$0") [-h|--help] [--json <cupname> | --zip <zipfile>]"
  echo ""
  echo "This script generates a JSON configuration for Zygarden-related features"
  echo "based on an existing PvPoke cup's data."
  echo "The output JSON is printed to standard output."
  echo ""
  echo "Arguments:"
  echo "  --json <cupname>   The codename of the PvPoke cup to use (e.g., december2025)."
  echo "  --zip <zipfile>    Path to a zipped cup archive."
  echo ""
  echo "Options:"
  echo "  -h, --help         Display this help message and exit."
  echo ""
  echo "Environment Variables:"
  echo "  PVPOKE_SRC_ROOT (Optional) Override the default root path for PvPoke source files."
  echo "                  Default: /var/www/builder.devon.gg/public_html/pvpoke/src"
}

webrt="${PVPOKE_SRC_ROOT:-/var/www/builder.devon.gg/public_html/pvpoke/src}"
CUP_NAME=""
ZIP_FILE=""

# Ensure jq is installed
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is not installed. Please install jq to run this script." >&2
  exit 1
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
  -h | --help)
    usage
    exit 0
    ;;
  --json)
    CUP_NAME="$2"
    shift 2
    ;;
  --zip)
    ZIP_FILE="$2"
    shift 2
    ;;
  *)
    # All remaining arguments are positional
    echo "Error: Unknown argument '$1'" >&2
    usage >&2
    exit 1
    ;;
  esac
done

# Validate arguments
if [[ -z $CUP_NAME && -z $ZIP_FILE ]]; then
  echo "Error: You must provide either --json <cupname> or --zip <zipfile>." >&2
  usage >&2
  exit 1
fi

if [[ -n $CUP_NAME && -n $ZIP_FILE ]]; then
  echo "Error: You cannot provide both --json and --zip at the same time." >&2
  usage >&2
  exit 1
fi

# --- Path Resolution ---
temp_dir=""
cleanup() {
  if [[ -n $temp_dir && -d $temp_dir ]]; then
    rm -rf "$temp_dir"
  fi
}
trap cleanup EXIT

if [[ -n $ZIP_FILE ]]; then
  # --- ZIP File Logic ---
  if [[ ! -f $ZIP_FILE ]]; then
    echo "Error: Zip file not found at '$ZIP_FILE'" >&2
    exit 1
  fi

  temp_dir=$(mktemp -d)
  echo "INFO: Unzipping '$ZIP_FILE' to temporary directory: $temp_dir" >&2
  unzip -q "$ZIP_FILE" -d "$temp_dir"

  cup_shortname=""
  for item in "$temp_dir"/*; do
    if [[ -d $item ]]; then
      cup_shortname=$(basename "$item")
      break
    fi
  done

  if [[ -z $cup_shortname ]]; then
    echo "Error: Could not determine cup shortname from zip archive structure." >&2
    exit 1
  fi
  echo "INFO: Detected cup shortname: ${cup_shortname}" >&2

  cupfile="${temp_dir}/${cup_shortname}/cupfile/${cup_shortname}.json"
  rankings_base_path="${temp_dir}/${cup_shortname}/rankings/${cup_shortname}"

else
  # --- JSON (cupname) Logic ---
  cupfile="${webrt}/data/gamemaster/cups/${CUP_NAME}.json"
  rankings_base_path="${webrt}/data/rankings/${CUP_NAME}"
fi

# --- Core Logic ---
if [[ ! -f $cupfile ]]; then
  echo "Error: cup file not found: $cupfile" >&2
  exit 1
fi

# Extract league, title, and link from cup file
league=$(jq -r '.league // empty' "$cupfile")
title=$(jq -r '.title // empty' "$cupfile")
rules_uri=$(jq -r '.link // empty' "$cupfile")

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
rankings="${rankings_base_path}/overall/rankings-${league}.json"
if [[ ! -f $rankings ]]; then
  echo "Error: rankings file not found: $rankings" >&2
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
  "rulesUri": "${rules_uri}",
  "uniquenessRule": "DexNumberAndType",
  "slots": 6
}
EOF
