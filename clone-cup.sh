#!/usr/bin/env bash
set -euo pipefail

# Use environment variable PVPOKE_SRC_ROOT if set, otherwise default
root="${PVPOKE_SRC_ROOT:-/var/www/builder.devon.gg/public_html/pvpoke/src}"

# Confirm the root directory exists
if [[ ! -d "$root" ]]; then
    echo "Error: root directory '$root' does not exist."
    exit 1
fi

echo "Using root directory: $root"

# Usage: ./clone-cup.sh oldname newname
# Example: ./clone-cup.sh december2025 january2026

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 oldname newname"
  exit 1
fi

# Ensure jq is installed
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is not installed. Please install jq to run this script."
  exit 1
fi

old="$1"
new="$2"

# Default pretty names: capitalize first letter
oldpretty_default="$(tr '[:lower:]' '[:upper:]' <<< ${old:0:1})${old:1}"
newpretty_default="$(tr '[:lower:]' '[:upper:]' <<< ${new:0:1})${new:1}"

read -e -i "$oldpretty_default" -p "OLD pretty name (just for confirmation): " oldpretty
read -e -i "$newpretty_default" -p "NEW pretty name (shown in UI): " newpretty

echo ""
echo "Cloning cup:"
echo "  codename    : $old --> $new"
echo "  display name: $oldpretty --> $newpretty"
echo ""

# --- 1. Copy directories (overrides & rankings) ---
for dir in "overrides/$old" "rankings/$old"; do
    if [[ -d "${root}/data/$dir" ]]; then
        cp -r "${root}/data/$dir" "${root}/data/${dir/$old/$new}"
    fi
done

# --- 2. Copy cup JSON and update only .name and .title ---
src_cup_json="${root}/data/gamemaster/cups/${old}.json"
dest_cup_json="${root}/data/gamemaster/cups/${new}.json"
cp "$src_cup_json" "$dest_cup_json"

jq --arg cup "$new" --arg title "$newpretty" \
   '.name = $cup | .title = $title' \
   "$dest_cup_json" > "${dest_cup_json}.tmp" && mv "${dest_cup_json}.tmp" "$dest_cup_json"

# --- 3. Copy group JSON if it exists ---
src_group_json="${root}/data/groups/${old}.json"
dest_group_json="${root}/data/groups/${new}.json"
if [[ -f "$src_group_json" ]]; then
    cp "$src_group_json" "$dest_group_json"
fi

# --- 4. Append a new entry to formats.json ---
formats_json="${root}/data/gamemaster/formats.json"
old_entry=$(jq --arg cup "$old" 'map(select(.cup == $cup)) | .[0]' "$formats_json")

if [[ "$old_entry" == "null" ]]; then
    echo "Error: could not find format entry for cup '$old' in formats.json"
    exit 1
fi

# Update only .cup and .title (and preserve all other fields)
new_entry=$(jq --arg cup "$new" --arg title "$newpretty" \
    '.cup = $cup | .title = $title' <<< "$old_entry")

jq --tab --argjson newentry "$new_entry" '. + [$newentry]' "$formats_json" > "${formats_json}.tmp" && mv "${formats_json}.tmp" "$formats_json"

echo ""
echo "✅ Cup cloned successfully."
echo "👉 New directories:"
echo "    overrides/${new}"
echo "    rankings/${new}"
echo "👉 New cup JSON: gamemaster/cups/${new}.json"
echo "👉 New group JSON: groups/${new}.json (if it existed)"
echo "👉 Entry added to formats.json"
echo ""
echo "Don't forget to compile gamemaster!"