# Fate Grand Order NA Wars VN Reader

This Ren'Py project is an initial implementation of a Fate/Grand Order visual novel reader for NA Wars story scripts.

## Features
- Fetches Atlas Academy NA war metadata from the live API
- Downloads and caches raw script text locally
- Parses FGO script dialogue markers into Ren'Py dialogue flow
- Displays war name, script ID, and parsed dialogue in Ren'Py

## Structure
- `game/script.rpy` — Ren'Py entrypoint and playback flow
- `game/atlas_api.py` — Atlas Academy fetch and cache manager
- `game/fgo_parser.py` — basic FGO raw script parser
- `game/cache.py` — file-based HTTP cache for JSON and text

## Usage
1. Open this workspace as a Ren'Py project.
2. Launch Ren'Py and select the project.
3. Run the game.
4. Enter a NA War ID when prompted (for example `1000` or `30001`).

## Notes
- The parser currently supports basic dialogue and choice lines from Atlas Academy script text.
- Cache files are stored under `cache/atlas_academy/` inside the Ren'Py game directory.
- The frontend is intentionally minimal so the core fetching/caching/parser flow can be validated first.

## Next steps
- Add a scrollable war selection UI
- Add background and character asset download/render support
- Improve parser support for additional FGO script tags and visual commands
- Add support for other languages 
