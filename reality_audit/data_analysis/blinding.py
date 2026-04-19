"""
blinding.py
===========
Blind / unblind support for real-data analysis.

Blinding discipline (from benchmark work):
  - freeze the analysis plan before looking at signal channels
  - write blinded summaries that hide result channels
  - preserve the reproducibility of the blinded state

A Blinder is created with a list of "blind_keys" — result keys that must
be hidden until the analysis plan is formally frozen.

Workflow
--------
1. Run analysis → get full_results dict.
2. blinder.blind(full_results) → blinded_results (safe to share/inspect).
3. Document analysis plan → call blinder.freeze(reason="...").
4. blinder.unblind(full_results) → full_results (unchanged, with audit trail).
5. blinder.save_blinded(full_results, path) and blinder.save_unblinded(...) 
   write separate JSON files.

Design note: the Blinder does NOT encrypt.  It operates on Python dicts in
memory and on disk.  The discipline is procedural (register intent first,
look at results second), not cryptographic.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any, Dict, List, Optional


class Blinder:
    """
    Manages blind / unblind lifecycle for a single analysis run.

    Parameters
    ----------
    blind_keys    : list of top-level result-dict keys to hide when blinded
    experiment_name : label for audit-trail entries
    """

    def __init__(
        self,
        blind_keys: List[str],
        experiment_name: str = "",
    ) -> None:
        self.blind_keys = list(blind_keys)
        self.experiment_name = experiment_name
        self.frozen: bool = False
        self.freeze_reason: str = ""
        self.freeze_timestamp: str = ""
        self._audit_trail: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def is_frozen(self) -> bool:
        return self.frozen

    def audit_trail(self) -> List[Dict[str, Any]]:
        return list(self._audit_trail)

    # ------------------------------------------------------------------
    # Freeze (lock the analysis plan)
    # ------------------------------------------------------------------

    def freeze(self, reason: str = "Analysis plan documented.") -> None:
        """
        Declare that the analysis plan is frozen.  After this call,
        unblind() is permitted.
        """
        self.frozen = True
        self.freeze_reason = reason
        self.freeze_timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        self._audit_trail.append({
            "event": "freeze",
            "reason": reason,
            "timestamp": self.freeze_timestamp,
        })

    # ------------------------------------------------------------------
    # Blind / Unblind
    # ------------------------------------------------------------------

    def blind(self, full_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return a copy of full_results with blind_keys replaced by
        the sentinel string "<BLINDED>".
        """
        blinded = dict(full_results)
        for k in self.blind_keys:
            if k in blinded:
                blinded[k] = "<BLINDED>"
        blinded["_blinding_status"] = "blinded"
        blinded["_blind_keys"] = self.blind_keys
        self._audit_trail.append({
            "event": "blind",
            "keys_hidden": self.blind_keys,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        })
        return blinded

    def unblind(self, full_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return the full, unblinded results.  Raises if not yet frozen.
        """
        if not self.frozen:
            raise RuntimeError(
                "Cannot unblind before the analysis plan is frozen. "
                "Call blinder.freeze(reason=...) first."
            )
        unblinded = dict(full_results)
        unblinded["_blinding_status"] = "unblinded"
        unblinded["_freeze_reason"] = self.freeze_reason
        unblinded["_freeze_timestamp"] = self.freeze_timestamp
        self._audit_trail.append({
            "event": "unblind",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        })
        return unblinded

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_blinded(
        self,
        full_results: Dict[str, Any],
        path: str,
    ) -> str:
        """Write blinded results to path.  Returns path."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        blinded = self.blind(full_results)
        blinded["_audit_trail"] = self.audit_trail()
        with open(path, "w") as f:
            json.dump(blinded, f, indent=2)
        return path

    def save_unblinded(
        self,
        full_results: Dict[str, Any],
        path: str,
    ) -> str:
        """
        Write unblinded results to path.  Raises if not frozen.
        Returns path.
        """
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        unblinded = self.unblind(full_results)
        unblinded["_audit_trail"] = self.audit_trail()
        with open(path, "w") as f:
            json.dump(unblinded, f, indent=2)
        return path

    def save_audit_trail(self, path: str) -> str:
        """Write the audit trail alone to path."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        trail = {
            "experiment_name": self.experiment_name,
            "blind_keys": self.blind_keys,
            "frozen": self.frozen,
            "freeze_reason": self.freeze_reason,
            "freeze_timestamp": self.freeze_timestamp,
            "audit_trail": self.audit_trail(),
        }
        with open(path, "w") as f:
            json.dump(trail, f, indent=2)
        return path

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        return {
            "experiment_name": self.experiment_name,
            "blind_keys": self.blind_keys,
            "frozen": self.frozen,
            "freeze_reason": self.freeze_reason,
            "freeze_timestamp": self.freeze_timestamp,
            "n_audit_events": len(self._audit_trail),
        }
