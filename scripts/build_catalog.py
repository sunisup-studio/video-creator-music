#!/usr/bin/env python3
"""Scans tracks/music/ and tracks/sfx/ to generate a deterministic catalog.json manifest."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

SUPPORTED_EXTENSIONS = {".m4a", ".mp3", ".wav", ".ogg", ".aac", ".flac"}
VALID_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
DEFAULT_DURATION_MS = 30_000


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_duration_ms(path: Path) -> int:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return DEFAULT_DURATION_MS
    try:
        proc = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        seconds = float(proc.stdout.strip())
        if seconds > 0:
            return max(1, int(round(seconds * 1000)))
    except (subprocess.SubprocessError, ValueError):
        pass
    return DEFAULT_DURATION_MS


def title_from_stem(stem: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[_-]+", stem) if part) or "Untitled"


def load_metadata_overrides(root: Path) -> dict[str, dict]:
    metadata_path = root / "tracks" / "metadata.json"
    if not metadata_path.is_file():
        return {}
    raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {metadata_path}")
    return {k: v for k, v in raw.items() if isinstance(v, dict)}


def scan_kind(root: Path, subdir: str, kind: str, metadata_overrides: dict[str, dict]) -> list[dict]:
    base_dir = root / "tracks" / subdir
    if not base_dir.is_dir():
        return []
    entries = []
    for file_path in sorted(base_dir.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        rel_path = file_path.relative_to(root).as_posix()
        rel_parts = file_path.relative_to(base_dir).parts
        category = rel_parts[0].capitalize() if len(rel_parts) > 1 else "General"
        track_id = re.sub(r"[^a-z0-9_-]+", "_", file_path.stem.lower()).strip("_-")
        if not track_id or not VALID_ID_PATTERN.match(track_id):
            raise ValueError(f"Invalid derived track id '{track_id}' for {rel_path}")
        entry = {
            "id": track_id,
            "title": title_from_stem(file_path.stem),
            "artist": "Studio Catalog",
            "kind": kind,
            "category": category,
            "durationMs": probe_duration_ms(file_path),
            "filePath": rel_path,
            "fileSizeBytes": file_path.stat().st_size,
            "license": "CC0",
            "sha256": compute_sha256(file_path),
            "tags": [category.lower()],
        }
        override = metadata_overrides.get(track_id)
        if override:
            for field in ("title", "artist", "license", "licenseUrl", "bpm", "tags"):
                if field in override and override[field] is not None:
                    entry[field] = override[field]
        entries.append(entry)
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Video Creator music catalog.json")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    output_path = (args.output or (root / "catalog.json")).resolve()
    metadata_overrides = load_metadata_overrides(root)

    tracks = scan_kind(root, "music", "MUSIC", metadata_overrides) + scan_kind(
        root, "sfx", "SFX", metadata_overrides
    )
    seen_ids: set[str] = set()
    for track in tracks:
        if track["id"] in seen_ids:
            raise ValueError(f"Duplicate track id: {track['id']}")
        seen_ids.add(track["id"])

    manifest = {
        "schemaVersion": 1,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tracks": tracks,
    }
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(tracks)} track(s) to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
