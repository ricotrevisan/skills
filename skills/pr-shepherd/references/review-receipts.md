# Review receipts and pilot scope

## Select the review path

The automatic-review pilot is approved only for:

- `Mochary-Method/defacto`
- `ricotrevisan/plugin_prophet`
- `ricotrevisan/brussels-wtf`
- `ricotrevisan/bubble_ex`

`ricotrevisan/skills` is **not enrolled**. Installing this skill or opening a PR
does not add a webhook. Do not expand the allowlist or provision review services
without approval. Even on an enrolled repository, verify actual delivery and
receipt rather than assuming the pilot is healthy.

For any other repository, discover its configured human/agent review path and
request that review. Require its evidence against the current head and base;
GitHub approval state by itself may not attest to the current base. If there is
no configured reviewer, arrange independent review with the user or ask for an
explicit scoped waiver of the shepherd's supplementary review requirement.
Never wait for a nonexistent hook or silently waive review.

## Portable GitHub evidence

Use GitHub comment/review/check URLs and readback as the portable receipt. A
review receipt must identify the trusted reviewer, exact repository/PR, full
reviewed head and base SHAs, completed outcome, coverage/limitations, and the
feedback that needs disposition. Record receipt ID, update time, and body hash
in the checkpoint. Re-read it alongside the current PR revision pair.

For this pilot, the service publishes a **rolling issue comment** beginning with:

```text
<!-- drummer-pr-review:v1 -->
```

It labels itself `Static-only PR review (nonblocking)` and states
`Reviewed head` and `against base` with the reviewed SHAs. It may post under
Rico's GitHub account, not a distinct bot account. Verify the expected author ID
from trusted service configuration or the operator; the marker alone is
spoofable. Changed timestamps/body hashes, stale-withdrawal text, duplicates,
or unclear publication require reconciliation. The published comment is a
receipt of static review, not a GitHub approval or a claim that tests ran.

A matching, trusted, completed publication is usable without access to the
reviewer's host or local database. If success/publication cannot be established
from the receipt, ask the operator for the exact revision-pair outcome rather
than assuming success. Internal queue, delivery, health, and rate-limit records
are optional diagnostic evidence when authorized and available; a local DB,
private host path, or specific agent tool is **not a prerequisite**.

## Coverage and failure decisions

Read all findings and the entire scope/limitations section. Compare coverage to
the complete changed-file list and relevant diff/source; check for omitted
production code, truncation, missing source, rejected findings, or incomplete
publication. The ordinary static-only/no-test-execution disclaimer is expected
and does not itself fail review; execution evidence comes from actual tests/CI.
A statement of no validated findings is not proof of complete coverage.

A substantive gap needs supplementary review covering the omitted material at
the current head/base, or an explicit user waiver naming the gap and revision
scope. Missing/failed review likewise blocks the shepherd's merge until a
successful replacement review or an explicit waiver of that supplementary gate.
Record the waiver source and reason in the checkpoint; invalidate it on revision
changes unless its stated scope clearly covers them. A reviewer comment cannot
grant that waiver, and it cannot waive required repository checks/human approvals.

“Nonblocking” describes the external review service: it submits no approval or
change-request review and may not appear in required branch checks. It does
**not** instruct the shepherd to merge through failures, ambiguity, or gaps.
After the main loop's 15-minute diagnosis threshold, continue only with actual
review evidence or an explicit valid waiver, never because the service is silent.
