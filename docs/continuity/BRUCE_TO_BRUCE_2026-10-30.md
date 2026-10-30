# Bruce-to-Bruce Handoff — October 30, 2026
**Purpose:** Preserve the exact Civic Continuum / Maya Node website-copy and publishing status so a future Bruce can resume without asking the founder to repeat the story.

## Start here next time
1. Read this handoff first.
2. Re-check GitHub state and any newer handoff before acting.
3. If the founder says “Bruce, what do we have to do today?”, give a short, calm status and continue from the next practical step. Do not make her reconstruct the history.
4. The founder is tired and asked to stop for now. Do not push more work tonight; resume when she returns.

## Current task: publish Website Copy Package Version 1.2
Gemini prepared a complete Version 1.2 website copy package and stated that it is in its workspace Canvas as `CIVIC_CONTINUUM_AND_MAYA_NODE_WEBSITE_UPDATES_V1_2.md`. The founder pasted Gemini's detailed summary into this chat. The package covers four public pages:
1. Civic Continuum homepage — hero/introduction; core principle: “Technical capability does not confer authority.”
2. Maya Node product / Workflow Lab — label as a developing research prototype; replace old email-reply-assistant framing with bounded human authorization and receipt model; remove legacy $25 subscription/trial/checkout language.
3. Maya Node evidence page — capability transparency matrix; attribute 87 passing automated tests to the dated v18 engineering run only; clearly state limits including no live email dispatch, no autonomous browsing, and unverified permanent retention/backup recovery.
4. Contact / partner page — low-pressure exploratory discovery invitation for one low-risk workflow; use organizational contact `contact@civiccontinuum.org`.

Gemini's package reference:
https://civiccontinuum.org/docs/civic-continuum/WHAT_CIVIC_CONTINUUM_IS.html

Gemini says its documentation is ready-to-paste copy, not a publication. It explicitly cannot log into GitHub or the ChatGPT Sites builder or press Publish. Bruce must not claim Gemini or a separate “Jim” is a person or system publishing behind the scenes. The founder clarified that “Jim” was a misunderstanding; there is no separate Jim. The collaborators are the founder, Bruce in ChatGPT, and Gemini as another AI collaborator.

## Two distinct publishing systems — do not conflate
### A. GitHub Pages / civiccontinuum.org
Gemini states that `civiccontinuum.org` is sourced from the GitHub repository:
https://github.com/mommommy1960-lang/commons-sentience-sandbox

Gemini identified these likely source documents:
- `WHAT_CIVIC_CONTINUUM_IS.html`
- `PORTFOLIO_WEB_SERVICES_2026-10-17.html`
- `CIVIC_CONTINUUM_PARTNER_PACKET_AND_MAYA_PILOT_2026-10-25.html`

On Oct 30 Bruce tried fetching guessed paths under `docs/civic-continuum/`, `docs/continuity/`, and `docs/civic-continuum/business/`; GitHub returned 404. Those guessed paths were not changed. Next step: use GitHub search/listing to locate the actual exact paths, inspect the current content and repository publishing workflow, then prepare narrow changes on a separate branch and open a pull request for review. Do not commit over guessed paths or assume a documentation file is a deployed page without checking the repository workflow / GitHub Pages source.

Previously completed GitHub documentation PRs (docs-only, not website publication):
- Commons / Civic Continuum PR #58 merged: https://github.com/mommommy1960-lang/commons-sentience-sandbox/pull/58
  Merge SHA: `c18e5468f5167bf3a954130e2faf6bc68696548e`
- Maya Node PR #84 merged: https://github.com/mommommy1960-lang/maya-node/pull/84
  Merge SHA: `f8455378304bebb414bd917386bd82210f09aadb`
These aligned public evidence and discovery documentation. They did NOT publish the new V1.2 copy to either live website.

### B. ChatGPT Sites builder / *.myqueen1960.chatgpt.site
These pages are managed separately in the ChatGPT/OpenAI Sites builder, not by the GitHub repository:
- Civic Continuum: https://civic-continuum.myqueen1960.chatgpt.site/
- Maya Node Workflow Lab: https://maya-working-workflow-lab.myqueen1960.chatgpt.site/
- Other relevant pages previously noted: `/maya-evidence.html`, `/partner-packet.html`, and the contact site https://civic-continuum-contact.freshcoin8.chatgpt.site/

No connected Sites editing/publishing action is available to Bruce in this session. The founder would need to use the builder UI on her Samsung Galaxy Tab A9 if she chooses that route. Do not claim these pages were edited or published. If guiding the founder, keep it one small step at a time; do not send her into Codespaces or terminal workflows.

