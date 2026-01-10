#!/usr/bin/env bash
set -euo pipefail

# Usage function
usage() {
  echo "Usage: $(basename "$0") [-h|--help] cupname"
  echo ""
  echo "This script deletes an existing PvPoke cup."
  echo "It removes associated data (overrides, rankings, JSON files)"
  echo "and updates relevant entries in formats.json."
  echo ""
  echo "Arguments:"
  echo "  cupname     The codename of the cup to delete (e.g., december2025)."
  echo ""
  echo "Options:"
  echo "  -h, --help  Display this help message and exit."
  echo ""
  echo "Environment Variables:"
  echo "  PVPOKE_SRC_ROOT (Optional) Override the default root path for PvPoke source files."
  echo "                  Default: /var/www/builder.devon.gg/public_html/pvpoke/src"
}

# Use environment variable PVPOKE_SRC_ROOT if set, otherwise default
root="${PVPOKE_SRC_ROOT:-/var/www/builder.devon.gg/public_html/pvpoke/src}"

# Confirm the root directory exists
if [[ ! -d $root ]]; then
  echo "Error: root directory '$root' does not exist."
  exit 1
fi

echo "Using root directory: $root"

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

# Usage: ./delete-cup.sh cupname
# Example: ./delete-cup.sh december2025

if [[ $# -ne 1 ]]; then
  usage
  exit 1
fi

cup="$1"

echo "Deleting cup: $cup"
echo ""

# --- 1. Remove directories if they exist ---
for dir in "overrides/$cup" "rankings/$cup"; do
  if [[ -d "${root}/data/$dir" ]]; then
    echo "Removing directory: $dir"
    rm -rf "${root}/data/$dir"
  else
    echo "Directory not found, skipping: $dir"
  fi
done

# --- 2. Remove cup JSON ---
cup_json="${root}/data/gamemaster/cups/${cup}.json"
if [[ -f $cup_json ]]; then
  echo "Removing file: gamemaster/cups/${cup}.json"
  rm "$cup_json"
else
  echo "Cup JSON not found, skipping: ${cup}.json"
fi

# --- 3. Remove group JSON if exists ---
group_json="${root}/data/groups/${cup}.json"
if [[ -f $group_json ]]; then
  echo "Removing file: groups/${cup}.json"
  rm "$group_json"
fi

# --- 4. Remove entry from formats.json ---
formats_json="${root}/data/gamemaster/formats.json"
if [[ -f $formats_json ]]; then
  echo "Removing entry from formats.json"
  jq --tab --arg cup "$cup" 'map(select(.cup != $cup))' "$formats_json" \
    >"${formats_json}.tmp" && mv "${formats_json}.tmp" "$formats_json"
else
  echo "formats.json not found, skipping removal from formats.json"
fi

echo ""
echo "✅ Cup '$cup' deleted successfully."
echo "Don't forget to compile gamemaster!"
