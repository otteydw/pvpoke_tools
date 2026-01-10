#!/usr/bin/env bash
set -euo pipefail

# Usage function
usage() {
  echo "Usage: $(basename "$0") [-h|--help] [meta_name]"
  echo ""
  echo "This script zips the files for a specified PvPoke meta, making them available for download."
  echo "It copies rankings, cup, overrides, and group JSON files into a ZIP archive."
  echo ""
  echo "Arguments:"
  echo "  meta_name   (Optional) The codename of the meta to zip (e.g., modifiedlove)."
  echo "              If not provided, you will be prompted to enter it."
  echo ""
  echo "Options:"
  echo "  -h, --help  Display this help message and exit."
  echo ""
  echo "Environment Variables:"
  echo "  PVPOKE_SRC_ROOT     (Optional) Override the default root path for PvPoke source files."
  echo "                      Default: /var/www/builder.devon.gg/public_html/pvpoke/src"
  echo "  FILEDROP            (Optional) Override the default filedrop directory path."
  echo "                      Default: <PVPOKE_SRC_ROOT parent>/filedrop"
  echo "  PVPOKE_FILEDROP_URI (Optional) Override the default URI root for the filedrop."
  echo "                      Default: https://builder.devon.gg/pvpoke/filedrop"
}

# ---------------------------------------------
# Check for required commands
# ---------------------------------------------
command -v zip >/dev/null 2>&1 || {
  echo >&2 "I require zip but it's not installed.  Aborting."
  exit 1
}

webrt="${PVPOKE_SRC_ROOT:-/var/www/builder.devon.gg/public_html/pvpoke/src}"
filedrop="${FILEDROP:-$(dirname "$webrt")/filedrop}"
uri_root="${PVPOKE_FILEDROP_URI:-https://builder.devon.gg/pvpoke/filedrop}"

# Variable to hold optional meta_name from CLI
CLI_META_NAME=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
  -h | --help)
    usage
    exit 0
    ;;
  *)
    # If it's not a recognized option, treat it as meta_name
    if [[ -z $CLI_META_NAME ]]; then
      CLI_META_NAME="$1"
    else
      echo "Error: Too many arguments. Expected at most one meta_name, but got '$1'." >&2
      usage
      exit 1
    fi
    shift # Consume the argument
    ;;
  esac
done

# meta name can be passed as first arg
default_name="${CLI_META_NAME:-}"

# prompt user, with default
if [[ -n $default_name ]]; then
  read -r -e -i "$default_name" -p "Enter the name of the meta you would like to zip: " name
else
  read -r -p "Enter the name of the meta you would like to zip: " name
fi

# make directory for downloading new meta
mkdir -p "${filedrop}/${name}/rankings"
mkdir -p "${filedrop}/${name}/cupfile"
mkdir -p "${filedrop}/${name}/overrides"
mkdir -p "${filedrop}/${name}/group"

# rankings
cp -ar "${webrt}/data/rankings/${name}" "${filedrop}/${name}/rankings/"

# cup file
cp -a "${webrt}/data/gamemaster/cups/${name}.json" "${filedrop}/${name}/cupfile/"

# overrides file
cp -ar "${webrt}/data/overrides/${name}" "${filedrop}/${name}/overrides/"

# group file
cp -a "${webrt}/data/groups/${name}.json" "${filedrop}/${name}/group/"

# make zip version
cd "$filedrop"
zip -r "${name}.zip" "${name}"

zip_path="${filedrop}/${name}.zip"
zip_url="${uri_root}/${name}.zip"
echo
echo "Local zip file: ${zip_path}"
echo "Web URL: ${zip_url}"
