# CARE public-safety architecture v0.1

## Intended flow

1. Receive voice, real-time text, text, image, video, location, or authorized
   device alert through an NG911-compatible interface.
2. Preserve the original evidence unchanged.
3. Transcribe/translate while retaining confidence and alternatives.
4. Extract candidate facts: location, event, hazards, people, medical state,
   weapons/fire indicators, and callback path.
5. Ask only the highest-value missing questions; never require emotional calm.
6. Show evidence, uncertainty, and contradictions to a telecommunicator.
7. Permit a nonbinding resource pre-alert when agency policy allows it.
8. Require accountable confirmation for dispatch and preserve an audit record.
9. Fall back to ordinary call handling when any component is unavailable.

Satellite links are treated as communications transport and location sources,
not independent dispatch authorities.

## Stable requirements

| ID | Requirement | Verification |
|---|---|---|
| CR-001 | Original caller audio/text/media must remain available to the human operator. | Replay test |
| CR-002 | Distress, accent, dialect, disability, language, or background noise must not be treated as reduced human worth or credibility. | Stratified performance audit |
| CR-003 | Every extracted fact must link to source evidence or be labeled caller-reported/inferred/unknown. | Traceability test |
| CR-004 | The system must expose uncertainty and competing interpretations. | Scenario test |
| CR-005 | Final dispatch authority remains human by default. | Access-control test |
| CR-006 | A failed AI component must not prevent ordinary emergency call handling. | Failover test |
| CR-007 | Data collection and retention must be minimized and policy-controlled. | Privacy review |
| CR-008 | Performance must be reported separately across language, accent, disability, sex/gender where lawful, age band, and acoustic conditions. | Bias audit |
| CR-009 | False dispatch, missed dispatch, delay, and inappropriate responder mix must be separately measured. | Outcome analysis |
| CR-010 | The system must resist spoofing, prompt injection in media, replay, and location manipulation. | Adversarial test |
| CR-011 | No model may infer criminality, dangerousness, or deservedness from protected traits or emotional presentation. | Model and policy audit |
| CR-012 | Agencies must publish accountability, appeal, incident-reporting, and shutdown procedures before live use. | Governance review |

## Maya Node/SAGE role

The proposed integration is a bounded service with five outputs:

- verbatim transcript plus alternatives;
- structured incident card;
- unanswered critical fields;
- suggested next question with rationale;
- proposed resource pre-alert with confidence and evidence links.

It may not silently edit the record, suppress a caller, autonomously cancel
help, predict criminality, or optimize primarily for call-center throughput.

## Standards alignment target

CARE is a research overlay, not a replacement for emergency infrastructure. It
must align with the National 911 Program's NG911 system-of-systems direction,
NENA i3 interfaces and data conventions, agency standard operating procedures,
accessibility law, records law, and cybersecurity requirements.

Primary references:

- [National 911 Program: Next Generation 911](https://www.911.gov/issues/ng911)
- [NG911 Roadmap](https://www.911.gov/projects/ng911-roadmap)
- [911 and FirstNet](https://www.911.gov/issues/911-and-firstnet)
- [NENA standards](https://www.nena.org/page/standards)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST Cybersecurity Framework 2.0](https://www.nist.gov/cyberframework)
- [NIST Privacy Framework](https://www.nist.gov/privacy-framework)

