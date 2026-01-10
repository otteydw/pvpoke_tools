#!/bin/bash
# This script generates the files required to build a custom PvPoke meta
# Reference: https://github.com/pvpoke/pvpoke/wiki/Creating-New-Cups-&-Rankings
# ---------------------------------------------------------------
# WARNING: This script will overwrite certain files, so backups are important
# ---------------------------------------------------------------

# ---------------------------------------------
# Check for required commands
# ---------------------------------------------
command -v rpl >/dev/null 2>&1 || {
  echo >&2 "I require rpl but it's not installed.  Aborting."
  exit 1
}

# Set the root path for the PvPoke source files
webrt="${webrt:-/var/www/builder.devon.gg/public_html/pvpoke/src}"

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
echo -n "Enter the json structure for the meta (must be a single line): "
read -r cup
# Append user-provided JSON structure to the file
cat <<<"$cup" >>"${webrt}"/data/gamemaster/cups/"${name}".json

# Replace placeholders in JSON with actual codename and title
rpl -w "custom" "$name" "${webrt}"/data/gamemaster/cups/"${name}".json
rpl -w "Custom" "$title" "${webrt}"/data/gamemaster/cups/"${name}".json

# ---------------------------------------------
# Step 3: Backup existing formats files
# ---------------------------------------------
echo "I am now backing up all format files before proceeding ..."
cp "${webrt}"/data/gamemaster/formats.json "${webrt}"/data/gamemaster/formats-bu/formats-"${date}".json
cp "${webrt}"/data/gamemaster/formats-all.json "${webrt}"/data/gamemaster/formats-bu/formats-all-"${date}".json
cp "${webrt}"/data/gamemaster/formats-new.json "${webrt}"/data/gamemaster/formats-bu/formats-new-"${date}".json
sleep 2s

# ---------------------------------------------
# Step 4: Prepare new format listings for the meta
# ---------------------------------------------
echo "Editing the Gamemaster Format Listing to include your new meta ..."
sleep 2s

cp "${webrt}"/data/gamemaster/formats-all.json "${webrt}"/data/gamemaster/formats-bu/formats-all-"${date}".json

# Make copies of formats-new.json and formats-all.json for the new meta
cp "${webrt}"/data/gamemaster/formats-new.json "${webrt}"/data/gamemaster/formats-bu/formats-"${name}"-new.json
cp "${webrt}"/data/gamemaster/formats-all.json "${webrt}"/data/gamemaster/formats-bu/formats-"${name}"-all.json

echo "The necessary files are created, now editing the name and title ..."
sleep 2s

# Replace placeholder names and titles in the new copies
rpl -w "custom" "$name" "${webrt}"/data/gamemaster/formats-bu/formats-"${name}"-new.json
rpl -w "Custom" "$title" "${webrt}"/data/gamemaster/formats-bu/formats-"${name}"-new.json
rpl -w "great" "$name" "${webrt}"/data/gamemaster/formats-bu/formats-"${name}"-new.json

# ---------------------------------------------
# Step 5: Merge new meta into formats.json
# ---------------------------------------------
echo "Adding the new meta to formats.json in gamemaster, creating a backup ..."
sleep 2s
cat "${webrt}"/data/gamemaster/formats-bu/formats-"${name}"-new.json >>"${webrt}"/data/gamemaster/formats-bu/formats-"${name}"-all.json

# Backup current formats.json
mv "${webrt}"/data/gamemaster/formats.json "${webrt}"/data/gamemaster/formats-bu/formats-"${date}".json

# Replace formats.json with the updated version
cp -ar "${webrt}"/data/gamemaster/formats-bu/formats-"${name}"-all.json "${webrt}"/data/gamemaster/formats.json

# ---------------------------------------------
# Step 6: Clean up temporary files and fix JSON structure
# ---------------------------------------------
echo "Removing temporary files and finalizing formats-all.json ..."
sleep 2s

# Remove the last line twice to prevent duplicate closing braces
head -n -1 "${webrt}"/data/gamemaster/formats-bu/formats-"${name}"-all.json >"${webrt}"/data/gamemaster/formats-bu/formats-temp1.json
head -n -1 "${webrt}"/data/gamemaster/formats-bu/formats-temp1.json >"${webrt}"/data/gamemaster/formats-bu/formats-temp2.json

# Add a comma to allow further meta entries
echo "        }," >>"${webrt}"/data/gamemaster/formats-bu/formats-temp2.json

# Replace formats-all.json with the cleaned-up version
mv "${webrt}"/data/gamemaster/formats-bu/formats-temp2.json "${webrt}"/data/gamemaster/formats-all.json

# Remove intermediate temporary files
rm "${webrt}"/data/gamemaster/formats-bu/formats-"${name}"-all.json
rm "${webrt}"/data/gamemaster/formats-bu/formats-"${name}"-new.json
rm "${webrt}"/data/gamemaster/formats-bu/formats-temp1.json

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
chmod 777 -R /var/www/builder.devon.gg/public_html/pvpoke/
sleep 2s
