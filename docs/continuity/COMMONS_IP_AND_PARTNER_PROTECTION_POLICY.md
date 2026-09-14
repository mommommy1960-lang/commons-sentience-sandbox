# Commons Initiative — IP, Partnership, and Anti-Capture Protection Policy

**Status:** public operating policy and diligence checklist.  
**Owner / principal author:** Mya P. Brown.  
**Purpose:** reduce preventable loss of ownership, leverage, attribution, confidentiality, or control when The Commons Initiative publishes research, accepts contributions, speaks with partners, hires contractors, or evaluates licensing/manufacturing opportunities.

> This policy is operational risk control, not a substitute for advice from a licensed attorney in a specific transaction.

## 1. Foundational rule

Public visibility is not surrender of ownership.

A public GitHub repository may be viewed and forked through GitHub as permitted by GitHub's Terms of Service. Additional reuse rights come only from the repository's applicable license. If no separate license grants reuse rights, default copyright law generally reserves reproduction, distribution, and derivative-work rights to the copyright owner, subject to applicable law and GitHub's platform terms.

Nothing in this policy retroactively revokes rights already granted under a repository license or third-party license. When an existing repository license grants broader rights, that license controls for the covered version/material.

## 2. Public / confidential boundary

### PUBLIC — may be placed in public repositories
- high-level architecture;
- evidence-bounded test results;
- published papers and public provenance records;
- non-confidential interface specifications;
- public governance principles;
- code expressly approved for public release under the repository's stated license.

### CONTROLLED — do not publish by default
- unfiled patent-critical implementation details;
- manufacturing tolerances, process recipes, private BOM pricing, supplier terms;
- credentials, keys, private endpoints, personal identifiers;
- unpublished source material intended for licensing negotiations;
- proprietary datasets or partner confidential information;
- deal terms, unpublished financial information, private reviewer identities unless consented.

Before a new technical disclosure, ask: **Does this disclosure destroy secrecy or patent options?** If yes or uncertain, pause publication until the protection path is chosen.

## 3. Patent / disclosure gate

Public disclosure can start a United States patent grace-period clock and can destroy patent rights in many foreign jurisdictions. Therefore:

1. identify potentially patentable subject matter before public release;
2. preserve dated invention records and contributor/inventor identity;
3. where patent protection may matter, evaluate filing before disclosure;
4. never label a person an inventor merely because they reviewed, funded, manufactured, or implemented work; inventorship follows actual contribution to claimed invention;
5. do not promise ownership percentages, patent rights, exclusivity, or co-inventorship casually in email or chat.

## 4. Trade-secret gate

Trade-secret protection depends on secrecy plus reasonable protective steps. Accordingly:

- mark controlled material `CONFIDENTIAL — COMMONS INITIATIVE`;
- disclose only on a need-to-know basis;
- use NDAs/confidentiality terms before sensitive disclosure where appropriate;
- keep sensitive implementation and commercial material out of public repositories;
- maintain access-control and disclosure logs for high-value confidential material;
- require contractors, suppliers, and collaborators to protect confidential information at least as strictly as the agreement requires.

Once information is intentionally made public, do not later pretend it remained a trade secret.

## 5. Partner / contractor / manufacturer gate

No partner, contractor, manufacturer, funder, advisor, accelerator, university, or reviewer receives ownership merely because they participate.

Before paid engineering, prototype fabrication, manufacturing, sponsored research, or substantive confidential disclosure, the written agreement must address at minimum:

### Background IP
- Commons background IP remains Commons/Mya P. Brown property;
- partner background IP remains partner property;
- no implied license beyond the defined project scope.

### Project-created IP
- ownership of commissioned CAD, schematics, firmware, PCB layouts, source files, manufacturing drawings, fixtures, documentation, data, and test artifacts must be explicit;
- preferred position for paid project-specific deliverables: assignment to The Commons Initiative upon payment, except partner pre-existing tools and general know-how;
- any license-back must be narrow, written, and non-competing unless deliberately negotiated otherwise.

### Commercial rights
- no independent manufacture, resale, white-labeling, sublicensing, franchising, distribution, training use, dataset extraction, or derivative commercialization unless expressly authorized;
- no exclusivity, right of first refusal, most-favored-nation clause, option, field restriction, territorial lock, or channel lock without deliberate written approval;
- no use of Commons names, marks, logos, founder identity, case studies, or publicity without written approval.

### Improvements / feedback
- reject clauses that automatically assign all "feedback," "improvements," "ideas," or future developments to the counterparty;
- feedback may be discussed without transferring background IP;
- improvements must be tied to defined project scope and ownership terms.

### Confidentiality
- define confidential information;
- limit permitted use to the project;
- require subcontractor flow-down;
- define return/destruction obligations;
- prevent residual-memory clauses from becoming a loophole to reuse confidential know-how.

### Tooling / manufacturing control
- identify who owns paid tooling, molds, fixtures, Gerbers, source CAD, test software, and production files;
- require access to project files needed to move manufacturing if the relationship ends;
- do not allow the supplier to hold customer-funded tooling or production data hostage through ambiguous ownership terms.

### Exit / change-of-control
- protect Commons rights if the partner is acquired, reorganized, bankrupt, or stops performing;
- avoid clauses allowing assignment of the relationship to a competitor without consent;
- preserve access to deliverables, data, tooling, and unfinished work on termination.

