"""
reality_audit.data_analysis
============================
Real-data analysis readiness layer.

Provides the generic infrastructure required before any real public-data
experiment can be executed:
  - ExperimentRegistry  : structured metadata for each planned experiment
  - NullModelLibrary    : configurable null-model generators
  - SignalInjector      : synthetic signal injection for pipeline validation
  - Blinder             : blind / unblind result channels
  - ReportWriter        : structured JSON/CSV/Markdown reporting

These modules do NOT fetch external data.  They define the software contracts
that future ingestion adapters will fulfil.
"""

from reality_audit.data_analysis.experiment_registry import (
    ExperimentSpec,
    ExperimentRegistry,
)
from reality_audit.data_analysis.null_models import NullModelLibrary
from reality_audit.data_analysis.signal_injection import SignalInjector
from reality_audit.data_analysis.blinding import Blinder
from reality_audit.data_analysis.reporting import ReportWriter

__all__ = [
    "ExperimentSpec",
    "ExperimentRegistry",
    "NullModelLibrary",
    "SignalInjector",
    "Blinder",
    "ReportWriter",
]
