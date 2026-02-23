# Trolley NES Game

A continuous minecart/train game for the NES (Mapper 0, NROM).

## Gameplay
You control a train on tracks with many branches.
Avoid robots and holes!
Use Left/Right to switch tracks at junctions.

## Development Environment
This project uses the **cc65** toolchain.

### Prerequisites
1.  **cc65**: Install via your package manager.
    -   Ubuntu/Debian: `sudo apt install cc65`
    -   macOS: `brew install cc65`
    -   Windows: Download from https://cc65.github.io/

### Building
Run the build script:
```bash
./build.sh
```
This will generate `trolley.nes`.

### Running
Open `trolley.nes` in any NES emulator (FCEUX, Mesen, Nestopia).

## Controls
-   **Left/Right**: Move Train
-   **A/B**: Action (Planned)

## Project Structure
-   `src/`: Assembly source code (.s)
-   `assets/`: Graphics (.chr)
-   `cfg/`: Linker configuration (.cfg)
-   `tools/`: Asset generation scripts (.py)
