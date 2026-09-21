# CARE validation plan

## The first falsifiable question

Does CARE reduce time to a correct, policy-compliant incident card without
increasing missed critical events, inappropriate dispatch, disparate error,
privacy exposure, or operator over-reliance?

## Stages

| Gate | Environment | Required result |
|---|---|---|
| CE-0 | Static schemas and threat model | Independent standards review |
| CE-1 | Synthetic text scenarios | Reproducible extraction and uncertainty metrics |
| CE-2 | Consented simulated calls | Accuracy by language/acoustic/distress strata |
| CE-3 | Trained-operator tabletop | Faster correct routing without unsafe reliance |
| CE-4 | Shadow mode; no dispatch connection | Prospective comparison to real outcomes under approval |
| CE-5 | Limited pilot | Independent oversight, incident reporting, immediate rollback |

## Primary metrics

- time to verified location;
- time to verified incident type;
- critical-field precision and recall;
- missed-critical-event rate;
- false/inappropriate pre-alert and dispatch rate;
- operator correction rate and correction time;
- calibration error for confidence scores;
- performance gaps between predefined strata;
- privacy incidents and unauthorized accesses;
- failover success and recovery time.

Accuracy averaged across all calls is not sufficient. Safety-critical misses and
group-specific error must be reported separately.

## Experimental discipline

- preregister scenarios, primary metrics, thresholds, and exclusion rules;
- freeze model and prompt versions before each evaluation;
- keep training, tuning, and final evaluation sets separate;
- include ordinary baseline handling and a non-AI structured form comparator;
- blind outcome adjudicators when practicable;
- publish null, adverse, and stopped results;
- never connect the research simulator to live dispatch.

