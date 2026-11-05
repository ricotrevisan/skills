---
name: hill-climb-design
description: UI/UX hill climb — blind judges score each round, kept rounds merge into one root PR that Rico merges at the end.
disable-model-invocation: true
---

# Hill-climb design

You are the **climber**. You improve one surface of an app in **rounds**. Each round is a small change in its own worktree and its own PR. Fresh **blind judges** compare it against the current root. A round that wins is **kept**: it squash-merges into the **root PR**. A round that loses is **discarded**: its PR closes and the root stays clean. Only Rico merges the root PR into `main`.

```text
main
 └─ root PR  climb/<topic> → main     draft; Rico merges it, squash
     ├─ round 1 PR → climb/<topic>    kept: squash-merged
     ├─ round 2 PR → climb/<topic>    discarded: closed
     └─ round 3 PR → climb/<topic>    branched from the latest root
```

Every PR shows screenshots. Upload them with [`scripts/pr-shots`](scripts/pr-shots). It commits images to the orphan branch `pr-assets` and prints Markdown links pinned to that commit, which render on private repos for logged-in members. Use 1x PNG or WebP. Never delete `pr-assets`.

## 1. Pin the climb

Write `climb.md` in the **run dir** `~/hill-climb-runs/<repo>/<topic>/`, outside any worktree, with these fields:

- **Surface**: the routes in scope.
- **Fixed set**: every screen the judges see, at 320px and 1440px. Use the same seeded data, locale and full-page capture every time. Add states that matter, such as empty, error and an open menu.
- **Key tasks**: 1–3 things a user comes to do, each with an observable end state, e.g. "an issue is added to the meeting and shows in the list".
- **Reference**: one best-in-class page the judges also score. A stable reference score shows the judges aren't drifting.
- **Rubric**: the criteria set from [`rubric.md`](rubric.md).
- **Judges**: two judges on different providers. In T3, call `orchestrator_capabilities` and pick two providers. In pi, use `subagent` with two `model`s.
- **Constraints**: the repo's `AGENTS.md`, `DESIGN.md` and `PRODUCT.md` rules, and what is off limits, such as official wording, pricing or legal copy.

Then write `capture` in the run dir. It takes a base URL and an output dir and shoots the fixed set the same way every run, using the host's browser policy. The fixed set is frozen after round 0.

**Exit:** `climb.md` has every field, and `capture` produces the whole set twice in a row with the same file names.

## 2. Open the root

```bash
git switch -c climb/<topic> origin/main
git commit --allow-empty -m "Start hill climb: <topic>"
git push -u origin climb/<topic>
gh pr create --draft --base main --head climb/<topic> --title "<Topic>: design hill climb" --body "Hill climb in progress. Rico merges this PR."
```

**Exit:** the draft root PR exists and its URL is in `climb.md`.

## 3. Round 0: baseline

Serve the root, then run `capture` into `round-0/shots/`. Run one walker on the root ([`walker-brief.md`](walker-brief.md)). Run the judges on the baseline alone, with the reference ([`judge-brief.md`](judge-brief.md)). Write the root PR body (see **Root PR body**).

**Exit:** `round-0/` has shots, `walk.md` and one score file per judge, and the root PR shows the baseline.

## 4. Climb

Repeat for round `n = 1, 2, …`:

1. **Pick.** Choose the change with the most headroom: the lowest criteria, the judges' `top_fixes`, and every walker friction moment. Make one coherent change per round. A big redesign is fine if it is one idea.
2. **Build.** Merge `origin/main` into the root if `main` moved. Then create a worktree on branch `climb/<topic>-r<n>` from the latest `origin/climb/<topic>`. Make the change and run the repo's checks, such as `mix precommit`, the fit check and translations.
3. **Shoot.** Serve the worktree. Run `capture` into `round-<n>/shots/` and one walker into `round-<n>/walk.md`.
4. **Open.** Open a PR to `climb/<topic>`. The body lists what changed and why, with a `| Before | After |` table for each screen that changed, at both widths. Before is the root's current shot.
5. **Judge.** Give each fresh judge two sets, root and candidate, labelled `X` and `Y` in random order, plus the reference. Shuffle the order per judge. Judges never learn which set is new, the round number, earlier scores or the target.
6. **Decide.** Keep the round when the mean gain across judges, measured as candidate average minus root average, is positive, and no judge scores `task_flow` lower. Otherwise discard it.
   - **Kept:** `gh pr merge --squash --delete-branch`. Its shots and walk become the root's. Update the root PR body.
   - **Discarded:** comment the scores on the PR, then close it. Reuse its lessons, not its branch.
   - Either way, add a row to `scores.md` and remove the round's worktree.

**Stop** when either judge scores every criterion 80+ for the root, after round 8, or after 3 rounds in a row with no kept round. Continue past round 8 only when Rico asks.

A finding that needs a product decision is not a design fix: generated headlines, new copy claims, pricing, removing a step. Log it as `needs decision` with the options, and keep climbing on the rest.

**Exit:** a stop rule fired, every round has a `scores.md` row and a merged or closed PR, and no round worktree is left.

## 5. Hand over

Merge `origin/main` into the root once more, run the repo's checks, recapture and update the root PR body. Then run `gh pr ready`. Leave the merge to Rico, and say it should be a squash merge.

## Root PR body

Rewrite the whole body after round 0, after each kept round and at hand-over. It has these parts:

1. **Outcome:** whether the target was reached, and which scores are still under 80, with the reason.
2. **Scores:** baseline → now per criterion, one column per judge, and the reference row.
3. **Rounds:** one row per round: PR link, idea, kept or discarded, mean gain.
4. **Screens:** the root's current shot of every screen in the fixed set, at 320px and 1440px side by side. Put each route group in a `<details>` block when the set is longer than 6 screens.
5. **Key tasks:** one line per task with the walker's result: steps taken, and done, stuck or quit.
6. **Needs decision:** each item with its options.
7. **Verified:** checks run and their counts.
