# Trolley NES Game

A continuous minecart/train game for the NES (Mapper 0, NROM).

## Gameplay
You control a train on tracks with many branches.
Avoid robots and holes!
Use Left/Right to switch tracks at junctions.

## Building (Python)
This project now uses a custom Python-based build script that leverages `py65`.

1. Run the build script:
   ```bash
   ./build.sh
   ```

   This will run `tools/build_rom.py` and generate `trolley.nes`.

## Building (Source)
- `src/main.s`: Main game logic (6502 assembly).
- `src/reset.s`: Initialization code.
- `assets/trolley.chr`: Graphics.

## Note
The build system was switched to Python to ensure compatibility where cc65 is not available.
