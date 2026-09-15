# Commons IP Red-Team & Defense Standard

Status: operational policy; not legal advice.
Owner: Mya P. Brown / applicable rights holders.

## Purpose
This document converts the Commons portfolio's IP posture into an adversarial checklist. It does not claim that any legal protection is impenetrable. Its purpose is to expose failure modes before disclosure, contracting, licensing, manufacturing, funding, publication, or collaboration.

## Threat model
Before any material disclosure or agreement, assume a sophisticated counterparty may lawfully try to obtain maximum rights at minimum cost. Test for:

1. IP assignment hidden in services, accelerator, contest, grant, platform, publishing, manufacturing, or evaluation terms.
2. Work-made-for-hire language or present-tense assignment of future inventions.
3. Broad licenses to submissions, feedback, improvements, derivatives, data, models, outputs, or documentation.
4. Residual-knowledge clauses allowing personnel to reuse remembered confidential information.
5. No-confidentiality or unsolicited-submission clauses.
6. Sublicensable, transferable, perpetual, irrevocable, worldwide, royalty-free licenses broader than the transaction requires.
7. Exclusivity, right of first refusal, right of first negotiation, most-favored terms, option rights, or field-of-use restrictions.
8. Joint-IP defaults that create deadlock or allow independent exploitation.
9. Background-IP definitions that accidentally sweep preexisting Commons technology into project IP.
10. Improvement clauses that transfer later inventions or adjacent research.
11. Contractor/subcontractor ownership gaps.
12. Tooling, CAD, firmware, source-code, model-weight, dataset, test-data, fixture, and manufacturing-file ownership ambiguity.
13. Patent-publication traps, including disclosure before filing.
14. Trade-secret destruction through unnecessary public disclosure.
15. Open-source or third-party license contamination and incompatible obligations.
16. Trademark/name/domain capture.
17. AI training, model improvement, benchmarking, retention, or dataset reuse of confidential submissions.
18. Data telemetry, logging, retention, cross-border transfer, or security terms broader than necessary.
19. Reverse engineering or benchmarking permissions where contractually restrictable.
20. Change-of-control clauses that transfer rights to an acquirer or competitor.
21. Bankruptcy/insolvency provisions affecting licenses or escrow.
22. Indemnity, warranty, liability, insurance, or audit provisions disproportionate to a small entity.
23. Publication/press rights that reveal patent-sensitive or confidential material.
24. Grant/funder terms that impose government, university, sponsor, march-in, data-sharing, publication, or commercialization rights.
25. Repository/platform terms that differ from the project's intended license.
26. Inconsistent license files, headers, READMEs, product terms, or historical releases.
27. Apparent-authority problems: no collaborator, assistant, contractor, reviewer, or manufacturer may grant rights without actual written authority.
28. Signature traps: clickwrap, portal upload, purchase order, statement of work, invoice, email acceptance, or API/platform action may form contractual obligations.

## Mandatory disclosure gate
Classify information before sharing:

- PUBLIC: intentionally disclosed and safe for public release.
- CONTROLLED: non-secret diligence material shared only for a defined purpose.
- CONFIDENTIAL: NDA/contract gate required.
- PATENT-SENSITIVE: do not publicly disclose until patent strategy is reviewed.
- TRADE-SECRET: need-to-know only; access, copies, recipients, purpose, and return/destruction tracked.
- THIRD-PARTY: disclose only within the rights actually held.

If classification is uncertain, default to the more restrictive class until reviewed.

## Contract minimums
For counterparties receiving non-public Commons material, seek terms that:

- identify Commons background IP and reserve all ungranted rights;
- define the permitted purpose narrowly;
- grant no implied license;
- prohibit unauthorized copying, distribution, commercialization, model training, or sublicensing;
- limit access to personnel/subcontractors with equivalent duties;
- require reasonable security and incident notice;
- define project-created IP before work begins;
- define ownership of source, CAD, tooling, fixtures, test data, documentation, and improvements;
- require return/deletion or archival restrictions when the engagement ends;
- survive termination for confidentiality, ownership, payment, audit evidence, and accrued rights as appropriate;
- prohibit publicity/use of name or marks without written permission;
- require written authorization for any expanded scope.

Do not assume an NDA solves ownership. NDA, IP ownership, license scope, patent rights, trade secrets, data rights, and commercial terms are separate questions.

## GitHub/repository controls
Public Git history is useful provenance but is not a substitute for copyright registration, patent protection, trademark protection, trade-secret controls, or contracts.

For each repository:
- inventory LICENSE files, headers, README rights notices, third-party dependencies, and historical releases;
- never claim a later restrictive notice retroactively cancels rights already granted under an earlier license;
- separate public reference implementations from non-public crown-jewel implementation details where appropriate;
- do not commit credentials, personal data, private keys, unpublished patent-sensitive details, or trade secrets;
- require review for changes to license, legal, ownership, patent, disclosure, release, and security-sensitive files;
- enable branch/ruleset protections where available and appropriate; current protection must be verified rather than assumed;
- preserve release tags/commits and evidence of authorship/provenance.

## DC-derived books and other third-party-IP works
The Commons protection strategy cannot manufacture rights in third-party characters or settings. For DC-derived manuscripts:
- preserve dated originals and version history;
- distinguish Mya P. Brown's original expression from preexisting DC-owned material;
- do not send manuscripts through unsolicited-submission channels;
- disclose only a minimal licensing inquiry until an authorized route and acceptable terms exist;
- do not represent the books as authorized, official, or commercially cleared before written permission/license exists;
- if registration is pursued, accurately exclude preexisting third-party material and claim only eligible new authorship;
- retain every rights inquiry, response, agreement, and version sent.

## Red-team cadence
A '1,000 iteration' claim is not meaningful if it merely repeats the same checklist. Use attack classes instead:
1. ownership attack;
2. licensing attack;
3. disclosure attack;
4. patent attack;
5. trade-secret attack;
6. contractor/manufacturer attack;
7. investor/acquirer attack;
8. platform/cloud/AI attack;
9. open-source dependency attack;
10. third-party-IP attack;
11. evidence/provenance attack;
12. governance/authority attack;
13. security/credential attack;
14. publication/marketing attack;
15. insolvency/change-of-control attack.

A defense passes only when the relevant document, technical control, filing, or contract actually exists. Aspirational language is recorded as OPEN, not PASS.

## Current known critical gaps
- CERL terminology/permissions are inconsistent across parts of the portfolio and require prospective reconciliation.
- Public repositories can establish provenance but cannot keep disclosed information secret.
- Copyright does not protect underlying ideas, systems, methods, algorithms, or inventions; other protection may be required.
- Patent-sensitive disclosures require jurisdiction-specific review.
- Trade-secret protection requires actual secrecy measures, not a notice pasted onto public material.
- DC-derived books require permission/licensing for third-party protected material; Commons notices cannot override DC's rights.
- Repository branch/ruleset protection must be configured and verified; it must not be assumed merely because legal notices exist.

## Stop conditions
Do not sign, upload, submit, publish, manufacture, provide source/CAD, or accept money tied to unfamiliar terms when any of these appear unresolved: ownership transfer; broad license; confidentiality waiver; patent-sensitive disclosure; exclusivity; future-IP/improvements rights; AI-training rights; third-party-IP uncertainty; sublicensing; change of control; personal guarantee; disproportionate indemnity; or inconsistent governing documents.

The correct response to an unresolved stop condition is not panic and not bluffing. It is: preserve evidence, limit disclosure, identify the exact clause, obtain clarification/amendment, and obtain qualified counsel where the stakes justify it.
