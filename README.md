# PvPoke Cup Management Scripts

This repository contains a set of shell scripts for managing "cups" (custom metas) for a [PvPoke](https://pvpoke.com/) instance. These scripts help automate the creation, cloning, renaming, and deletion of cup configurations, which include JSON files, rankings, and overrides.

## Prerequisites

- **[jq](https://stedolan.github.io/jq/):** A lightweight and flexible command-line JSON processor. This is required for manipulating the JSON files that define the cups.
- **[rpl](https://github.com/vrocher/rpl):** A command-line utility to replace strings in files. This is used in the `poke-create-files.sh` script.

## Configuration

The scripts expect a `PVPOKE_SRC_ROOT` environment variable to be set to the root directory of your PvPoke source code. If this variable is not set, it defaults to `/var/www/builder.devon.gg/public_html/pvpoke/src`.

You can set this variable in your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`) or export it before running the scripts:

```bash
export PVPOKE_SRC_ROOT="/path/to/your/pvpoke/src"
```

## Scripts

Here is a list of the available scripts and their primary functions:

### `clone-cup.sh`

Clones an existing PvPoke cup to a new one.
**Usage:** `./clone-cup.sh oldname newname`

### `delete-cup.sh`

Deletes an existing PvPoke cup.
**Usage:** `./delete-cup.sh cupname`

### `poke-create-files.sh`

Generates the files required to build a custom PvPoke meta.
**Usage:** `./poke-create-files.sh [--json-file <filename>]`

### `poke-create-meta-threat-group.sh`

Creates a 'meta threat group' JSON file by filtering Pokémon data.
**Usage:** `./poke-create-meta-threat-group.sh <threat_group_file> <pokemon_json_file>`

### `poke-zip-meta.sh`

Zips the files for a specified PvPoke meta, making them available for download.
**Usage:** `./poke-zip-meta.sh [meta_name]`

### `poke-zygarden-create-json.sh`

Generates a JSON configuration for Zygarde-related features based on an existing PvPoke cup's data.
**Usage:** `./poke-zygarden-create-json.sh <cupname>`

### `pvpoke-resolve-conflicts.sh`

Automates the resolution of common git merge conflicts in the pvpoke repository.
**Usage:** `./pvpoke-resolve-conflicts.sh`

### `pvpoke-rankings-sanity-check.py`

Validates PvPoke CSV rankings against a cup JSON file for inclusion/exclusion rules.
**Usage:** `./pvpoke-rankings-sanity-check.py <csv_path> <cup_json_path> <gamemaster_json_path>`

### `rename-cup.sh`

Renames an existing PvPoke cup.
**Usage:** `./rename-cup.sh oldname newname`

## Disclaimer

**⚠️ Warning:** These scripts directly modify the files in your PvPoke source directory. It is highly recommended to back up your data before running them.
