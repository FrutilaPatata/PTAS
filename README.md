# PTAS

**Pizza Tower TAS Assembly Language**

PTAS (Pizza Tower TAS Assembly) is a deterministic input scripting
language and compiler designed for creating Tool-Assisted Speedruns
(TAS) for *Pizza Tower*.

The project focuses on frame-perfect input control, human-readable
scripts, and reproducibility, without automating gameplay decisions.

------------------------------------------------------------------------

## Features

-   Deterministic, frame-perfect input scripting
-   Human-readable TAS scripts
-   Dynamic keymap loaded directly from Pizza Tower `saveData.ini`
-   Converts between `tas.txt` and `tas.ptm`
-   Designed specifically for TASers
-   No gameplay logic or automation

------------------------------------------------------------------------

## Project Structure

    ptas/
    ├─ main.py
    ├─ README.md
    └─ src/
       ├─ config.py
       └─ macros/

-   `main.py` --- PTAS compiler and CLI
-   `src/config.py` --- Loads key mappings from `saveData.ini`
-   `src/macros/` --- Reusable PTAS macro scripts (`.ptas`)

------------------------------------------------------------------------

## Usage

### Compile TAS script to Pizza Tower format

``` bash
python main.py --write
```

### Decode Pizza Tower TAS to readable script

``` bash
python main.py --read
```

### Dump active keymap

Displays the key mappings currently used by PTAS (loaded from
`saveData.ini`).

``` bash
python main.py --dump-keymap
```

------------------------------------------------------------------------

## Input Philosophy

PTAS operates strictly on **physical key inputs**.

-   PTAS does not interpret actions such as "jump" or "attack"
-   PTAS emits raw keycodes only
-   Gameplay behavior is fully determined by Pizza Tower's own
    configuration

This ensures determinism, reproducibility, and compatibility with
player-defined controls.

------------------------------------------------------------------------

## Versioning

-   **PTAS v1** --- Stable and frozen
-   **PTAS v2** --- In development

Future versions may introduce optional higher-level abstractions while
preserving full compatibility with PTAS v1 scripts.

------------------------------------------------------------------------

## Disclaimer

PTAS is an independent project and is not affiliated with the developers
of Pizza Tower.

------------------------------------------------------------------------

## License

To be determined.
