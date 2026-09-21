# CARE: Compassionate Assisted Response Exchange

**Working name only — naming and trademark clearance are pending.**  
**Owner:** Mya P. Brown / Civic Continuum  
**Status:** public-safety architecture and simulation specification; not deployed

CARE is a proposed human-centered decision-support layer for emergency
communications. It accepts natural distressed speech and digital media, uses a
bounded Maya Node/SAGE service to structure facts and uncertainty, and helps a
trained telecommunicator route help. It does not decide whose life matters, make
autonomous law-enforcement judgments, or replace accountable emergency staff.

## Plain-language promise

The caller should not have to sound calm enough for a machine. The system should
adapt to the human in crisis, extract what is known, show what is uncertain, and
help the responsible professional send appropriate help faster.

## Public artifact map

- [Architecture and requirements](PUBLIC_SAFETY_ARCHITECTURE.md)
- [Risk and failure register](THREAT_AND_FAILURE_REGISTER.md)
- [Validation plan](VALIDATION_PLAN.md)
- [Reproducible routing simulation](../../tools/care_routing_sim.py)
- [Outreach record](../outreach/CARE_OUTREACH_LOG.md)

## Authority boundary

Maya Node/SAGE may transcribe, translate, extract candidate facts, identify
missing critical fields, propose questions, and prepare a **nonbinding** resource
pre-alert. A trained human remains responsible for final dispatch unless a
public authority has approved a narrowly specified deterministic rule with a
tested safe fallback. Confidence scores never become a measure of human worth.

