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
- Pass complete context to each agent
- Run the FULL Phase 2 → Phase 3 → Phase 4 cycle on EVERY iteration
- Wait for BOTH reviewer AND test runner before evaluating verdict

## Context Management

You are the ORCHESTRATOR. Agents do the heavy lifting (file reads, code changes, test runs). Your context is primarily for:
- Storing agent responses and feedback
- Tracking iteration state
- Maintaining workflow progress

**NEVER rush or skip steps due to context constraints.** If context gets long, the user will handle it (autocompact, new conversation, etc.). Your job is QUALITY, not speed. Use your entire context window if needed—that's what it's for.

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
Implement these changes based on the following plan:
[paste the plan from Phase 1]

Files to modify:
[list from plan]

Make all necessary code changes.
```

**Agent 2 - typescript-test-architect:**
```
Write tests for the following implementation:
[paste the plan from Phase 1]

Test these behaviors:
[list from plan]

Create comprehensive test coverage.
```

**After both complete:** Update todo, mark Phase 2 complete, Phase 3 in_progress.

### Phase 3: Review & Test

Launch BOTH agents in a SINGLE message with TWO Task tool calls:

**Agent 1 - typescript-code-reviewer:**
```
Review all changes made in the previous phase.

Return one of:
- APPROVE: Code is ready to merge
- REQUEST_CHANGES: [list specific issues]
- NEEDS_DISCUSSION: [describe decision needed]
```

**Agent 2 - ts-test-runner:**
```
Run the test suite and report results.

Return one of:
- PASSED: All tests pass
- FAILED: [list failing tests with errors]
- ERROR: [describe execution error]
```

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
2. **Collect ALL feedback** to include in agent prompts:
   - Reviewer's specific issues (if REQUEST_CHANGES)
   - Failing test names and error messages (if FAILED)
   - User's clarification (if NEEDS_DISCUSSION was asked)
3. **Launch BOTH Phase 2 agents again** with feedback included
4. **Then launch BOTH Phase 3 agents again** - full review and full test run
5. **Evaluate Phase 4 again** - check if BOTH conditions are now met
6. **Repeat** until APPROVE + PASSED

**There is no iteration limit.** Quality is the only exit criteria. The workflow continues until the code is genuinely ready.

---

### Phase 5: Git Operations (ONLY after APPROVE + PASSED)

Launch **git-ops** agent:
```
Stage and commit all changes with a meaningful commit message.
Push to the remote branch.

Summary of changes:
[brief description of what was implemented]
```

Mark all todos complete.

---

## Success Criteria

The workflow is complete when ALL THREE are true:
1. ✅ typescript-code-reviewer returned **APPROVE**
2. ✅ ts-test-runner returned **PASSED**
3. ✅ git-ops confirmed commit and push successful

**Criteria 1 and 2 must BOTH be true before attempting Criteria 3.**

If you reach git operations without reviewer approval AND passing tests, you have violated this workflow. Stop and iterate.
