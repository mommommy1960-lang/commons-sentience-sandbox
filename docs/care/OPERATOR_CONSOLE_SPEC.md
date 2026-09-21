# CARE operator console specification v0.1

## One-screen incident card

The screen must favor confirmation over re-interviewing. It shows:

| Panel | Required contents |
|---|---|
| Location | dispatchable address, map, source, timestamp, uncertainty radius, conflict/spoof warning |
| What happened | incident hypotheses, confidence, quoted/source-linked evidence, contradictions |
| People | count, injuries, mobility/access needs, caller-reported descriptions; no identity guess from appearance |
| Hazards | fire, weapon, traffic, chemical, structural, medical, animal, weather, responder-safety evidence |
| Communications | live transcript, translation, audio replay, open-line/silent/disconnected status |
| Resources | several eligible units, ETA, capability, jurisdiction, availability, mutual-aid basis |
| Actions | take over, ask, correct, confirm, pre-alert if permitted, dispatch, escalate, cancel recommendation |
| Audit | model/version, policy/version, operator edits, timestamps, final authority |

## Interaction rules

- Never hide the original call behind a summary.
- Highlight uncertainty instead of filling blanks.
- Require the fewest high-value confirmations.
- Provide one-action human takeover.
- Never make “calm down” a prerequisite for aid.
- Do not use protected traits, neighborhood proxies, caller emotion, or perceived social worth to prioritize.
- A model-suggested description remains caller-reported or inferred until a human confirms it.
- Escalation labels such as terrorism require policy-defined evidence and human confirmation.
- If the console fails, the ordinary call-handling interface remains usable.

## Example handoff

> Possible shooting. Location candidate: 100 Example Ave, entrance B (device location; 18 m uncertainty). Caller reports being shot and wearing a green shirt. One adult voice; heavy distress; call remains connected. Weapon location unknown. Two EMS-capable and three law-enforcement units are eligible. Fastest policy-compliant pair: Medic 4 (ETA 4:10) and Unit 12 (ETA 3:35). Confirm/correct/authorize.

This is a design example, not a validated clinical or dispatch protocol.
