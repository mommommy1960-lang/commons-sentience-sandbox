# CARE threat and failure register

| Hazard | Consequence | Required control | Evidence gate |
|---|---|---|---|
| Transcription error | Wrong location/event | Original audio, alternatives, human confirmation | Stratified word/error and field accuracy |
| Translation error | Lost clinical or hazard detail | Certified evaluation and source-language display | Bilingual scenario review |
| Automation bias | Human accepts wrong suggestion | Evidence links, friction on low confidence, training | Controlled human-factors trial |
| Emotional-presentation bias | Distressed caller discounted | Prohibit demeanor scoring; outcome audits | Disparate-error analysis |
| False positive | Unneeded or harmful dispatch | Separate pre-alert from dispatch; policy gates | False-dispatch rate |
| False negative | Delayed/missed help | Conservative escalation and human monitoring | Missed-critical-event rate |
| Location spoofing | Resources sent incorrectly | Multi-source location and discrepancy alarm | Adversarial location tests |
| Prompt injection in message/media | Model changes policy or leaks data | Treat all caller content as untrusted data | Red-team suite |
| Surveillance expansion | Secondary use chills help-seeking | Purpose limitation and retention deletion | Privacy impact assessment |
| Outage/vendor loss | Calls cannot be handled | Bypass to ordinary procedures | Failover drill |
| Model update drift | Previously tested behavior changes | Version pinning and revalidation | Regression suite |
| Unauthorized dispatch | Unaccountable state action | Strong identity, role controls, signed events | Access-control penetration test |

## Stop-ship conditions

- CARE delays any ordinary path to a human telecommunicator.
- Performance is materially worse for a protected or accessibility-relevant
  group and no safe mitigation is validated.
- The system cannot show the source for a dispatch-relevant assertion.
- Operators cannot reject or correct recommendations quickly.
- A model can issue or cancel dispatch outside approved authority.
- Failover, audit, privacy, or incident response is absent.