## 6. Contract red-flag list

Do not sign without deliberate review if language includes any of the following:

- "all right, title and interest" extending beyond defined deliverables;
- "irrevocable, perpetual, worldwide, sublicensable" rights to Commons background IP;
- broad "feedback" ownership;
- "residuals" allowing use of remembered confidential information;
- automatic ownership of improvements or derivative works;
- exclusivity or non-compete obligations;
- right of first refusal / first negotiation / option rights;
- most-favored-customer or most-favored-licensee clauses;
- broad rights to train AI/ML systems on Commons code, documents, data, or confidential material;
- publicity rights without approval;
- assignment/change-of-control rights without Commons consent;
- uncapped indemnity;
- warranties that promise experimental technology will work;
- acceptance clauses that deem work accepted through silence;
- payment terms that transfer ownership before agreed payment conditions are satisfied;
- governing-law/venue clauses creating unreasonable enforcement burden;
- unilateral amendment rights;
- audit rights broader than necessary;
- clauses allowing subcontractors without flow-down confidentiality/IP obligations.

## 7. Funding / investment gate

Money is not ownership unless an agreement grants ownership.

Before accepting investment, accelerator terms, sponsored research, or grant terms, check for:

- equity percentage and dilution;
- SAFE/note conversion mechanics;
- board/control rights;
- information rights;
- pro-rata rights;
- IP security interests or collateral;
- founder vesting/revesting;
- drag-along/tag-along provisions;
- liquidation preference;
- anti-dilution;
- exclusivity;
- grant/sponsor rights in inventions, data, publication, or commercialization;
- publication-review delays;
- government rights attached to funded research.

Do not trade permanent IP/control for a small short-term payment without understanding the long-term cost.

## 8. GitHub-specific rules

1. Every public repository must have a clear rights notice.
2. Every repository should identify its actual license, if any. Do not rely on conflicting shorthand in a README.
3. Public GitHub means others can view and fork through GitHub functionality. It does not mean "anything goes."
4. A repository license may grant rights that cannot simply be withdrawn from already distributed copies. License changes should therefore be prospective and deliberate.
5. Do not commit secrets, private keys, credentials, unpublished patent-critical material, or partner-confidential material.
6. Preserve Git history and signed/timestamped provenance where practical.
7. Treat external pull requests as rights-sensitive contributions. Contributors must have the right to submit their material; acceptance does not give them ownership of Commons background IP or create a partnership.
8. Do not merge third-party code without checking its license compatibility and attribution obligations.
9. If infringement occurs, preserve evidence before requesting takedown; GitHub DMCA procedures may require identifying infringing forks separately.
10. Repository tags such as `simulation`, `prototype`, `measured`, `verified`, and `speculative` must remain evidence labels, not marketing decorations.

## 9. Trademark / branding rule

Copyright in code or text is not trademark ownership in project names.

Until trademark strategy is completed:

- use Commons names consistently;
- keep dated public evidence of use;
- avoid claiming federal registration unless it actually exists;
- do not let partners register Commons names, logos, domains, app-store identities, social handles, or product marks in their own name;
- brand licenses, if any, must be separate and revocable on breach.

## 10. Third-party IP rule

Commons protection does not erase third-party rights.

Repositories and publications that reference third-party characters, software, datasets, media, trademarks, standards, papers, or code must preserve attribution and licensing boundaries. DC-derived creative works remain rights-sensitive and are not commercialized without a proper licensing basis.

## 11. Corporate-opportunity / acquisition rule

If a larger company proposes a pilot, partnership, acquisition, exclusive license, investment, or "strategic collaboration":

1. preserve the exact written proposal;
2. do not disclose confidential implementation details before appropriate protection;
3. ask what rights they actually need and narrow the grant to that need;
4. separate evaluation rights from production/commercial rights;
5. separate patent, copyright, trademark, data, publicity, and manufacturing rights;
6. place time, territory, field-of-use, sublicensing, and termination boundaries around any license;
7. require payment/accounting/audit terms appropriate to the deal;
8. preserve the right to continue independent research unless exclusivity is intentionally paid for;
9. do not sign away future inventions outside the defined project;
10. escalate the final contract for qualified legal review whenever economically possible.

## 12. Enforcement / evidence preservation

If suspected copying, misuse, unauthorized commercialization, or ownership dispute occurs:

- do not destroy or rewrite evidence;
- preserve repository history, releases, emails, contracts, invoices, source files, screenshots, publication timestamps, and Zenodo/DOI records;
- identify exactly what material is ours, what license covered it, what version was accessed, and what the alleged misuse is;
- distinguish copyright, patent, trademark, contract, trade secret, and unfair-competition theories rather than treating "they stole it" as one undifferentiated claim;
- use the platform's formal infringement process where appropriate;
- obtain legal counsel before threats, settlement demands, or litigation claims where possible.

## 13. Commons deal posture

The default is **collaboration without capture**.

We welcome review, funding, manufacturing, replication, distribution, and scientific criticism. None of those relationships silently convert into ownership or control. Rights are granted only when expressly stated, for a defined purpose, under terms deliberately accepted by the rights holder.

---

© 2025–2026 Mya P. Brown. All Rights Reserved except rights expressly granted under an applicable repository-specific license and third-party rights in third-party material.
