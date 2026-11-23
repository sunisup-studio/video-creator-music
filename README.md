# Video Creator Music & SFX Catalog Repository

Standalone static catalog repository for **Video Creator v2**.

## Layout
- `catalog.json`: Root `schemaVersion = 1` manifest fetched by the app (`<MUSIC_CATALOG_BASE_URL>catalog.json`).
- `tracks/music/`: Royalty-free music tracks (`.m4a` / `.mp3`).
- `tracks/sfx/`: Royalty-free sound effects (`.wav` / `.m4a` / `.mp3`).
- `ATTRIBUTION.md`: License & artist attribution log for every track in the catalog.
- `scripts/build_catalog.py`: Generates deterministic `catalog.json` from `tracks/music/` and `tracks/sfx/`.

## Usage
1. Drop audio files into `tracks/music/<category>/` or `tracks/sfx/<category>/` (or flat under `tracks/music/` / `tracks/sfx/`).
2. Run:
   ```bash
   python3 scripts/build_catalog.py --root . --output catalog.json
   ```
3. Commit `catalog.json`, `ATTRIBUTION.md`, and audio assets (or upload large assets to GitHub Releases and set `filePath` to the `https://` release asset URL).
4. To point the Android app at a custom mirror (e.g., Cloudflare R2), set `MUSIC_CATALOG_BASE_URL` in `local.properties` or pass `-PmusicCatalogBaseUrl=...`.
