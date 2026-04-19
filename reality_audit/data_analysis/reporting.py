"""
reporting.py
============
Structured reporting for real-data analysis pipelines.

Produces:
  - JSON summary (machine-readable)
  - CSV row (for aggregation across runs)
  - Markdown methods summary (human-readable, journal-style)
  - Run manifest (lists all output files)

Design principles:
  - separate blinded and unblinded reports at write time
  - include reproducibility metadata in every report
  - produce a file manifest so outputs are always traceable
"""

from __future__ import annotations

import csv
import datetime
import json
import os
from typing import Any, Dict, List, Optional


class ReportWriter:
    """
    Writes structured analysis reports to disk.

    Parameters
    ----------
    output_dir  : base directory for all outputs
    experiment_name : label used in filenames and headers
    """

    def __init__(self, output_dir: str, experiment_name: str = "experiment") -> None:
        self.output_dir = output_dir
        self.experiment_name = experiment_name
        os.makedirs(output_dir, exist_ok=True)
        self._manifest: List[Dict[str, str]] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _path(self, filename: str) -> str:
        return os.path.join(self.output_dir, filename)

    def _record(self, path: str, description: str) -> None:
        self._manifest.append({
            "file": os.path.relpath(path),
            "description": description,
            "written_at": datetime.datetime.utcnow().isoformat() + "Z",
        })

    # ------------------------------------------------------------------
    # JSON summary
    # ------------------------------------------------------------------

    def write_json_summary(
        self,
        results: Dict[str, Any],
        filename: Optional[str] = None,
        blinded: bool = False,
    ) -> str:
        tag = "blinded" if blinded else "unblinded"
        fname = filename or f"{self.experiment_name}_{tag}_summary.json"
        path = self._path(fname)
        payload = {
            "experiment": self.experiment_name,
            "blinded": blinded,
            "written_at": datetime.datetime.utcnow().isoformat() + "Z",
            "results": results,
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
        self._record(path, f"JSON {tag} summary")
        return path

    # ------------------------------------------------------------------
    # CSV row
    # ------------------------------------------------------------------

    def write_csv_row(
        self,
        row: Dict[str, Any],
        filename: Optional[str] = None,
    ) -> str:
        fname = filename or f"{self.experiment_name}_results.csv"
        path = self._path(fname)
        write_header = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        self._record(path, "CSV result row")
        return path

    # ------------------------------------------------------------------
    # Markdown methods summary
    # ------------------------------------------------------------------

    def write_markdown_summary(
        self,
        results: Dict[str, Any],
        analysis_plan: str = "",
        filename: Optional[str] = None,
        blinded: bool = False,
    ) -> str:
        tag = "blinded" if blinded else "unblinded"
        fname = filename or f"{self.experiment_name}_{tag}_methods_summary.md"
        path = self._path(fname)

        lines = [
            f"# {self.experiment_name} — Methods Summary",
            "",
            f"**Generated:** {datetime.datetime.utcnow().isoformat()}Z",
            f"**Blinding status:** {tag}",
            "",
        ]

        if analysis_plan:
            lines += ["## Analysis Plan", "", analysis_plan, ""]

        lines += ["## Results", ""]
        if blinded:
            lines.append(
                "_Signal result channels are blinded. "
                "This summary is safe to share before unblinding._"
            )
        else:
            lines.append(
                "**Note:** This is the unblinded report. "
                "Share only after analysis plan is formally frozen."
            )
        lines.append("")

        for k, v in results.items():
            if v == "<BLINDED>":
                lines.append(f"- **{k}:** `<BLINDED>`")
            elif isinstance(v, float):
                lines.append(f"- **{k}:** {v:.6g}")
            elif isinstance(v, dict):
                lines.append(f"- **{k}:**")
                for kk, vv in v.items():
                    lines.append(f"  - {kk}: {vv}")
            else:
                lines.append(f"- **{k}:** {v}")

        lines += ["", "## Reproducibility", ""]
        repro = results.get("reproducibility", {})
        if repro:
            for k, v in repro.items():
                lines.append(f"- **{k}:** {v}")
        else:
            lines.append("_Reproducibility metadata not present in this result dict._")

        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")
        self._record(path, f"Markdown {tag} methods summary")
        return path

    # ------------------------------------------------------------------
    # Run manifest
    # ------------------------------------------------------------------

    def write_manifest(self, filename: Optional[str] = None) -> str:
        fname = filename or f"{self.experiment_name}_manifest.json"
        path = self._path(fname)
        payload = {
            "experiment": self.experiment_name,
            "written_at": datetime.datetime.utcnow().isoformat() + "Z",
            "files": self._manifest,
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
        return path

    # ------------------------------------------------------------------
    # Convenience: write everything
    # ------------------------------------------------------------------

    def write_all(
        self,
        blinded_results: Dict[str, Any],
        unblinded_results: Optional[Dict[str, Any]] = None,
        csv_row: Optional[Dict[str, Any]] = None,
        analysis_plan: str = "",
    ) -> Dict[str, str]:
        """
        Write blinded JSON + markdown, optionally unblinded, CSV row,
        and final manifest.  Returns dict of written paths.
        """
        paths: Dict[str, str] = {}
        paths["blinded_json"] = self.write_json_summary(
            blinded_results, blinded=True
        )
        paths["blinded_md"] = self.write_markdown_summary(
            blinded_results, analysis_plan=analysis_plan, blinded=True
        )
        if unblinded_results is not None:
            paths["unblinded_json"] = self.write_json_summary(
                unblinded_results, blinded=False
            )
            paths["unblinded_md"] = self.write_markdown_summary(
                unblinded_results, analysis_plan=analysis_plan, blinded=False
            )
        if csv_row is not None:
            paths["csv"] = self.write_csv_row(csv_row)
        paths["manifest"] = self.write_manifest()
        return paths
