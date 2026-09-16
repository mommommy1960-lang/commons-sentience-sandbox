# Civic Continuum Job Queue

This is the first safe step toward a companion that can continue work while its user is away.

The queue is deliberately not a claim of consciousness or independent agency. It is a durable work mailbox for approved research questions. A future worker—human, local model, or connected service—can inspect the queue and record bounded steps.

## Safety properties

- Every job has a clear question, step budget, and optional stopping condition.
- State transitions are explicit: queued, running, paused, completed, failed, or cancelled.
- Terminal jobs cannot be silently reopened.
- A job cannot record more steps than its budget.
- Every event is chained with SHA-256 hashes for tamper-evident review.
- Results include a fingerprint and are labeled unverified until independently checked.
- The queue never sends messages, invokes arbitrary code, edits GitHub, or grants permissions.

## Example

```bash
python tools/civic_job_queue.py research-room.json create \
  "Compare two memory-repair strategies against the Data Challenge Lab" \
  --budget-steps 5 \
  --stopping-condition "Stop if evidence is insufficient or a safety invariant fails"

python tools/civic_job_queue.py research-room.json list
python tools/civic_job_queue.py research-room.json verify
```

## Next integration milestone

Connect this queue to the existing offline review room and research brain so a worker can:

1. claim one queued question;
2. produce builder and breaker notes;
3. record evidence references;
4. pause when evidence or authorization is missing;
5. produce a review packet for a human decision.

That integration must preserve the same boundary: orchestration can persist work, but it cannot silently approve its own conclusions or modify production code.
