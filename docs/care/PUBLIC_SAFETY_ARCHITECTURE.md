# CARE public-safety architecture v0.2

## Purpose

CARE is an AI-assisted emergency-intake and decision-support overlay for 911/NG911. It is designed to understand people in distress without requiring them to speak calmly, organize the available evidence quickly, and help an accountable human telecommunicator make a faster, better-informed decision.

It is not an autonomous police-dispatch system and it does not replace the 911 workforce.

## Operating model: AI first, human authorized

1. **Answer immediately.** Accept voice, real-time text, text, image, video, location, or an authorized device alert through an NG911-compatible interface.
2. **Preserve the source.** Retain original audio, text, media, timestamps, and provenance unchanged.
3. **Work concurrently.** While the caller speaks, CARE:
   - transcribes and, when needed, translates;
   - estimates a dispatchable location using authorized network/device sources;
   - extracts candidate facts and competing interpretations;
   - detects critical hazards and unanswered questions;
   - queries CAD/AVL for eligible response resources;
   - builds a proposed response and agency-policy escalation path.
4. **Do not demand calmness.** The system must tolerate distress, screaming, fragmentary speech, open-line calls, silence, background noise, and disconnection.
5. **Show an incident card.** A human receives the address/location and confidence, incident type, injuries, hazards, people and clothing descriptions, callback path, source-linked evidence, contradictions, unanswered critical fields, and several eligible resource options.
6. **Rank appropriate resources.** “Closest” means closest appropriate, available, jurisdictionally authorized unit with the required capability—not merely the smallest straight-line distance.
7. **Human confirm/correct/authorize.** The telecommunicator can replay evidence, edit extracted facts, ask one high-value question, take over instantly, select resources, pause, escalate under agency policy, and authorize dispatch.
8. **Preserve accountability.** Log what the caller supplied, what the model inferred, what the human changed, the policy used, timestamps, confidence, and the final authority.
9. **Fail safely.** If AI, location, network, CAD, or sensor services fail, ordinary emergency call handling continues.

Agency-approved pre-alerts may occur before final confirmation when policy permits. Final dispatch authority remains human by default.

Satellite links are communications transport and possible location sources, not independent dispatch authorities. Maya Node/SAGE may supply bounded decision-support services but may not silently dispatch, cancel help, or assign criminality.

## Resource-ranking rule

A unit is eligible only if it is:

- available;
- within the responsible jurisdiction or covered by an approved mutual-aid rule;
- equipped and trained for the incident;
- reachable given traffic, closures, hazards, and travel conditions;
- permitted by agency policy.

Only eligible units are ranked by estimated arrival time and response fit. The interface must show several candidates and the reason for the ranking. Protected traits, neighborhood stereotypes, caller emotion, and predicted “deservedness” are forbidden inputs.

## Stable requirements

| ID | Requirement | Verification |
|---|---|---|
| CR-001 | Original caller audio/text/media remains available to the operator. | Replay test |
| CR-002 | Distress, accent, dialect, disability, language, or noise does not reduce credibility or priority by itself. | Stratified performance audit |
| CR-003 | Every extracted fact links to source evidence or is labeled reported/inferred/unknown. | Traceability test |
| CR-004 | Uncertainty, alternatives, and contradictions are visible. | Scenario test |
| CR-005 | Final dispatch authority remains human by default. | Access-control test |
| CR-006 | Any failed AI component permits ordinary call handling. | Failover test |
| CR-007 | Location displays source, timestamp, uncertainty, and spoof/conflict warnings. | Location test |
| CR-008 | Unit recommendations enforce availability, capability, jurisdiction, travel time, and policy. | CAD/AVL simulation |
| CR-009 | Only agency-approved pre-arrival instructions may be presented; no improvisation. | Protocol-conformance test |
| CR-010 | The operator has one-action takeover, correction, confirmation, and dispatch controls. | Human-factors test |
| CR-011 | Silent/open-line, disconnected, multilingual, and media-rich calls have tested paths. | Scenario suite |
| CR-012 | False dispatch, missed dispatch, delay, and inappropriate response mix are measured separately. | Outcome analysis |
| CR-013 | The system resists spoofing, replay, malicious media instructions, and location manipulation. | Adversarial test |
| CR-014 | No model infers criminality, dangerousness, or deservedness from protected traits or emotional presentation. | Model/policy audit |
| CR-015 | Data collection, access, sharing, and retention are minimized and policy-controlled. | Privacy review |
| CR-016 | Suspected terrorism or major-incident escalation follows predefined policy; the model does not casually label an event. | Escalation test |
| CR-017 | Duplicate calls can be linked without suppressing distinct victims or evidence. | Multi-call test |
| CR-018 | Human edits never erase the original model output or source evidence. | Audit test |
| CR-019 | Performance is reported by language, accent, disability, sex/gender where lawful, age band, and acoustic condition. | Bias audit |
| CR-020 | Agencies publish accountability, appeal, incident-reporting, workforce, and shutdown procedures before live use. | Governance review |

## Workforce rule

CARE must be tested as a tool that strengthens telecommunicators, not justified by an assumed head-count reduction. Early pilots require trained people for supervision, takeover, quality assurance, cybersecurity, model monitoring, and difficult calls. Staffing changes may be considered only after independent workload, safety, labor, and human-factors evidence.

## Maya Node/SAGE bounded outputs

- verbatim transcript and alternatives;
- structured, source-linked incident card;
- location candidates with confidence and provenance;
- unanswered critical fields;
- suggested next question with rationale;
- eligible unit list and proposed response;
- policy-based escalation prompt.

It may not silently alter evidence, suppress a caller, autonomously cancel help, invent instructions, predict criminality, or optimize primarily for throughput.

## Standards alignment target

CARE is a research overlay, not a replacement for emergency infrastructure. It must align with the National 911 Program’s NG911 system-of-systems direction, NENA i3 interfaces and data conventions, agency procedures, accessibility law, records law, labor obligations, privacy requirements, and cybersecurity controls.

Primary references:

- [National 911 Program: Next Generation 911](https://www.911.gov/issues/ng911)
- [NG911 Roadmap](https://www.911.gov/projects/ng911-roadmap)
- [911 and FirstNet](https://www.911.gov/issues/911-and-firstnet)
- [NENA standards](https://www.nena.org/page/standards)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST Cybersecurity Framework 2.0](https://www.nist.gov/cyberframework)
- [NIST Privacy Framework](https://www.nist.gov/privacy-framework)
