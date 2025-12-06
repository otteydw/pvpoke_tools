#!/bin/bash
set -euo pipefail

webrt="/var/www/builder.devon.gg/public_html/pvpoke/src"
filedrop="/var/www/builder.devon.gg/public_html/pvpoke/filedrop"
uri_root="https://builder.devon.gg/pvpoke/filedrop"

# meta name can be passed as first arg
default_name="${1:-}"

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
echo "Zip file available at ${zip_path} and ${zip_url}"
