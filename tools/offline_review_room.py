#!/usr/bin/env python3
"""Dependency-free mailbox bridge for an offline code reviewer.

This tool never contacts the network. It packages exact local files with
SHA-256 hashes and records reviewer responses without interpreting them.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def prepare(args: argparse.Namespace) -> None:
    packet = Path(args.packet)
    blocks = [
        "# Offline Review Packet",
        "",
        "Evidence status: exact files supplied to the reviewer; no execution is implied.",
        "",
    ]
    for raw_path in args.files:
        path = Path(raw_path)
        data = path.read_bytes()
        blocks.extend([
            f"## FILE: {path}",
            f"SHA-256: {digest(data)}",
            "",
            "----- BEGIN FILE -----",
            data.decode("utf-8"),
            "----- END FILE -----",
            "",
        ])
    packet.parent.mkdir(parents=True, exist_ok=True)
    packet.write_text("\n".join(blocks), encoding="utf-8")

def start(args: argparse.Namespace) -> None:
    """Start a batch and leave an explicit waiting-state marker."""
    prepare(args)
    packet = Path(args.packet)
    status = packet.parent.parent / "STATUS.md"
    status.write_text(
        "# Offline Review Room Status\n\n"
        "State: WAITING_FOR_OFFLINE_REVIEW\n"
        f"Packet: {packet}\n"
        "No code changes are authorized by this state.\n"
        "Record the reviewer response before proposing repairs.\n",
        encoding="utf-8",
    )

def record(args: argparse.Namespace) -> None:
    packet = Path(args.packet)
    response = Path(args.response)
    record_path = Path(args.record)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(
        "# Offline Review Record\n\n"
        f"Packet: {packet}\n"
        f"Packet SHA-256: {digest(packet.read_bytes())}\n"
        f"Response SHA-256: {digest(response.read_bytes())}\n\n"
        "----- BEGIN REVIEW -----\n\n"
        + response.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Offline review-room mailbox bridge")
    sub = parser.add_subparsers(required=True)
    packet = sub.add_parser("prepare")
    packet.add_argument("--packet", required=True)
    packet.add_argument("--file", dest="files", action="append", required=True)
    packet.set_defaults(func=prepare)
    starter = sub.add_parser("start")
    starter.add_argument("--packet", required=True)
    starter.add_argument("--file", dest="files", action="append", required=True)
    starter.set_defaults(func=start)
    response = sub.add_parser("record")
    response.add_argument("--packet", required=True)
    response.add_argument("--response", required=True)
    response.add_argument("--record", required=True)
    response.set_defaults(func=record)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()