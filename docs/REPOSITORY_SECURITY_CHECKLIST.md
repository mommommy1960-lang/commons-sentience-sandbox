# Repository security checklist

## Current controls

- Work remains on the feature branch; `main` is not changed by the repair loop.
- CI uses read-only repository contents permission.
- CI checkout uses the repository-provided token and does not add third-party actions.
- The demonstrator uses synthetic data and has no external side effects.
- No credentials or private reports belong in the repository.

## Owner actions

1. Enable two-factor authentication on the GitHub account.
2. Review installed GitHub Apps and remove anything unrecognized.
3. Use least-privilege repository access; do not grant broad access to unknown apps.
4. Review repository collaborators, outside collaborators, deploy keys, and personal access tokens.
5. Rotate any credential that may have appeared in chat, screenshots, commits, or logs.
6. Keep `main` protected with required CI and review before merging.
7. Do not place API keys in workflow files, issues, comments, or documents.
8. Use synthetic or redacted data for demonstrations and reviewer testing.
9. Preserve release commit SHAs and CI evidence before public announcements.
10. Treat unsolicited bot comments requesting `OPENAI_API_KEY` or other secrets as untrusted; do not add secrets in response.

## Disclosure rule

Before sharing with a reviewer, provide only the demo link and reviewer handout. Do not provide write access. A reviewer should not need repository credentials, private data, or a personal access token.

## Incident response

If an account, token, or repository is suspected compromised:

- stop sharing links temporarily;
- revoke or rotate the affected credential;
- inspect recent commits, workflow runs, collaborators, and installed apps;
- preserve evidence;
- restore from a known-good commit only after review;
- do not force-push or delete evidence.
