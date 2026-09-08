"""Machine-readable naming and reproducibility contract for audit artifacts."""

from __future__ import annotations

import hashlib
import os
import re
from typing import Any, Dict, Iterable, Mapping, Optional

VALID_MODES = frozenset(("exploratory", "confirmatory"))
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def normalize_mode(run_mode: str) -> str:
    if run_mode == "preregistered_confirmatory":
        return "confirmatory"
    if run_mode in VALID_MODES:
        return run_mode
    raise ValueError(f"Unsupported run mode: {run_mode!r}")


def artifact_name(stage: int | str, mode: str, catalog: str, run_id: str,
                  artifact: str, extension: str = "json") -> str:
    """Return ``stage_mode_catalog_runid_artifact.extension``."""
    fields = (str(stage), normalize_mode(mode), catalog, run_id, artifact)
    if any(not _TOKEN.match(value) for value in fields):
        raise ValueError("artifact name fields must be simple non-empty tokens")
    extension = extension.lstrip(".")
    if not _TOKEN.match(extension):
        raise ValueError("extension must be a simple token")
    return "_".join(fields) + "." + extension


def sha256_file(path: str) -> Optional[str]:
    """Return a file digest, or None when the input is unavailable."""
    if not os.path.isfile(path):
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_reproducibility_contract(
    *, stage: int | str, run_mode: str, catalog: str, run_id: str,
    input_files: Iterable[str] = (), code_version: str = "unknown",
    seed: Optional[int] = None, null_model: Any = None,
    axis_count: Optional[int] = None,
    trial_correction_method: Optional[str] = None,
    preregistration_hash: Optional[str] = None,
    preregistration_locked: Optional[bool] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a stable contract block suitable for a run manifest."""
    inputs = [{"path": str(path), "sha256": sha256_file(str(path))}
              for path in input_files]
    result: Dict[str, Any] = {
        "contract_version": "1.0",
        "stage": int(stage),
        "run_mode": normalize_mode(run_mode),
        "catalog": catalog,
        "run_id": run_id,
        "code_version": code_version,
        "inputs": inputs,
        "seed": seed,
        "null_model": null_model,
        "axis_count": axis_count,
        "trial_correction_method": trial_correction_method,
        "preregistration_hash": preregistration_hash,
        "preregistration_locked": preregistration_locked,
    }
    if extra:
        result["extra"] = dict(extra)
    return result

