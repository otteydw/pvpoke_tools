#!/usr/bin/env bash
set -euo pipefail

# Usage function
usage() {
  echo "Usage: $(basename "$0") [-h|--help] oldname newname"
  echo ""
  echo "This script renames an existing PvPoke cup."
  echo "It renames associated directories and files, and updates relevant entries in formats.json."
  echo ""
  echo "Arguments:"
  echo "  oldname     The current codename of the cup (e.g., october25)."
  echo "  newname     The new codename for the cup (e.g., december25)."
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

# Usage: rename-cup.sh oldname newname
# Example: ./rename-cup.sh october25 december25

if [[ $# -ne 2 ]]; then
  usage
  exit 1
fi

oldname="$1"
newname="$2"

# Default pretty names: capitalize first letter
# shellcheck disable=SC2086
oldpretty_default="$(tr '[:lower:]' '[:upper:]' <<<${oldname:0:1})${oldname:1}"
# shellcheck disable=SC2086
newpretty_default="$(tr '[:lower:]' '[:upper:]' <<<${newname:0:1})${newname:1}"

# Prompt user for pretty names with defaults
read -r -e -i "$oldpretty_default" -p "Enter the OLD pretty name: " oldpretty
read -r -e -i "$newpretty_default" -p "Enter the NEW pretty name: " newpretty

echo "Renaming cup:"
echo "  codename: $oldname -> $newname"
echo "  pretty:   $oldpretty -> $newpretty"

# 1. Rename directories and files
mv "${root}/data/overrides/${oldname}" "${root}/data/overrides/${newname}"
mv "${root}/data/groups/${oldname}.json" "${root}/data/groups/${newname}.json"
mv "${root}/data/rankings/${oldname}" "${root}/data/rankings/${newname}"
mv "${root}/data/gamemaster/cups/${oldname}.json" "${root}/data/gamemaster/cups/${newname}.json"

# --- 2. Update formats.json ---
formats_json="${root}/data/gamemaster/formats.json"

jq --tab \
  --arg oldcup "$oldname" --arg newcup "$newname" \
  --arg oldtitle "$oldpretty" --arg newtitle "$newpretty" \
  'map(
        if .cup == $oldcup then
            .cup = $newcup
            | .title = $newtitle
        else
            .
        end
    )' "$formats_json" >"${formats_json}.tmp" && mv "${formats_json}.tmp" "$formats_json"

# --- 3. Update cup JSON ---
cup_json="${root}/data/gamemaster/cups/${newname}.json"
jq --arg cup "$newname" --arg title "$newpretty" \
  '.cup = $cup | .title = $title' \
  "$cup_json" >"${cup_json}.tmp" && mv "${cup_json}.tmp" "$cup_json"

echo "✅ Cup renamed successfully."
echo "Don't forget to compile gamemaster!"