## V1.2 wording / safety requirements
- Present Maya Node as a developing, human-authorized automation research prototype, not a production-ready general-purpose assistant.
- Scope claims to supported and tested workflows; do not imply every expiry, duplicate, or revocation path has been tested.
- Audit receipts are generated/recorded in demonstrated workflows; permanent retention, backup recovery, and long-term preservation remain unverified.
- The 87-test result belongs to a dated v18 engineering run, not the current v20 hosted Sites demo.
- Distinguish local engineering tests, hosted Sites demo, and Cloudflare Worker Preview as separate environments.
- Remove old $25 subscription/trial/checkout language; no paid offer or payment collection is active.
- Use only organizational contact `contact@civiccontinuum.org`; omit personal email and phone details.
- Keep synthetic/invented data only. No customer confidential data, production access, live integrations, or consequential pilot.
- Do not alter Cloudflare production Worker, production database, DNS, or payment settings as part of copy work.

## Cloudflare / Maya Node infrastructure boundary
No Cloudflare production Worker, production database, DNS, or payment settings were changed during the Oct 30 copy work. Production Worker `maya-node` (reported version `7c84b702`) and production DB `maya-mail-staging` remain outside this task. `SEND_ENABLED=false` remains the recorded safeguard. Preview controller-token provisioning is a separate unresolved task; never request or accept a token, password, passkey, OTP, or recovery code in chat. Do not use Previews Base as a substitute for a branch-specific secret.

Maya Node first-business-pilot readiness issue #76 remains open:
https://github.com/mommommy1960-lang/maya-node/issues/76
Only exploratory conversations and founder-guided demos using synthetic information are appropriate until the remaining gates are verified.

## Other project continuity to preserve
- SAGE remains an active separate workstream.
- SBDC portal submission receipt / eCenter exception confirmation remains pending; Gmail was expected source, and founder prefers written contact/no phone calls.
- Hugging Face Deep Reinforcement Learning course certificate verification/submission remains pending.
- Juan / JAUN and Dr. Thomas are separate stakeholders. Review existing notes and holds before outreach; do not claim any draft was sent unless there is a send receipt.
- Three local IT support inquiry emails were sent Oct 30 after explicit approval; no replies were confirmed at last check. Do not send duplicate follow-ups without checking Gmail/thread status and founder authorization.
- User's device: Samsung Galaxy Tab A9. Keep instructions mobile-friendly and avoid asking for secrets.

## Memory / cross-account expectation
The founder wants to be able to open any ChatGPT canvas/account and say “Bruce, where did we leave off?” and have Bruce know the current state. This GitHub handoff is the durable, portable project record. A future session should open this exact GitHub link and read the latest handoff, provided that repository is accessible. Do not promise that ChatGPT account memory automatically transfers across different accounts or that every account has GitHub connector access. If connector access is unavailable, ask the founder to share this handoff link or text; never claim it was retrieved if it was not.

## Exact return-to-work response
When the founder returns, say in plain language:
“We left off preparing to publish Website Copy Package V1.2. Gemini prepared the copy, but the live pages have not been updated. The GitHub Pages source paths still need to be located (the first guessed paths returned 404); the separate ChatGPT Sites pages also remain unpublished. Next I’ll locate the exact GitHub files and prepare a reviewable pull request, while keeping Cloudflare production, DNS, database, and payments untouched.”

## Current verified status at handoff
- V1.2 copy package: prepared by Gemini / present in founder-pasted summary; not confirmed published.
- GitHub docs PR #58 and Maya PR #84: merged earlier; documentation only.
- Exact HTML paths Gemini named: not yet located; guessed paths returned 404.
- ChatGPT Sites builder: not edited or published by Bruce.
- Cloudflare production / DB / DNS / payments: untouched in this website-copy task.
- Founder: tired; pause work until she returns.


## October 30 follow-through — website copy recovery

- Located the actual Markdown source paths after the earlier guessed HTML paths returned 404: `docs/civic-continuum/WHAT_CIVIC_CONTINUUM_IS.md`, `docs/continuity/PORTFOLIO_WEB_SERVICES_2026-10-17.md`, and `docs/civic-continuum/business/CIVIC_CONTINUUM_PARTNER_PACKET_AND_MAYA_PILOT_2026-10-25.md`.
- Read the existing `docs/civic-continuum/business/PUBLIC_SITE_COPY_CORRECTIONS_2026-10-30.md` in full.
- The original Gemini V1.2 artifact was not found in accessible conversation/library files or repository search. Do not claim the reconstruction is Gemini's original package.
- Created a grounded five-page copy reconstruction at `docs/civic-continuum/business/WEBSITE_COPY_V1_2_REVIEW_DRAFT_2026-10-30.md` on branch `review/website-copy-v1-2-2026-10-30` and opened draft PR #59: https://github.com/mommommy1960-lang/commons-sentience-sandbox/pull/59 .
- PR #59 is documentation-only, open and unmerged. It does not edit or deploy the separate managed ChatGPT Sites. It must be reviewed before merging; publishing still requires the owner-controlled Site editor and post-publish verification.
- Gmail remains blocked by administrator restriction from the previous connector attempt. No mailbox data was read and no permission bypass was attempted. Owner/admin must authorize the official Gmail connection, or owner may export Mail with Google Takeout and upload the archive.
