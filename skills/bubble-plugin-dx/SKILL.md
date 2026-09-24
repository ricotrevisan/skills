---
name: bubble-plugin-dx
description: Bubble plugin DX audit, element usability, junior/senior grading.
---

# Bubble plugin developer experience

Evaluate the experience of a Bubble builder using a plugin element. Apply this
rubric to audits, comparisons, and ease-versus-power design decisions. Keep
plugin-specific findings in the evaluated project's report or issue.

## Gather evidence

Inspect the element's actual properties, defaults, field help, preview, states,
events, actions, data contract, builder documentation, and relevant runtime
paths. Read project instructions for the correct editor/demo and version.

Identify the reviewed revision/version and distinguish source inspection,
historical test evidence, fresh runtime verification, and observed usability
sessions. A source review produces provisional scores; existing test counts
alone do not establish smooth onboarding. Mark unavailable evidence as unknown.

Follow these builder journeys where access and task scope permit:

- Place the element and produce the first meaningful result.
- Connect real Bubble data, including empty and missing values.
- Change data through a filter or workflow.
- Consume an interaction through native states and events.
- Diagnose invalid configuration and recover.
- Resize, hide/show, and interact on mobile and with a keyboard.
- Exercise an advanced requirement appropriate to the element.

Record the obstacle, observable consequence, evidence, and smallest useful
improvement for each finding. Separate confirmed defects from design tradeoffs
and untested hypotheses. An audit does not imply implementation or publication.

## Audience priorities

| Need | Junior builder | Senior builder |
| --- | --- | --- |
| First success | Copyable example and good defaults | Quickly assess product fit |
| Data | Bind a search and choose fields | Aggregation, identities, dates, multiple series, API data |
| Configuration | Familiar names and relevant options | Explicit semantics, reusable settings, overrides |
| Workflows | Copyable interaction-to-action recipe | Typed states, event timing, selection lifecycle |
| Failure | Know exactly what to fix | Observe failure, retained data, and recovery |
| Appearance | Good result with little setup | Consistent design-system control |
| Production | Responsive behavior without special fixes | Lifecycle, performance, compatibility, upgrades |
| Documentation | Short editor-oriented tutorial | Accurate searchable reference and edge cases |

Senior builders also value simplicity. Added complexity should buy capability.

## Grade

Use the same evidence-based dimension scores with audience-specific weights.
Explain any intentional weight changes before comparing results.

| Dimension | Observable standard | Junior % | Senior % |
| --- | --- | ---: | ---: |
| First success | Install, place, configure, preview a meaningful result | 15 | 5 |
| Real data | Bind ordinary data without fragile transformations | 25 | 15 |
| Configuration clarity | Understand names, defaults, applicable options | 15 | 5 |
| Errors and recovery | Diagnose failure and recover independently | 15 | 15 |
| Workflow integration | Use states, events, actions, and stable selection | 10 | 20 |
| Runtime reliability | Update, resize, hide/show, mobile and keyboard use | 10 | 15 |
| Customization and control | Meet relevant product requirements without hacks | 5 | 15 |
| Documentation and maintenance | Find accurate instructions and upgrade safely | 5 | 10 |

Score each dimension 0–5:

- 0: Missing or unusable.
- 1: Requires substantial assistance.
- 2: Works with frequent workarounds.
- 3: Usable independently with documentation.
- 4: Smooth common tasks and predictable edge cases.
- 5: Excellent common and advanced paths, demonstrated in usability testing.

Each audience's score out of 100 is `sum(weight * dimension_score / 5)`.
Bands: A 90–100; B 75–<90; C 60–<75; D 40–<60; F <40.
Report uncertainty alongside the grade. If a dimension is unknown, report a
possible total range or leave the total ungraded; unknown is not a zero or pass.

Assess release blockers separately: silent incorrect data, broken advertised
workflow outputs, and unexplained breaking changes override a favorable average.
Report whether each is observed, ruled out in a stated test, or unverified.

## Balance ease and power

Prefer a short path to a useful result, native controls for common adjustments,
and documented advanced inputs for less common needs. Keep those paths on one
consistent validated behavior contract, with explicit precedence.

Evaluate data entry by the builder's task. JSON may be valuable for API-shaped
data but costly as the mandatory path for a simple Bubble search. Investigate
native binding when useful; verify the actual Bubble editor/API capabilities
before prescribing field mapping. Account for ordering, nulls, and alignment if
considering parallel lists.

Judge configuration by relevance and comprehension, not field count alone.
Separate elements when their data or interaction models differ; standardize
shared behavior and terminology. Check practical details such as zero versus no
selection, stable IDs, raw versus formatted values, event timing, programmatic
updates, stale data after errors, load failures, and defaults versus controlled
inputs. Assess these against each element's documented semantics.

## Deliver and validate

Return the verdict, evidence scope, both weighted scorecards, prioritized
findings, and concrete next steps. Preserve strengths worth retaining. Recommend
independently demoable improvements rather than disconnected implementation
layers. When asked for a ticket, make it self-contained with problem, evidence,
scope, observable acceptance criteria, demo path, dependencies, and open decisions.

For usability validation, use comparable tasks with junior and senior builders.
Measure completion, time, assistance, documentation lookups, and incorrect
results. Suggested initial targets for a simple chart are 10 minutes to real
data, 5 more to an interaction workflow, and 2 to recover from an injected error.
Label these as proposed targets, adapt them to the element, and distinguish them
from measured outcomes. Regrade after evidence changes.
