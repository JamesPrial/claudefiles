# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Recommended Workflow

For non-trivial implementation, prefer the parallel wave pattern:

| Wave | Agents | Purpose |
|------|--------|---------|
| 1 | explorer + architect | Parallel analysis |
| 2 | implementer | Implementation |
| 3 | reviewer + tester | Parallel review |

**Verdict loop:**
- `APPROVE` → done
- `REQUEST_CHANGES` → retry Wave 2
- `NEEDS_DISCUSSION` → AskUserQuestion, then retry

Use TodoWrite for progress. Use AskUserQuestion when requirements are unclear.

## Structure

```
agents/           # All agents by language (typescript/, golang/, docs/)
commands/         # All commands by language
hooks/            # Automated scripts (golang/)
skills/           # Reference knowledge (golang/)
```

## Component Organization

This repository is organized by component type (agents, commands, hooks, skills) rather than by plugin. Components are grouped by language or domain within each directory.

## Key Constraints

- **TypeScript**: Launch implementer + test-writer TOGETHER (prevents reward hacking)
- **Python**: Use `python-code-writer` for writing/refactoring, `python-code-pedant` for rigorous review, `python-test-runner` for testing
- **Go**: Hooks auto-run `go fmt`/`go vet` on file changes
- **Git ops**: Require APPROVE + tests PASSED
