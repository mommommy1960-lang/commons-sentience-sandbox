#!/usr/bin/env python3
"""Fetch and SHA-256-verify the frozen official Fermi 2FLGC inputs."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/real/fermi_2flgc_official"
MANIFEST = DEST / "acquisition_manifest.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url: str, path: Path, expected: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or digest(path) != expected:
        with urllib.request.urlopen(url, timeout=180) as response:
            payload = response.read()
        if hashlib.sha256(payload).hexdigest() != expected:
            raise RuntimeError(f"digest mismatch for {url}")
        path.write_bytes(payload)
    if digest(path) != expected:
        raise RuntimeError(f"verification failed for {path}")
    print(f"VERIFIED {expected} {path.relative_to(ROOT)}")


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    for item in manifest["catalog"]:
        fetch(item["url"], DEST / item["path"], item["sha256"])
    for item in manifest["target_queries"]:
        prefix = f'{item["source"]}_{item["query_id"]}'
        for code, key in (("EV00", "event_sha256"), ("SC00", "spacecraft_sha256")):
            remote = f'{item["query_id"]}_{code}.fits'
            fetch(
                manifest["query_file_base"] + remote,
                DEST / "target_queries" / f"{prefix}_{code}.fits",
                item[key],
            )


if __name__ == "__main__":
    main()
