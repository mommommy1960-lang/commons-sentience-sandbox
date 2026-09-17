# Civic Continuum repository plan

## Existing repositories

Continue using the existing repositories where the code already lives:

- `commons-sentience-sandbox`: shared experimental and demonstrator work.
- `maya-node`: consent-and-control review service.
- `sage-situated-companion`: companion-related work.
- `commons-companion-vessel-1`: companion vessel work.
- `aurora-sovereign-core`: Aurora and governance experiments.
- `flux-drive-kernel`: Flux Drive research code.
- `mya-mprs-system`: MPRS research.
- `CERL-Preemptive`: licensing and governance experiments.
- `Commons-Unified-Protocol`: protocol work.
- `commons-master-tech-compendium`: archival compendium.

## Recommended dedicated repositories

Create these only when the account owner is ready to do so and the repository name is confirmed:

- `civic-continuum-governance`
- `civic-continuum-academy`
- `civic-continuum-housing-ledger`
- `civic-continuum-care-rescue`
- `crowned-coil`
- `cask-and-crunch`
- `civic-continuum-publishing`

The connected GitHub integration can document and modify repositories it can access, but it does not expose repository-creation authority in this workflow. Do not imply that a repository exists until the account owner creates it and it is verified.

## Minimum repository contents

Every active product repository should contain:

- README with scope and status;
- LICENSE or rights notice chosen by the owner;
- claim-boundary statement;
- threat model or hazard analysis;
- data and privacy statement;
- reproducible setup instructions;
- tests and test instructions;
- decision log;
- issue templates for bug, safety, evidence, and rights concerns;
- release checklist;
- changelog;
- and a clear statement of what is not implemented.

## Branch and merge rule

Work on feature branches. Open draft pull requests. Keep `main` untouched until the user reviews the diff, the checks pass, and the user explicitly approves merging.

## First issues to open

1. Repair offline test execution in `commons-sentience-sandbox`.
2. Remove or document the `OPENAI_API_KEY` dependency for tests that should not call external services.
3. Add the source register for the Companion and Maya Node claims.
4. Add a product-status page that distinguishes scaffold, prototype, pilot, and released.
5. Add the Crowned Coil requirements and animal-safety checklist.
6. Add the rights-cleared publishing queue.
