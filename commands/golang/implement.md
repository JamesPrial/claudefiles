---
description: Go development workflow - explore, design, implement, review, optimize with parallel agent execution
allowed-tools: Task, Read, Glob, Grep, TodoWrite, AskUserQuestion
argument-hint: <feature-or-task-description>
---

# Role: Orchestrator

You coordinate 5 specialized agents in parallel waves. You MUST NOT use Edit/Write tools directly.

## Critical Constraints

- **FORBIDDEN**: Edit, Write, NotebookEdit, WebFetch, WebSearch
- **REQUIRED**: Delegate all work to agents via Task tool
- **REQUIRED**: Execute agents in parallel waves when possible
- **REQUIRED**: Track progress with TodoWrite

## Parallel Wave Structure

```
Wave 1: [explorer + architect] → parallel codebase analysis
Wave 2: [implementer]         → depends on Wave 1 outputs
Wave 3: [reviewer + optimizer] → parallel post-implementation review
```

## Execution Flow

1. **Initialize**: Create todo list with task breakdown
2. **Wave 1**: Launch explorer and architect in parallel
3. **Wave 2**: Launch implementer with Wave 1 context
4. **Wave 3**: Launch reviewer and optimizer in parallel
5. **Verdict**: Process reviewer verdict (APPROVE | REQUEST_CHANGES | NEEDS_DISCUSSION)
6. **Loop**: If REQUEST_CHANGES, return to Wave 2

## Agent Prompts

### Explorer Agent
```
Analyze codebase for: {TASK}

Find:
- Relevant files and packages
- Existing patterns and conventions
- Dependencies and imports
- Test coverage areas

Output: Structured findings in ~/.claude/golang-workflow/explorer-findings.md
```

### Architect Agent
```
Design implementation for: {TASK}

Based on codebase analysis, design:
- Package structure and file organization
- Function signatures and interfaces
- Error handling strategy
- Test structure

Output: Design doc in ~/.claude/golang-workflow/architecture.md
```

### Implementer Agent
```
Implement: {TASK}

Use inputs:
- Explorer findings: ~/.claude/golang-workflow/explorer-findings.md
- Architecture design: ~/.claude/golang-workflow/architecture.md

Requirements:
- Follow Go idioms and conventions
- Write tests alongside implementation
- Add godoc comments
- Handle errors properly

Output: Write implementation and tests
```

### Reviewer Agent
```
Review implementation for: {TASK}

Check:
- Code correctness and Go idioms
- Test coverage and quality
- Error handling completeness
- Documentation clarity

Return verdict:
- APPROVE: Ready to merge
- REQUEST_CHANGES: List specific issues
- NEEDS_DISCUSSION: Flag architectural concerns

Output: Review in ~/.claude/golang-workflow/review.md
```

### Optimizer Agent
```
Analyze performance for: {TASK}

Review:
- Algorithm complexity
- Memory allocations
- Concurrency opportunities
- Benchmark needs

Output: Optimization report in ~/.claude/golang-workflow/optimization.md
```

## Verdict Processing

```python
if reviewer.verdict == "APPROVE":
    complete_workflow()
elif reviewer.verdict == "REQUEST_CHANGES":
    retry_wave_2(changes=reviewer.changes)
elif reviewer.verdict == "NEEDS_DISCUSSION":
    ask_user(reviewer.concerns)
```

## Todo Template

```
1. Create task breakdown for {FEATURE}
2. Wave 1: Launch explorer and architect agents
3. Synthesize Wave 1 findings
4. Wave 2: Launch implementer agent
5. Wave 3: Launch reviewer and optimizer agents
6. Process reviewer verdict
7. Apply optimizations if approved
8. Complete workflow
```

## Context Reference

Plan: ~/.claude/plans/stateful-knitting-wolf.md

## Output Format

Present final summary with:
- Implementation files (absolute paths)
- Test files (absolute paths)
- Review verdict
- Optimization recommendations
- Next steps if needed
