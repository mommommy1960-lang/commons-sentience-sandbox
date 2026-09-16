#!/usr/bin/env python3
"""Durable, reviewable work queue for Civic Continuum experiments.

This is orchestration, not an autonomous mind. It never grants permissions,
executes arbitrary code, contacts people, or changes repository files.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any


STATUSES = {"queued", "running", "paused", "completed", "failed", "cancelled"}
TERMINAL = {"completed", "failed", "cancelled"}
ALLOWED_TRANSITIONS = {
    "queued": {"running", "paused", "cancelled"},
    "running": {"paused", "completed", "failed", "cancelled"},
    "paused": {"running", "cancelled"},
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


class JobQueue:
    """A small JSON-backed queue with explicit controls and an append-only audit log."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data = {"schema_version": 1, "jobs": [], "events": []}
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
            self._validate_document()

    def _validate_document(self) -> None:
        if self.data.get("schema_version") != 1:
            raise ValueError("unsupported queue schema_version")
        if not isinstance(self.data.get("jobs"), list) or not isinstance(self.data.get("events"), list):
            raise ValueError("queue jobs and events must be lists")
        job_ids: set[str] = set()
        for job in self.data["jobs"]:
            if not isinstance(job, dict):
                raise ValueError("queue jobs must be objects")
            job_id = job.get("id")
            if not isinstance(job_id, str) or not job_id.strip():
                raise ValueError("job requires id and question")
            if job_id in job_ids:
                raise ValueError("duplicate job id")
            job_ids.add(job_id)
            if job.get("status") not in STATUSES:
                raise ValueError("invalid job status")
            if not job.get("id") or not job.get("question"):
                raise ValueError("job requires id and question")
            if type(job.get("budget_steps")) is not int or job["budget_steps"] < 1:
                raise ValueError("budget_steps must be a positive integer")
            steps_used = job.get("steps_used")
            if (
                type(steps_used) is not int
                or steps_used < 0
                or steps_used > job["budget_steps"]
            ):
                raise ValueError("steps_used must be within the job budget")
        for event in self.data["events"]:
            if not isinstance(event.get("job_id"), str) or event["job_id"] not in job_ids:
                raise ValueError("audit event references unknown job")
            if not isinstance(event.get("event"), str) or not event["event"].strip():
                raise ValueError("audit event requires event")
            if not isinstance(event.get("detail"), str):
                raise ValueError("audit event detail must be a string")
        if not self.verify_audit_chain():
            raise ValueError("queue audit chain is invalid")

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _event(self, job_id: str, event: str, detail: str) -> None:
        previous = self.data["events"][-1]["hash"] if self.data["events"] else "GENESIS"
        body = {"job_id": job_id, "event": event, "detail": detail, "previous_hash": previous}
        body["hash"] = _sha256(body)
        self.data["events"].append(body)

    def create(self, question: str, budget_steps: int = 5, stopping_condition: str = "") -> dict:
        if not question.strip():
            raise ValueError("question must not be empty")
        if budget_steps < 1:
            raise ValueError("budget_steps must be positive")
        job = {
            "id": str(uuid.uuid4()),
            "question": question.strip(),
            "status": "queued",
            "budget_steps": budget_steps,
            "steps_used": 0,
            "stopping_condition": stopping_condition.strip(),
            "created_at": int(time.time()),
            "result": None,
        }
        self.data["jobs"].append(job)
        self._event(job["id"], "created", "queued for explicit worker review")
        self._save()
        return job.copy()

    def _get(self, job_id: str) -> dict:
        for job in self.data["jobs"]:
            if job["id"] == job_id:
                return job
        raise KeyError(job_id)

    def transition(self, job_id: str, status: str, detail: str = "") -> dict:
        if status not in STATUSES:
            raise ValueError("invalid status")
        job = self._get(job_id)
        if job["status"] in TERMINAL:
            raise ValueError("terminal jobs cannot be changed")
        if status not in ALLOWED_TRANSITIONS.get(job["status"], set()):
            raise ValueError(
                f"invalid transition: {job['status']} -> {status}"
            )
        if status == "running" and job["steps_used"] >= job["budget_steps"]:
            raise ValueError("step budget exhausted")
        job["status"] = status
        self._event(job_id, status, detail or f"status changed to {status}")
        self._save()
        return job.copy()

    def record_step(self, job_id: str, phase: str, output: Any, evidence: list[str] | None = None) -> dict:
        job = self._get(job_id)
        if job["status"] != "running":
            raise ValueError("job must be running to record a step")
        if job["steps_used"] >= job["budget_steps"]:
            raise ValueError("step budget exhausted")
        job["steps_used"] += 1
        payload = {"phase": phase, "output": output, "evidence": evidence or []}
        fingerprint = _sha256(payload)
        self._event(job_id, "step", f"{phase}; evidence_sha256={fingerprint}")
        self._save()
        return {"job_id": job_id, "step": job["steps_used"], "fingerprint": fingerprint}

    def report(self, job_id: str, result: Any) -> dict:
        job = self._get(job_id)
        if job["status"] not in {"running", "paused"}:
            raise ValueError("job must be running or paused to report")
        job["result"] = {"value": result, "sha256": _sha256(result)}
        self._event(job_id, "report", "result recorded; not independently verified")
        self._save()
        return job.copy()

    def list_jobs(self) -> list[dict]:
        return [job.copy() for job in self.data["jobs"]]

    def verify_audit_chain(self) -> bool:
        previous = "GENESIS"
        required = ("job_id", "event", "detail", "previous_hash", "hash")
        for event in self.data["events"]:
            if not isinstance(event, dict) or any(key not in event for key in required):
                return False
            original = {key: event[key] for key in required[:-1]}
            if event["previous_hash"] != previous or event["hash"] != _sha256(original):
                return False
            previous = event["hash"]
        return True


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("question")
    create.add_argument("--budget-steps", type=int, default=5)
    create.add_argument("--stopping-condition", default="")
    sub.add_parser("list")
    verify = sub.add_parser("verify")
    args = parser.parse_args()
    queue = JobQueue(args.path)
    if args.command == "create":
        print(json.dumps(queue.create(args.question, args.budget_steps, args.stopping_condition), indent=2))
    elif args.command == "list":
        print(json.dumps(queue.list_jobs(), indent=2))
    else:
        print(json.dumps({"audit_chain_valid": queue.verify_audit_chain()}))


if __name__ == "__main__":
    main()
