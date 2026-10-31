# Deliverable 3 — Phase 3 Disaster-Recovery Plan

<badge>PLAN ONLY — NOT AUTHORIZED FOR EXECUTION</badge>

**Purpose:** propose a controlled way to evaluate Cloudflare D1 recovery and deletion/non-resurrection behavior without touching the existing Recovery Staging database, other Maya Node environments, or Production.

## 1. Provider capability confirmation — prerequisite

Before designing a native recovery test, obtain and archive the written response to Cloudflare support case **17489131**. Confirm from current Cloudflare documentation and the provider response:

- Exact D1-native backup / point-in-time recovery feature and supported operation.
- Whether the feature is available to this account/database and any plan or eligibility prerequisites.
- Backup frequency, retention period, point-in-time granularity, and limitations.
- Restore semantics: in-place versus restore-as-new-database, supported destination, downtime/availability impact, and whether a restore changes database identity.
- How to inspect backup inventory and obtain operation/audit records.
- Provider-defined behavior for deleted rows and point-in-time selection.

Until those details are documented, native D1 recovery remains **PENDING**. Do not substitute a manual JSON export/import and describe it as PITR.

## 2. Isolation and identity controls

A future drill requires a newly created disposable recovery-test database, with a unique provider-assigned database UUID recorded in an approval record. The proposed label `maya_dr_disposable_test` is only a human-readable name, not proof of identity.

The approved record must contain:
- Account/environment designation and intended purpose.
- Provider-returned database name and UUID.
- The exact approved UUID, independently read back from Cloudflare immediately before each operation.
- Separate destination database UUID for each restore target where the provider's restore semantics require one.
- Reviewer approval, operator, date, and expiration/cleanup decision.

**Hard abort rule:** before every create, write, backup, restore, delete, migration, or cleanup operation, independently query the provider for the live target database identity and compare its UUID to the exact UUID in the signed-off review record. Abort if the UUID is missing, differs, cannot be independently obtained, the account/environment is unexpected, or the operation's source/destination is ambiguous. A SQL query that returns a configured database name is not an identity check and is insufficient.

No scripts or commands are included as executable instructions in this plan. The identity check must be implemented through a provider-supported read-only identity lookup in a future, separately reviewed runbook.

## 3. Proposed test topology

Use only newly created disposable resources:
- **Test source A:** disposable database containing a synthetic marker row before the selected backup.
- **Restore destination A:** a distinct disposable database or provider-supported isolated restore target.
- **Test source B:** a separate disposable database for the post-deletion scenario.
- **Restore destination B:** a distinct disposable database or provider-supported isolated restore target.

Never point a test at or reuse:
- `maya_recovery_staging_db` / Recovery Staging;
- `maya-node` review or notification databases;
- any Preview database;
- Production or a database containing organizational/customer/pantry data.

The proposed names above are labels only. No database is created by this document.

## 4. Test A — record present at backup time

1. After separate written approval, provision and independently verify Test source A and Restore destination A.
2. Write one uniquely identifiable synthetic marker row to Test source A. Record its value and creation time.
3. Verify the marker by read-only query.
4. Create the selected **native D1 backup/snapshot** using the provider-confirmed mechanism; record the provider operation ID and backup timestamp.
5. Restore that backup to Restore destination A using the documented isolated restore method.
6. Independently verify Restore destination A's UUID before any follow-up query or operation.
7. Read the marker from Restore destination A.

**Expected result:** the marker is present because it existed at the selected backup time.

## 5. Test B — record deleted before backup time

1. After separate approval, provision and independently verify Test source B and Restore destination B.
2. Write a different uniquely identifiable synthetic marker row. Verify it exists.
3. Delete that marker from Test source B only after re-verifying its UUID against the approved record.
4. Confirm absence with a read-only query and record the deletion time.
5. Create a **later native D1 backup/snapshot after the deletion is committed**. Record the provider operation ID and timestamp; ensure the backup's point-in-time is later than the deletion.
6. Restore that later backup to Restore destination B using the provider-confirmed isolated restore method.
7. Independently verify the destination UUID and query for the marker.

**Expected result:** the marker is absent because it was already deleted at the selected backup time.

A restore of a backup taken *before* deletion is expected to contain the marker. Its reappearance in that earlier snapshot is normal historical recovery behavior and is not, by itself, evidence of a defect or failure of deletion.

## 6. Native recovery versus manual export/import

| Method | What it can demonstrate | What it cannot establish |
|---|---|---|
| Cloudflare-native D1 backup/PITR, if confirmed and used | Provider-managed recovery semantics at the selected backup/point in time | Anything beyond the documented feature/retention/restore scope |
| Manual JSON export/import | Application-level serialization, data portability, and a manually reconstructed copy | Native D1 backup retention, transaction-log PITR, provider restore behavior, or native deletion/non-resurrection guarantees |

Report the two methods separately. Do not combine their results or label a manual import as a native restore.

## 7. Evidence and acceptance criteria

For each test retain:
- Approval record and exact source/destination UUIDs.
- Provider documentation and support confirmation.
- Read-only identity verification immediately before each operation.
- Synthetic marker creation/deletion/readback evidence.
- Backup ID, backup timestamp, restore operation ID, source point-in-time, and destination identity.
- Redacted operation logs and exact observed results.
- A chronological evidence index and reviewer sign-off.

**Test A passes** only if the selected native backup is proven to predate no marker creation and the isolated restore contains the marker.

**Test B passes** only if deletion is confirmed before the selected native backup's point-in-time and the isolated restore does not contain the marker.

A test fails or is inconclusive if timestamps/identity cannot be proven, source and destination are ambiguous, provider semantics are unknown, the restore touches a prohibited environment, or evidence is incomplete. Any mismatch or uncertainty triggers immediate abort; do not attempt a corrective write.

## 8. Abort, rollback, cleanup, and retention

Abort on any identity mismatch, missing provider evidence, unexpected environment, unapproved operation, accidental exposure of real data, or inability to isolate source and destination. Preserve logs and stop; do not improvise.

No cleanup, deletion, or rollback action is authorized by this plan. Following a future drill, retain disposable resources and evidence until a separate written cleanup decision identifies exact UUIDs and approved actions. Do not delete the existing staging records or any database as part of this work.

## 9. Command / operation inventory for future review (not executable)

- Read provider documentation and support response.
- Read-only inventory of account, environment, database names, and provider UUIDs.
- Separately approved creation of disposable source and destination databases.
- Read-only UUID verification before every state-changing operation.
- Synthetic marker write/readback.
- Provider-native backup creation and isolated restore.
- Synthetic marker deletion and post-deletion backup.
- Isolated restore and read-only presence/absence checks.
- Evidence export, redaction, review, and retention decision.

**None of these operations has been run or authorized by this plan.** A separate explicit approval must name the exact database UUIDs, operation, operator, and allowed time window before any execution.
