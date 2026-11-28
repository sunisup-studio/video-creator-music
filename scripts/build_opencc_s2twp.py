#!/usr/bin/env python3
"""Build a deterministic 2-pass OpenCC s2twp TSV dictionary for offline zh-TW conversion."""

from __future__ import annotations

import hashlib
import os
import urllib.request
from pathlib import Path

OPENCC_BASE_URL = (
    "https://raw.githubusercontent.com/BYVoid/OpenCC/ver.1.1.9/data/dictionary/"
)

ST_FILES = ("STPhrases.txt", "STCharacters.txt")
TW_FILES = ("TWPhrasesIT.txt", "TWPhrasesName.txt", "TWPhrasesOther.txt", "TWVariants.txt")


def fetch_lines(filename: str) -> list[str]:
    url = f"{OPENCC_BASE_URL}{filename}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8").splitlines()


def merge_dictionary(files: tuple[str, ...]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for filename in files:
        for raw_line in fetch_lines(filename):
            line = raw_line.strip()
            if not line or line.startswith("#") or "\t" not in line:
                continue
            key, rhs = line.split("\t", 1)
            candidates = rhs.strip().split()
            if not candidates:
                continue
            value = candidates[0]
            if not key or not value or key == value:
                continue
            if key not in merged:
                merged[key] = value
    return merged


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    out_path = repo_root / "stt" / "opencc_s2twp.tsv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    st_map = merge_dictionary(ST_FILES)
    tw_map = merge_dictionary(TW_FILES)

    lines = [
        "# OpenCC s2twp compiled dictionary (Apache-2.0, BYVoid/OpenCC ver.1.1.9)",
        "[ST]",
    ]
    for key in sorted(st_map):
        lines.append(f"{key}\t{st_map[key]}")
    lines.append("[TW]")
    for key in sorted(tw_map):
        lines.append(f"{key}\t{tw_map[key]}")

    payload = ("\n".join(lines) + "\n").encode("utf-8")
    out_path.write_bytes(payload)

    sha256_hex = hashlib.sha256(payload).hexdigest()
    size_bytes = os.path.getsize(out_path)
    print(f"Wrote {out_path}")
    print(f"ST entries: {len(st_map)}, TW entries: {len(tw_map)}")
    print(f"sizeBytes: {size_bytes}")
    print(f"sha256: {sha256_hex}")


if __name__ == "__main__":
    main()
