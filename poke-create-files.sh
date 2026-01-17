#!/usr/bin/env bash
set -euo pipefail
# This script generates the files required to build a custom PvPoke meta
# Reference: https://github.com/pvpoke/pvpoke/wiki/Creating-New-Cups-&-Rankings
# ---------------------------------------------------------------
# WARNING: This script will overwrite certain files, so backups are important
# ---------------------------------------------------------------

# Usage function
usage() {
  echo "Usage: $(basename "$0") [--json-file <filename>]"
  echo "       $(basename "$0") [-h|--help]"
  echo ""
  echo "This script generates the files required to build a custom PvPoke meta."
  echo "Options:"
  echo "  --json-file <filename>  Provide a JSON file containing the meta structure."
  echo "                          If not provided, you will be prompted for direct input."
  echo "  -h, --help              Display this help message and exit."
  echo ""
  echo "Environment Variables:"
  echo "  PVPOKE_SRC_ROOT         (Optional) Override the default root path for PvPoke source files."
  echo "                          Default: /var/www/builder.devon.gg/public_html/pvpoke/src"
  echo ""
  echo "Reference: https://github.com/pvpoke/pvpoke/wiki/Creating-New-Cups-&-Rankings"
}

# ---------------------------------------------
# Check for required commands
# ---------------------------------------------
command -v rpl >/dev/null 2>&1 || {
  echo >&2 "I require rpl but it's not installed.  Aborting."
  exit 1
}
command -v jq >/dev/null 2>&1 || {
  echo >&2 "I require jq but it's not installed.  Aborting."
  exit 1
}

JSON_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
  --json-file)
    if [[ -n $2 && ! $2 =~ ^- ]]; then
      JSON_FILE="$2"
      shift 2
    else
      echo "Error: --json-file requires a filename argument." >&2
      usage
      exit 1
    fi
    ;;
  -h | --help)
    usage
    exit 0
    ;;
  *)
    echo "Error: Unknown argument '$1'" >&2
    usage
    exit 1
    ;;
  esac
done

# Set the root path for the PvPoke source files
webrt="${PVPOKE_SRC_ROOT:-/var/www/builder.devon.gg/public_html/pvpoke/src}"

# Get current timestamp for backups and logging
date=$(date +"%Y%m%d-%H:%M:%S")

# ---------------------------------------------
# Step 1: Gather meta name and title from the user
# ---------------------------------------------
echo -n "Enter the name of the meta: "
read -r name # internal codename (usually lowercase)
sleep 1s
echo -n "Enter the title of the meta: "
read -r title # "pretty" name, typically capitalized
sleep 1s
echo "I am now creating the Gamemaster Cup File $name.json for you ..."
sleep 2s

# ---------------------------------------------
# Step 2: Create the Gamemaster Cup JSON file
# ---------------------------------------------
touch "${webrt}"/data/gamemaster/cups/"${name}".json

_cup_content="" # Use a local variable to hold content

if [[ -n $JSON_FILE ]]; then
  if [[ -f $JSON_FILE ]]; then
    _cup_content=$(cat "$JSON_FILE")
    if [[ -z $_cup_content ]]; then
      echo "Error: JSON file '$JSON_FILE' is empty. Aborting." >&2
      exit 1
    fi
  else
    echo "Error: JSON file not found at '$JSON_FILE'. Aborting." >&2
    exit 1
  fi
else
  echo -n "Enter the json structure for the meta (must be a single line): "
  read -r _cup_content
  if [[ -z $_cup_content ]]; then
    echo "Error: JSON input cannot be empty. Aborting." >&2
    exit 1
  fi
fi

# Append user-provided JSON structure to the file
cat <<<"$_cup_content" >>"${webrt}"/data/gamemaster/cups/"${name}".json

# Replace placeholders in JSON with actual codename and title
rpl -w "custom" "$name" "${webrt}"/data/gamemaster/cups/"${name}".json
rpl -w "Custom" "$title" "${webrt}"/data/gamemaster/cups/"${name}".json

# ---------------------------------------------
# Step 3: Backup existing formats files
# ---------------------------------------------
echo "I am now backing up all format files before proceeding ..."
mkdir -p "${webrt}"/data/gamemaster/formats-bu
cp "${webrt}"/data/gamemaster/formats.json "${webrt}"/data/gamemaster/formats-bu/formats-"${date}".json
sleep 2s

