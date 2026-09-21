# CARE: Compassionate Assisted Response Exchange

**Working name only — naming and trademark clearance are pending.**  
**Owner:** Mya P. Brown / Civic Continuum  
**Status:** public-safety architecture and simulation specification; not deployed

CARE is a proposed AI-first, human-authorized decision-support layer for
emergency communications. It accepts natural distressed speech and digital
media, uses a bounded Maya Node/SAGE service to structure facts and uncertainty,
and helps a trained telecommunicator send appropriate help. It does not decide
whose life matters, make autonomous law-enforcement judgments, or replace
accountable emergency staff.

## Plain-language promise

The caller should not have to sound calm enough for a machine. While the caller
speaks, the system should preserve the call, find location candidates, extract
what is known, show what is uncertain, identify appropriate available response
options, and hand a clear incident card to the responsible professional for
confirmation and authorization.

## Public artifact map

- [Architecture and requirements](PUBLIC_SAFETY_ARCHITECTURE.md)
- [Operator console specification](OPERATOR_CONSOLE_SPEC.md)
- [Twenty design improvements and pilot gates](TWENTY_DESIGN_IMPROVEMENTS.md)
- [Risk and failure register](THREAT_AND_FAILURE_REGISTER.md)
- [Validation plan](VALIDATION_PLAN.md)
- [Reproducible routing simulation](../../tools/care_routing_sim.py)
- [Verified outreach record](../outreach/CARE_OUTREACH_LOG.md)

## Authority boundary

Maya Node/SAGE may transcribe, translate, extract candidate facts, identify
missing critical fields, estimate location with provenance, rank only eligible
resources, propose questions, and prepare a nonbinding pre-alert. A trained human
remains responsible for final dispatch by default. Confidence scores never
become a measure of human worth.
