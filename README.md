# PvPoke Cup Management Scripts

This repository contains a set of scripts for managing "cups" (custom metas) for a [PvPoke](https://pvpoke.com/) instance. These scripts help automate the creation, cloning, renaming, and deletion of cup configurations, which include JSON files, rankings, and overrides.

## Prerequisites

- **[jq](https://stedolan.github.io/jq/):** A lightweight and flexible command-line JSON processor. This is required for manipulating the JSON files that define the cups.
- **[rpl](https://github.com/vrocher/rpl):** A command-line utility to replace strings in files. This is used in the `poke-create-files.sh` script.
- **Python 3:** With `pandas` libraries for the validation scripts.

## Configuration

Some scripts expect a `PVPOKE_SRC_ROOT` environment variable to be set to the root directory of your PvPoke source code. If this variable is not set, those scripts will fail.

You can set this variable in your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`) or export it before running the scripts:

```bash
export PVPOKE_SRC_ROOT="/path/to/your/pvpoke/src"
```

## Scripts

Here is a list of the available scripts and their primary functions:

### Cup Management

#### `cup-clone.sh`

Clones an existing PvPoke cup to a new one.

**Usage:**

```bash
./cup-clone.sh oldname newname
```

#### `cup-delete.sh`

Deletes an existing PvPoke cup.

**Usage:**

```bash
./cup-delete.sh cupname
```

#### `cup-rename.sh`

Renames an existing PvPoke cup.

**Usage:**

```bash
./cup-rename.sh oldname newname
```

### Cup File Generation

#### `poke-create-files.sh`

Generates the files required to build a custom PvPoke meta.

**Usage:**

```bash
./poke-create-files.sh [--json-file <filename>]
```

#### `poke-create-meta-threat-group.sh`

Creates a 'meta threat group' JSON file by filtering a cup's override file.

**Usage:**

```bash
./poke-create-meta-threat-group.sh <threat_group_file> <cup_overrides_json_file>
```

#### `poke-zip-meta.sh`

Zips the files for a specified PvPoke meta, making them available for download.

**Usage:**

```bash
./poke-zip-meta.sh [meta_name]
```

#### `poke-zygarden-create-json.sh`

Generates a JSON configuration for Zygarden-related features based on an existing PvPoke cup's data. It can extract data from a cup name in `PVPOKE_SRC_ROOT` or directly from a zipped archive.

**Usage (from PVPOKE_SRC_ROOT):**

```bash
./poke-zygarden-create-json.sh --json <cupname>
```

**Usage (from zip file):**

```bash
./poke-zygarden-create-json.sh --zip <zipfile>
```

### Validation Scripts

#### `pvpoke-cup-validator.py`

Validates a PvPoke cup JSON file against the gamemaster data to ensure all mentioned species and moves exist.

**Usage:**

```bash
PVPOKE_SRC_ROOT=/path/to/src ./pvpoke-cup-validator.py <cup_json_path>
```

#### `pvpoke-rankings-sanity-check.py`

Validates PvPoke CSV rankings against a cup JSON file for inclusion/exclusion rules. It uses `PVPOKE_SRC_ROOT` to locate `gamemaster.json` and `moves.json`.

**Usage:**

```bash
PVPOKE_SRC_ROOT=/path/to/src ./pvpoke-rankings-sanity-check.py <csv_path> <cup_json_path>
```

#### `pvpoke-zip-validator.py`

Validates a zipped cup archive, checking file structure, and ensuring all species and moves in the rankings and overrides are valid and adhere to the cup's rules.

**Usage:**

```bash
PVPOKE_SRC_ROOT=/path/to/src ./pvpoke-zip-validator.py <zip_file_path>
```

### Utility Scripts

#### `pvpoke-resolve-conflicts.sh`

Automates the resolution of common git merge conflicts in the pvpoke repository.

**Usage:**

```bash
./pvpoke-resolve-conflicts.sh
```

## Disclaimer

**⚠️ Warning:** These scripts directly modify the files in your PvPoke source directory. It is highly recommended to back up your data before running them.
