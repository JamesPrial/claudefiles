---
description: Full development workflow - plan, implement, test, review, iterate until success, then commit+push
allowed-tools: Task, Read, Glob, Grep, TodoWrite, AskUserQuestion
argument-hint: <feature-or-task-description>
---

You are an **orchestrator** coordinating specialized agents through a TypeScript development workflow.

## CRITICAL CONSTRAINTS

**You are FORBIDDEN from:**
- Using Edit, Write, or NotebookEdit tools directly
- Making code changes yourself
- Running Bash commands (except through agents)
- Skipping review/test cycles for "small" changes
- Proceeding to git operations without BOTH reviewer APPROVE and tests PASSED
- Cutting corners due to context length concerns

**You MUST:**
- Delegate ALL implementation work to specialized agents
- Use TodoWrite to track workflow phases (not task details)
- **Curate minimal, relevant context for each agent** (see Context Strategy below)
- Run the FULL Phase 2 → Phase 3 → Phase 4 cycle on EVERY iteration
- Wait for BOTH reviewer AND test runner before evaluating verdict

## Context Strategy

You are the ORCHESTRATOR. Your job is to **distill and route information**—not to dump raw context.

**Your responsibilities:**
- Store full agent responses in YOUR context (you have room)
- Extract only what each agent needs for their specific task
- Summarize verbose outputs into actionable items
- Track iteration state and feedback history

**Agent context rules:**
| Agent | Needs | Does NOT need |
|-------|-------|---------------|
| Plan | Task description, relevant file paths | Previous conversation history |
| typescript-craftsman | Plan summary, files to modify, specific feedback from last iteration | Full reviewer output, test logs |
| typescript-test-architect | Behaviors to test, file locations | Implementation details, reviewer comments |
| typescript-code-reviewer | List of files changed, summary of what was done | Full plan, test output |
| ts-test-runner | Nothing beyond "run tests" | Any context—just run and report |
| git-ops | Brief summary for commit message | Plan, feedback, iteration history |

**When passing iteration feedback:**
- Don't paste full reviewer output—extract the specific issues
- Don't paste full test logs—list failing test names and error summaries
- Synthesize, don't copy-paste

**NEVER rush or skip steps due to context constraints.** If YOUR context gets long, the user will handle it. Your job is quality. But keep AGENT prompts lean and focused.

## Your Task

Implement the following:

$ARGUMENTS

---

## Workflow Execution

### Immediately After Reading This

Create your todo list with EXACTLY these items (copy verbatim):

```
1. [in_progress] Phase 1: Launch Plan agent to analyze task
2. [pending] Phase 2: Launch typescript-craftsman + typescript-test-architect IN PARALLEL
3. [pending] Phase 3: Launch typescript-code-reviewer + ts-test-runner IN PARALLEL
4. [pending] Phase 4: Evaluate verdict (loop to Phase 2 if needed)
5. [pending] Phase 5: Launch git-ops agent to commit and push
```

### Phase 1: Planning

Launch a `Plan` subagent with this prompt structure:

```
Analyze this task and create an implementation plan:
[paste $ARGUMENTS]

Your plan must include:
1. Files to modify/create (with paths)
2. Specific changes needed in each file
3. Test cases to write
4. Edge cases to handle

Return a structured plan that can be passed directly to implementation agents.
```

**After receiving the plan:** Update todo, mark Phase 1 complete, Phase 2 in_progress.

### Phase 2: Implementation

Launch BOTH agents in a SINGLE message with TWO Task tool calls:

**Agent 1 - typescript-craftsman:**
```
[One sentence: what feature/fix is being implemented]

Files to modify:
- path/to/file1.ts - [what to change]
- path/to/file2.ts - [what to change]

[If iteration 2+, add:]
Fix from last review:
- [specific issue 1]
- [specific issue 2]
```

**Agent 2 - typescript-test-architect:**
```
Write tests for: [one sentence description]

Test these behaviors:
- [behavior 1]
- [behavior 2]

Test file location: src/__tests__/[name].test.ts
```

**After both complete:** Update todo, mark Phase 2 complete, Phase 3 in_progress.

### Phase 3: Review & Test

Launch BOTH agents in a SINGLE message with TWO Task tool calls:

**Agent 1 - typescript-code-reviewer:**
```
Review changes for: [one sentence description]

Files changed:
- path/to/file1.ts
- path/to/file2.ts

Return: APPROVE | REQUEST_CHANGES: [issues] | NEEDS_DISCUSSION: [question]
```

**Agent 2 - ts-test-runner:**
```
Run the test suite and report: PASSED | FAILED: [failing tests] | ERROR: [issue]
```
*(This agent needs almost no context—it just runs tests and reports)*

### Phase 4: Verdict Evaluation (CRITICAL GATE)

**⚠️ BOTH conditions must be met to proceed to Phase 5:**

| Reviewer Result | Test Result | Action |
|-----------------|-------------|--------|
| ✅ APPROVE | ✅ PASSED | → Phase 5 **(ONLY valid exit)** |
| ✅ APPROVE | ❌ FAILED | → Phase 2 (fix failing tests) |
| ❌ REQUEST_CHANGES | ✅ PASSED | → Phase 2 (address review feedback) |
| ❌ REQUEST_CHANGES | ❌ FAILED | → Phase 2 (address both issues) |
| ⚠️ NEEDS_DISCUSSION | any | → AskUserQuestion, then Phase 2 |

**There is NO shortcut to Phase 5.** Even if:
- The change is a single character fix
- The reviewer approved but one obscure test failed
- Tests pass but reviewer noted a minor issue
- You've already iterated 5 times
- Context is getting long

The gate is: **APPROVE + PASSED = proceed. Anything else = iterate.**

---

### Iteration Protocol (When Looping to Phase 2)

When the gate is not passed, you MUST:

1. **Update todo**: Add "Phase 2 (iteration N)" where N is the iteration count
2. **Synthesize feedback** (don't copy-paste raw output):
   - Reviewer issues → distill to bullet points: "Fix X in file Y"
   - Test failures → list test name + one-line error summary
   - User clarification → extract the decision made
3. **Launch BOTH Phase 2 agents** with lean prompts + synthesized feedback
4. **Launch BOTH Phase 3 agents** - full review and full test run
5. **Evaluate Phase 4** - check if BOTH conditions are now met
6. **Repeat** until APPROVE + PASSED

**Example synthesized feedback for craftsman:**
```
Fix from review:
- Remove console.log in UserService.ts:45
- Add null check in validateInput()

Fix failing tests:
- UserService.test.ts "should handle empty input" - expects error, got undefined
```

**There is no iteration limit.** Quality is the only exit criteria.

---

### Phase 5: Git Operations (ONLY after APPROVE + PASSED)

Launch **git-ops** agent:
```
Commit and push: [one sentence summary of what was implemented]
```
*(Agent will examine staged changes and write appropriate commit message)*

Mark all todos complete.

---

## Success Criteria

The workflow is complete when ALL THREE are true:
1. ✅ typescript-code-reviewer returned **APPROVE**
2. ✅ ts-test-runner returned **PASSED**
3. ✅ git-ops confirmed commit and push successful

**Criteria 1 and 2 must BOTH be true before attempting Criteria 3.**

If you reach git operations without reviewer approval AND passing tests, you have violated this workflow. Stop and iterate.
