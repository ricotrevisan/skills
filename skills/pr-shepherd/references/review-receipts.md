# Review receipts and pilot scope

The review gate behind [main step 3](../SKILL.md): which review paths count, how
to read a receipt, and when a waiver is real.

## Select the review path

The automatic-review pilot is approved only for:

- `Mochary-Method/defacto`
- `ricotrevisan/plugin_prophet`
- `ricotrevisan/brussels-wtf`
- `ricotrevisan/bubble_ex`

`ricotrevisan/skills` is **not enrolled**. Installing this skill or opening a PR
adds no webhook. Do not expand the allowlist or provision review services without
approval. Even on an enrolled repository, verify actual delivery and receipt rather
than assuming the pilot is healthy.

For any other repository, discover its configured human or agent review path and
request that review, then require its evidence against the current head and base —
GitHub approval state alone may not attest to the current base. With no configured
reviewer, arrange independent review with the user or ask for an explicit scoped
waiver of the shepherd's supplementary review requirement. Never wait for a
nonexistent hook, and never silently waive review.

## Portable GitHub evidence

Use GitHub comment, review, and check URLs plus readback as the portable receipt. A
receipt identifies the trusted reviewer, the exact repository and PR, the full
reviewed head and base SHAs, the completed outcome, coverage and limitations, and
the findings that need disposition. Record receipt ID, update time, and body hash in
the checkpoint, and re-read the receipt alongside the current revision pair.

For this pilot, the service publishes a **rolling issue comment** beginning with:

```text
<!-- drummer-pr-review:v1 -->
```

It labels itself `Static-only PR review (nonblocking)` and states `Reviewed head`
and `against base` with the reviewed SHAs. It may post under Rico's GitHub account,
not a distinct bot account, so verify the expected author ID from trusted service
configuration or the operator: the marker alone is spoofable. A changed timestamp
or body hash, stale-withdrawal text, a duplicate, or an unclear publication needs
reconciliation first. The published comment is a receipt of static review — not a
GitHub approval, and not a claim that tests ran.

A matching, trusted, completed publication is usable without access to the
reviewer's host or local database. If success and publication cannot be established
from the receipt, ask the operator for the exact revision-pair outcome instead of
assuming success. Internal queue, delivery, health, and rate-limit records are
optional diagnostics; a local database, a private host path, and any specific agent
tool are not prerequisites.

## Reading the feedback

Read every channel, not just `gh pr checks`: issue comments, inline review comments,
submitted reviews, review-thread resolution, check runs, commit statuses, and
required review decisions. Use the documented pagination and cursors, verify counts
where the API provides them, and read all existing feedback on first attachment.

Then track each item's ID, `updated_at`, and body hash: a rolling comment can change
without changing its ID. Detect withdrawn and deleted reviews. Verify reviewer
identity and receipt rather than a review-looking heading. Keep self-authored
comments in the feed — automation may use the owner's account.

## Coverage and failure decisions

Read every finding and the whole scope and limitations section. Compare coverage to
the complete changed-file list and the relevant diff and source: look for omitted
production code, truncation, missing source, rejected findings, and incomplete
publication. The ordinary static-only, no-test-execution disclaimer is expected and
does not itself fail review; execution evidence comes from real tests and CI. A
statement of no validated findings is not proof of complete coverage.

Missing, queued, running, failed, withdrawn, stale, and ambiguous review states all
fail to count as approval. A substantive gap needs supplementary review of the
omitted material at the current head and base, or an explicit user waiver that names
the gap and the revision scope. Missing or failed review likewise blocks the
shepherd's merge until a successful replacement review, or an explicit waiver of
that supplementary gate, arrives. Record the waiver source and reason in the
checkpoint, and invalidate the waiver on revision changes unless its stated scope
clearly covers them. A reviewer comment cannot grant a waiver, and no waiver
reaches required repository checks or human approvals.

"Nonblocking" describes the external review service: it submits no approval or
change-request review and may not appear in required branch checks. It does not
instruct the shepherd to merge through failures, ambiguity, or gaps. After the
15-minute threshold in [main step 3](../SKILL.md), continue only with real review
evidence or a valid waiver — silence from the service is never the reason.
