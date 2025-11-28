---
description: Full development workflow - plan, implement, test, review, iterate until success, then commit+push
allowed-tools: Task, Read, Glob, Grep, TodoWrite, AskUserQuestion
argument-hint: <feature-or-task-description>
---

You are orchestrating a complete TypeScript development workflow. Your role is to coordinate specialized agents through a structured process until the implementation is complete and verified.

## Your Task

Implement the following:

$ARGUMENTS

## Workflow Phases

Execute these phases in order, looping as needed until success:

### Phase 1: Planning

Launch a `Plan` subagent to analyze the task:
- Understand the scope and requirements
- Identify files that need modification
- Design the implementation approach
- Consider edge cases and error handling

Wait for the plan before proceeding.

### Phase 2: Implementation

Launch BOTH agents IN PARALLEL (single message, two Task tool calls):

1. **typescript-craftsman**: Implement the planned changes
   - Provide the plan from Phase 1
   - Specify which files to create/modify

2. **typescript-test-architect**: Write comprehensive tests
   - Provide the plan from Phase 1
   - Describe what behaviors to test

### Phase 3: Review & Test

After implementation completes, launch BOTH agents IN PARALLEL:

1. **typescript-code-reviewer**: Review all changes
   - Will return: APPROVE, REQUEST_CHANGES, or NEEDS_DISCUSSION

2. **ts-test-runner**: Execute the test suite
   - Will return: PASSED, FAILED, or ERROR

### Phase 4: Verdict Evaluation

Analyze the results from Phase 3:

**If reviewer returns APPROVE AND tests PASSED:**
- Proceed to Phase 5 (Git)

**If reviewer returns REQUEST_CHANGES OR tests FAILED:**
- Extract the specific issues from both reports
- Return to Phase 2 with the feedback incorporated
- Continue looping until success

**If reviewer returns NEEDS_DISCUSSION:**
- First, assess if YOU can resolve the discussion point
- If you can make a reasonable decision: loop back to Phase 2 with your decision
- If the issue requires user input: use AskUserQuestion to get their preference, then loop

### Phase 5: Git Operations

Once APPROVE + PASSED:

Launch **git-ops** agent to:
1. Stage all changed files
2. Create a meaningful commit message summarizing the implementation
3. Push to the remote branch

## Important Guidelines

- Use TodoWrite to track progress through phases
- Always launch parallel agents in a SINGLE message with multiple Task tool calls
- Pass context forward: each phase builds on previous results
- Never skip the review/test phase
- Be persistent: keep iterating until the code is correct
- When looping, be specific about what needs fixing based on reviewer/test feedback

## Success Criteria

The workflow is complete when:
1. Code reviewer returns APPROVE
2. Test runner returns PASSED
3. Changes are committed and pushed

Begin by reading the codebase context, then start Phase 1.
