from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class EvidenceItem:
    label: str
    kind: str
    reference: str
    digest: str
    created_at: str = field(default_factory=utc_now)


@dataclass
class ProvenanceRecord:
    title: str
    author: str
    purpose: str
    public_boundary: str
    version: str = "0.1"
    created_at: str = field(default_factory=utc_now)
    evidence: list[EvidenceItem] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    def add_text_evidence(self, label: str, text: str) -> EvidenceItem:
        item = EvidenceItem(
            label=label,
            kind="text",
            reference=f"inline:{label}",
            digest=sha256_text(text),
        )
        self.evidence.append(item)
        self.events.append(
            {
                "event": "evidence_added",
                "label": label,
                "kind": item.kind,
                "digest": item.digest,
                "timestamp": utc_now(),
            }
        )
        return item

    def add_file_evidence(self, path: str | Path, label: str | None = None) -> EvidenceItem:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        item = EvidenceItem(
            label=label or file_path.name,
            kind="file",
            reference=str(file_path),
            digest=sha256_file(file_path),
        )
        self.evidence.append(item)
        self.events.append(
            {
                "event": "evidence_added",
                "label": item.label,
                "kind": item.kind,
                "digest": item.digest,
                "timestamp": utc_now(),
            }
        )
        return item

    def add_event(self, event: str, note: str) -> dict[str, Any]:
        entry = {"event": event, "note": note, "timestamp": utc_now()}
        self.events.append(entry)
        return entry

    def record_hash(self) -> str:
        payload = asdict(self)
        payload["events"] = sorted(payload["events"], key=lambda e: json.dumps(e, sort_keys=True))
        payload["evidence"] = sorted(payload["evidence"], key=lambda e: e["digest"])
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256_text(encoded)

    def to_json(self) -> str:
        payload = asdict(self)
        payload["record_hash"] = self.record_hash()
        return json.dumps(payload, indent=2, sort_keys=True)


def demo_record() -> ProvenanceRecord:
    record = ProvenanceRecord(
        title="Consent Token Review and Demo Pack",
        author="Mya P. Brown",
        purpose="Preserve the launch state for the first Civic Continuum consent review offer.",
        public_boundary="Public offer copy is shareable. Customer records, private project files, and payment details stay private.",
    )
    record.add_text_evidence(
        "offer_summary",
        "A plain-language review of one AI workflow or project decision focused on permission, revocation, and auditability.",
    )
    record.add_event("launch_ready", "Offer copy, boundaries, and starting price are ready for a payment link.")
    return record


if __name__ == "__main__":
    print(demo_record().to_json())
