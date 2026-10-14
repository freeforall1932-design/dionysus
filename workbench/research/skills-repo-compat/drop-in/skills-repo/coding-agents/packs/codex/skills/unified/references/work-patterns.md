# Work patterns

All six exist to write **less code**, so the agent bills fewer tokens. Pick the
pattern that fits the task, then stop inside it.

## 1. investigate-first

*Unknown cause, intermittent bug, performance regression.*

Rank hypotheses by evidence. Reproduce first. **Do not edit until one credible
mechanism explains the evidence.** Report the cause and the proof.

## 2. lean-build

*New feature, product slice, integration.*

Derive acceptance criteria **and explicit non-goals**. Omit modes, providers,
configuration and polish unless acceptance requires them. Prefer the boring,
well-understood option.

## 3. surgical-patch

*Bug fix, small behaviour change.*

Reproduce the failure first. Change the narrowest layer that owns the behaviour.
No drive-by refactors, no opportunistic renames.

## 4. safe-refactor

*Restructuring with behaviour preserved (make the change easy, then make the easy change).*

Establish verification **before** any structural edit. Move one ownership
boundary at a time. Behaviour unchanged at every step.

## 5. migration

*Schema change, data move, API change, dependency upgrade.*

Define the forward path **and the rollback path**. Sequence: expand → migrate →
verify → contract.

## 6. verify-and-stop

*Validation only, completion check.*

Smallest sufficient proof set. **Stop the moment acceptance proof is complete.**
Do not continue into adjacent improvements.
