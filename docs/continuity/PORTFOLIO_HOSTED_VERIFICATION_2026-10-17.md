# Public hosted portfolio verification — October 17, 2026

The [GitHub-hosted public source run](https://github.com/mommommy1960-lang/commons-sentience-sandbox/actions/runs/39070612103) completed successfully. Its job log confirms **262 passing tests** across six pinned public repositories, excluding additional pytest subtests.

| Repository | Passing tests |
|---|---:|
| sage-situated-companion | 136 |
| CERL-Preemptive | 23 |
| Commons-Unified-Protocol | 11 |
| aurora-sovereign-core | 47 |
| commons-sentience-sandbox | 32 |
| maya-node | 13 |

The public source suite excludes the private web implementation (44 local tests) and private workbench (18 local tests). Combined local source/web verification remains 324 tests; the separately deployed web workshop passed 40 hosted runtime/storage checks. Do not add these overlapping counts together as if they were unique tests.

The [public evidence artifact](https://github.com/mommommy1960-lang/commons-sentience-sandbox/actions/runs/39070612103/artifacts/12114503118) contains logs, JUnit, structured results and a summary; its retention is 30 days. Artifact SHA-256: `89da22647715e8d8559078e449a4acd89dafd137ef6627a5d65b4b4c219a6a0d`. This permanent [structured observation](PORTFOLIO_HOSTED_VERIFICATION_2026-10-17.json) retains the verified counts and scope after artifact expiry. The reproducible runner pins each source commit in `tools/verify_public_portfolio.py`.

This does not resolve the separate private repository runner failure, establish live AI or payment delivery, or substitute for independent customer/Android acceptance. See [software service progress and links](PORTFOLIO_WEB_SERVICES_2026-10-17.md).