# ---------------------------------------------
# Step 5: Merge new meta into formats.json
# ---------------------------------------------
echo "Adding the new meta to formats.json in gamemaster ..."
sleep 2s

FORMATS_FILE="${webrt}/data/gamemaster/formats.json"

# Check if formats.json exists and is a valid JSON array
if [[ ! -f $FORMATS_FILE ]]; then
  echo "Error: formats.json not found at '$FORMATS_FILE'. Aborting." >&2
  exit 1
fi
if ! jq -e . <"$FORMATS_FILE" >/dev/null; then
  echo "Error: formats.json at '$FORMATS_FILE' is not valid JSON. Aborting." >&2
  exit 1
fi
if ! jq -e '.[0]' <"$FORMATS_FILE" >/dev/null; then
  echo "Error: formats.json at '$FORMATS_FILE' is not a JSON array. Aborting." >&2
  exit 1
fi

# Extract the "Custom" template from formats.json
CUSTOM_TEMPLATE=$(jq -c '.[] | select(.cup == "custom" or .title == "Custom")' "$FORMATS_FILE")

if [[ -z $CUSTOM_TEMPLATE ]]; then
  echo "Error: 'Custom' template (cup: \"custom\" or title: \"Custom\") not found in formats.json. Aborting." >&2
  exit 1
fi

# Read existing formats, append new template, update placeholders, and write back
if ! jq --arg name "$name" --arg title "$title" \
  --argjson custom_template "$CUSTOM_TEMPLATE" \
  '[ .[] | select(.cup != $name) ] +
     [ $custom_template | .cup = $name | .title = $title | .meta = $name ]' \
  "$FORMATS_FILE" >"${FORMATS_FILE}.tmp"; then
  echo "Error: Failed to update formats.json with jq. Aborting." >&2
  rm -f "${FORMATS_FILE}.tmp" # Clean up temp file
  exit 1
fi
mv "${FORMATS_FILE}.tmp" "$FORMATS_FILE"

echo "formats.json is now complete. Compile and run the ranker/sandbox next."
sleep 2s

# ---------------------------------------------
# Step 7: Create empty Meta Group JSON
# ---------------------------------------------
echo "Creating empty group file for Multi Battle/Matrix battle ..."
sleep 2s
touch "${webrt}"/data/groups/"${name}".json
echo "[]" >>"${webrt}"/data/groups/"${name}".json

echo "Remember to edit the group JSON later via Custom Rankings > Export > JSON ..."
sleep 2s

# ---------------------------------------------
# Step 8: Create empty Moveset Override JSON
# ---------------------------------------------
echo -n "Enter the CP (500, 1500, 2500, 10000) for this cup: "
read -r cp
mkdir -p "${webrt}"/data/overrides/"${name}"
touch "${webrt}"/data/overrides/"${name}"/"${cp}".json
echo "[]" >>"${webrt}"/data/overrides/"${name}"/"${cp}".json
echo "Edit the $cp.json file with overrides as needed and run the ranker after changes."

# ---------------------------------------------
# Step 9: Create empty Ranking directories and files
# ---------------------------------------------
echo "Creating ranking directories and files ..."
sleep 2s
mkdir -p "${webrt}"/data/rankings/"${name}"/{attackers,chargers,closers,consistency,leads,overall,switches}

# Initialize ranking files with empty JSON arrays
for folder in attackers chargers closers consistency leads overall switches; do
  echo "[]" >>"${webrt}"/data/rankings/"${name}"/${folder}/rankings-"${cp}".json
done

echo "All necessary files are now created. Compile, create groups, import movesets, and run ranker/sandbox."

# ---------------------------------------------
# Step 10: Set permissions
# ---------------------------------------------
echo "Setting permissions ..."
# This chmod command applies permissions to the main project directory,
# specifically for the devon.gg build server where specific permissions are required.
# It only runs if 'webrt' is using its default value, indicating it's on the build server.
if [[ $webrt == "/var/www/builder.devon.gg/public_html/pvpoke/src" ]]; then
  chmod 777 -R "$(dirname "$webrt")/"
fi
sleep 2s
