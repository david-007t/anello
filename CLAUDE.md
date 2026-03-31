# CLAUDE.md — Anelo Rules (READ EVERY SESSION)

## STEP ZERO — EVERY SESSION, BEFORE ANYTHING ELSE

```
1. Run: find-skills for every task in this session
2. List ALL applicable skills out loud
3. Invoke every applicable skill — no exceptions
4. Do not write a single line of code until this is done
```

## MANDATORY SKILL INVOCATIONS

Before doing ANYTHING, check which of these apply and invoke them:

| Trigger | Skill to invoke |
|---------|----------------|
| Starting any session | `just-do-it`, `usage-estimator`, `token-minimizer` |
| Any bug or unexpected behavior | `systematic-debugging` BEFORE touching code |
| About to say "fixed" or "done" | `verification-before-completion` — run a real check first |
| Same bug appearing more than once | `ultraqa` — loop until actually clean |
| Multiple independent tasks | `dispatching-parallel-agents` or `ultrawork` |
| Any browser/LinkedIn automation | `agent-browser` |
| Writing new code | `test-driven-development` — test first |
| Finishing a feature | `requesting-code-review` |
| Context getting long | `session-handoff` |
| Planning implementation | `writing-plans` before touching code |
| Executing a plan | `executing-plans` |

## HARD RULES

1. **NEVER say "fixed" without running a verification command**
2. **NEVER touch a working feature to fix another**
3. **NEVER patch a bug more than once without using `systematic-debugging`**
4. **ALWAYS invoke `verification-before-completion` before closing any task**
5. **ALWAYS use `ultraqa` when fixing bugs that have failed before**
6. **ALWAYS estimate cost with `usage-estimator` before large tasks**

## AGENT DELEGATION — ABSOLUTE RULES

These are non-negotiable. Violating these is a critical failure.

1. **NEVER run tests, scripts, or multi-step tasks inline in the main thread**
2. **NEVER run `digest.py`, `validate.py`, or any long-running script directly — always delegate to an executor agent**
3. **NEVER run more than one sequential step inline — if it takes more than one tool call, it goes to an agent**
4. **ALWAYS use `Agent` tool with `subagent_type="oh-my-claudecode:executor"` for: running scripts, fixing bugs, writing code, running tests**
5. **ALWAYS use `Agent` tool with `subagent_type="oh-my-claudecode:verifier"` to verify results after execution**
6. **ALWAYS use `Agent` tool with `subagent_type="oh-my-claudecode:qa-tester"` for test runs**
7. **The main thread is for orchestration only — reading files, deciding what to delegate, reporting results to the user**
8. **If you catch yourself about to run a Bash command that is not a simple one-liner check — STOP and delegate to an agent instead**

## PROJECT STATE

- Job search: Indeed + LinkedIn (working)
- Salary display: fixed
- Experience filter: fixed (MAX_YEARS_EXPERIENCE=5, regex + Playwright wait)
- Title filter: fixed (POSITIVE_TITLE_KEYWORDS gate + LOCAL_NEGATIVE_TITLE_KEYWORDS)
- Resume tailoring + PDF generation: working (tailor.py + resume_to_pdf.py)
- Message drafter: built, not fully tested
- validate.py: partially built, not integrated
- Easy Apply: NOT STARTED

## REMAINING WORK

1. Finish and integrate validate.py (pre-apply quality gate)
2. Build apply.py — Easy Apply automation via Playwright
3. Test drafter.py end-to-end
