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

**You MUST:**
- Delegate ALL implementation work to specialized agents
- Use TodoWrite to track workflow phases (not task details)
- Pass complete context to each agent

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

### Phase 4: Verdict Evaluation

| Reviewer | Tests | Action |
|----------|-------|--------|
| APPROVE | PASSED | → Phase 5 |
| REQUEST_CHANGES | any | → Phase 2 (with feedback) |
| any | FAILED | → Phase 2 (with failures) |
| NEEDS_DISCUSSION | any | → AskUserQuestion, then Phase 2 |

**If looping:** Update todo to show "Phase 2 (iteration N)" and include the feedback in the agent prompts.

### Phase 5: Git Operations

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

The workflow is complete when:
1. typescript-code-reviewer returns APPROVE
2. ts-test-runner returns PASSED
3. git-ops confirms commit and push successful
