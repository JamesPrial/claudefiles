# Commands

Commands are orchestrators that coordinate specialized agents through multi-step workflows. Unlike individual agents that perform focused tasks, commands define entire development processes with phases, gates, and quality controls.

## What Are Commands?

Commands are markdown files with frontmatter that:
- Define allowed tools (typically Task, Read, Glob, Grep, TodoWrite, AskUserQuestion)
- Coordinate multiple specialized agents in parallel or sequential waves
- Enforce workflow gates (review approval, tests passing, etc.)
- Track progress through complex multi-phase processes
- Prevent shortcuts and ensure quality standards

Commands are invoked as slash commands: `/implement`, `/golang/implement`, `/docs/generate-overview`

## Available Commands

### TypeScript Development

**`typescript/implement.md`** - Full TypeScript development workflow
- Orchestrates 6+ specialized agents through 6 phases
- Parallel wave execution for analysis, implementation, and review
- Multi-perspective planning (security, maintainability, testing, etc.)
- Enforces paired code + test implementation to prevent reward hacking
- Quality gates: reviewer APPROVE + tests PASSED required to proceed
- Usage: `/typescript/implement <feature-or-task-description>`

Key phases:
1. Phase 0: Codebase exploration
2. Phase 1A: Multi-perspective analysis (2-5 perspectives in parallel)
3. Phase 1B: Plan synthesis with conflict resolution
4. Phase 2: Parallel implementation (craftsman + test-architect pairs)
5. Phase 3: Parallel review + test execution
6. Phase 4: Unit-level verdict with iteration loop
7. Phase 5: Final integration review
8. Phase 6: Git operations (commit + push)

### Go Development

**`golang/implement.md`** - Go development workflow with parallel agent execution
- Coordinates 5 specialized agents in 3 parallel waves
- Explorer + architect analyze in parallel (Wave 1)
- Implementer executes based on analysis (Wave 2)
- Reviewer + optimizer validate in parallel (Wave 3)
- Verdict loop: APPROVE | REQUEST_CHANGES | NEEDS_DISCUSSION
- Hooks auto-run `go fmt` and `go vet` on file changes
- Usage: `/golang/implement <feature-or-task-description>`

Agent structure:
- **Explorer**: Analyzes codebase patterns and dependencies
- **Architect**: Designs package structure and interfaces
- **Implementer**: Writes code and tests following Go idioms
- **Reviewer**: Checks correctness, tests, errors, documentation
- **Optimizer**: Analyzes performance and suggests improvements

### Documentation

**`docs/generate-overview.md`** - Repository documentation generator
- Analyzes repository structure automatically
- Generates AI-powered "What's Here" section for README.md
- Documents directories, agents, commands, skills, hooks, and plugins
- Preserves existing content with clear separator
- Usage: `/docs/generate-overview`

Process:
1. Explores repository structure (directories, config files, components)
2. Analyzes codebase to understand purpose and organization
3. Generates comprehensive overview with directory structure
4. Updates README.md with formatted Markdown
5. Optionally commits changes

## Command Structure

All commands follow this structure:

```markdown
---
description: Brief description shown in CLI
allowed-tools: Task, Read, Glob, Grep, TodoWrite, AskUserQuestion
argument-hint: <what-the-user-should-provide>
---

# Command content with instructions for the orchestrator
```

## Key Principles

1. **Orchestration, not implementation**: Commands delegate work to agents via Task tool
2. **Parallel execution**: Independent work happens simultaneously for efficiency
3. **Quality gates**: Enforce review + tests before proceeding
4. **Progress tracking**: Use TodoWrite to show workflow state
5. **Context curation**: Pass minimal, relevant context to each agent
6. **No shortcuts**: Complete all phases even for "simple" changes
7. **Verdict loops**: Iterate until quality gates pass

## Forbidden in Commands

Commands must NOT:
- Use Edit, Write, or NotebookEdit tools directly
- Make code changes themselves
- Skip review/test cycles
- Proceed without passing quality gates
- Let agents see each other's work when it would bias results
- Dump raw context - always synthesize and curate

## Usage Examples

```bash
# TypeScript feature implementation
/typescript/implement Add user authentication with JWT tokens

# Go feature with testing
/golang/implement Create HTTP middleware for rate limiting

# Generate repository documentation
/docs/generate-overview
```

## Creating Custom Commands

To create a new command:

1. Create a `.md` file in an appropriate subdirectory (or create a new one)
2. Add frontmatter with description, allowed-tools, argument-hint
3. Define the orchestration workflow with phases
4. Specify which agents to use and when (parallel vs sequential)
5. Define quality gates and verdict handling
6. Document the success criteria

Custom commands appear as slash commands based on their path:
- `commands/mycommand.md` → `/mycommand`
- `commands/mytype/mycommand.md` → `/mytype/mycommand`
