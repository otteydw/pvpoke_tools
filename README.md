# PvPoke Cup Management Scripts

TThis repository contains a set of shell scripts for managing "cups" (custom metas) for a [PvPoke](https://pvpoke.com/) instance. These scripts help automate the creation, cloning, renaming, and deletion of cup configurations, which include JSON files, rankings, and overrides

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

### `clone-cup.sh`

Clones an existing cup to create a new one. This is useful for creating a new cup based on an existing one.

**Usage:**

```bash
./clone-cup.sh <old_cup_name> <new_cup_name>
```

**Example:**

```bash
./clone-cup.sh december2025 january2026
```

### `delete-cup.sh`

Deletes a cup, including its associated directories and JSON files.

**Usage:**

```bash
./delete-cup.sh <cup_name>
```

**Example:**

```bash
./delete-cup.sh january2026
```

### `rename-cup.sh`

Renames an existing cup.

**Usage:**

```bash
./rename-cup.sh <old_cup_name> <new_cup_name>
```

**Example:**

```bash
./rename-cup.sh december2025 holidaycup2025
```

### `poke-create-files.sh`

A more interactive script to create all the necessary files for a new cup. It prompts for the cup name, title, and other details.

**Usage:**

```bash
./poke-create-files.sh
```

## Disclaimer

**⚠️ Warning:** These scripts directly modify the files in your PvPoke source directory. It is highly recommended to back up your data before running them.
