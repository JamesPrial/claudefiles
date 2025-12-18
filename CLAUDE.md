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
agents/           # TypeScript agents
commands/         # Slash commands
golang-workflow/  # Go plugin (agents, commands, hooks, skills)
readme-docs/      # Documentation plugin
```

## Plugin Format

`.claude-plugin/plugin.json` + `agents/` + `commands/` + optional `skills/`, `hooks/`

## Key Constraints

- **TypeScript**: Launch implementer + test-writer TOGETHER (prevents reward hacking)
- **Go**: Hooks auto-run `go fmt`/`go vet` on file changes
- **Git ops**: Require APPROVE + tests PASSED
