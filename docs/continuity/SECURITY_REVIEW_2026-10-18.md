# Civic Continuum security review — October 18, 2026 (Pacific)
Updated after publication at October 19 UTC. Status: scoped internal review and remediation completed for the checks below; whole-business security assurance remains open.

## What a complete review consists of
A review needs a defined asset list and evidence for each control, not a universal “secure” label. Organize work using NIST CSF 2.0 Govern, Identify, Protect, Detect, Respond and Recover: https://www.nist.gov/itl/smallbusinesscyber/nist-cybersecurity-framework-0 . This is our internal assessment, not NIST certification.
1. Inventory every domain, site, repository, account, device, vendor, data store and integration; identify owner, purpose, audience and data flows.
2. Verify MFA, recovery methods, sessions, members, app scopes, tokens, deployment keys and least privilege. Never publish secrets or recovery values.
3. Review code, dependency lockfiles, CI/CD, secret exposure, upload/body limits, identity isolation, consent/revocation, webhooks and payment boundaries. Test adverse cases and retest fixes.
4. Verify live TLS, DNS, runtime configuration, authorization, rate limits, input validation and storage behavior on each deployed service.
5. Map collected data, retention/deletion, sharing, encryption, IP ownership/licensing and signed collaboration terms where needed.
6. Verify audit logs, alert routing and a rehearsed incident response process.
7. Restore a real backup into an isolated environment and verify its contents; confirm recovery responsibility and achievable recovery times.
8. Record findings, severity, evidence, owner, remediation, retest and exceptions; repeat after meaningful changes.

Routine technical checks can be performed internally. Specific legal interpretations, registrations or binding contract questions may need qualified counsel. An attorney does not replace technical testing.

## Executed in this pass
- Inspected GitHub MFA, three installed Apps, five OAuth grants, account SSH/GPG keys, classic/fine-grained token inventories, visible web/mobile sessions and recent security-log categories.
- Reduced an overbroad review App to known public repositories and verified the saved scope; details remain private.
- No account personal tokens, SSH keys or GPG keys were listed. This says nothing about repository deploy keys or other providers.
- Rebuilt and published patched Maya Accountable Actions, Service Workshop and Crowned Coil, preserving their audiences and configuration.
- Updated Next, React/React DOM/RSC, Vite, image-size and applicable transitive dependency pins. Retained existing package-manager supply-chain safeguards. Used mature patched Next16.3.8 on pnpm projects and16.4.2 on the npm project.
- Final production-only audits report zero known advisory findings in all three projects. Broader audits were also run; development-chain findings remain below. Dependency labels alone do not prove what is deployed: RSC/Vinext-related code was included in remediation.
- All three final builds succeeded; regression tests passed: Maya52, Workshop72, Crown7 (131 total, not independent security certification).
- Earlier same-day Reality Audit25 and older Maya snapshot32 plus11 subtests remain scoped evidence, not rerun counts or a latest-source claim.
- Earlier Crown signup hardening remains in the final publication:8KiB stream cap, JSON/content-type/body-shape rejection; seven tests passed.
- Earlier limited tracked-source secret-pattern scan, policy entry points and branch-integrity checks remain in the same-date Bruce-to-Bruce record.

## Remaining findings and verification gates
| Area | Evidence / limitation | Required closure |
| --- | --- | --- |
| Build dependencies | Broader pnpm audits retain3 advisory entries: esbuild moderate development-server issue, esbuild low Windows development-server issue, braces high recursive-pattern DoS. npm reports14 affected dependency/package entries cascading from these families; counts are not comparable. | Keep development servers private and process only trusted build/lint inputs. Validate a compatible esbuild/toolchain upgrade rather than a blind breaking override; monitor braces upstream fix/replacement. No public user-controlled glob endpoint was found in the focused Maya app/server search; this is not proof of universal nonreachability. |
| Recovery | Source history and deployment versions exist; production database restore has not been demonstrated. | Verify provider backup retention/export and restore to an isolated target; record measured recovery. |
| Provider accounts | GitHub review is partial account evidence, not Cloudflare, Google/Gmail, Stripe, domain registrar or LinkedIn security clearance. | Authenticated settings, role/token, recovery, billing/webhook and log checks at each provider; do not repeat known authentication loops. |
| Devices and sessions | Visible GitHub session inventory reviewed; browser geography alone cannot identify an intruder. Owner's Android mobile authentication preserved. | Owner recognition of devices; device OS/update/screen-lock and recovery checks require the actual devices. |
| Access and branch enforcement | Broad recognizable OAuth grants preserved; private-vault plan enforcement limitation remains. | Confirm need for VSCode/Android/Zenodo grants before removing working access; verify repo deploy keys and enforceable private branch protections without paid/public changes by assumption. |
| Runtime detection and abuse | Unit/integration boundaries tested; production-wide rate limits, log retention and alert delivery not fully demonstrated. | Controlled non-destructive runtime probes, quota/rate-limit evidence, alert test and incident exercise. |
| Legal and IP | Public policy entry points and internal process exist; policies are not signatures or proof of title. | Reconcile creators/licenses and obtain actual agreements before confidential collaboration; counsel for specific uncertain legal conclusions. |
| Original Maya recovery | Separate OpenAI support case remains open. | Provider investigation/restoration; do not present the working demo as restored original data. |

No invasive penetration test, actual purchase, customer-data export, credential rotation, contract signature or recovery-code disclosure performed. No evidence here proves that a compromise did or did not occur.

## Closure rule
A finding is closed only after the change and a meaningful retest are evidenced. “Not tested,” “not accessible,” and “upstream unresolved” remain visible states. Never advertise whole-business security certification or a guarantee against every harm.
