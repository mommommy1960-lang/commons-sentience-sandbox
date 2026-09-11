# Reality Audit Product Threat Model v0.1

## Protected decision

The engine protects the boundary between “interesting output” and “claim eligible
for external review.” It does not autonomously authorize discovery language.

## Attacks addressed in v0.1

- changed or missing evidence artifact;
- wrong expected artifact digest;
- invalid or missing provenance gate;
- null result relabeled as a surviving candidate;
- candidate promoted despite a missing required gate;
- malformed evidence bundle supplied to the verifier;
- post-compilation bundle-field tampering;
- post-compilation artifact tampering;
- concealed limitations or failed-gate list;
- severed continuity between claim, evidence and decision.

## Explicitly not yet solved

- creator identity and nonrepudiation: SHA-256 integrity is not a signature;
- trusted timestamping;
- compromised host or malicious compiler;
- key management and revocation;
- remote artifact durability;
- independent witness signatures;
- semantic truth of evidence supplied by a dishonest operator;
- legal/regulatory certification;
- freedom to operate against third-party patent claims.

## Competitive principle

The moat is not an unchallengeable slogan. It is accumulated verified failure-mode
coverage, domain adapters, review practice, evidence history, and customer trust.
Every claim about the product must itself be capable of entering Reality Audit.
