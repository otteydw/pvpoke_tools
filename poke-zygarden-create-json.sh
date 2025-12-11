#!/bin/bash
set -euo pipefail

webrt="/var/www/builder.devon.gg/public_html/pvpoke/src"

# Ensure jq is installed
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is not installed. Please install jq to run this script."
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <cupname>"
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

# Locate overrides file
overrides="${webrt}/data/overrides/${cup}/${league}.json"
if [[ ! -f $overrides ]]; then
  echo "Error: overrides file not found: $overrides"
  exit 1
fi

# Extract speciesIds and join into comma-separated list
allowedMons=$(jq -r 'map(.speciesId) | join(", ")' "$overrides")

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
