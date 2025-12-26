# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a collection of reusable Claude Code configurations (agents, commands, hooks, skills). Copy components to your `.claude/` directory at project or user level.

## Recommended Workflow

For non-trivial implementation, use the parallel wave pattern:

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

## Testing Hooks Locally

```bash
# Go hooks - run from hooks/golang/
echo '{"tool_input":{"file_path":"test.go"}}' | ./scripts/go-fmt.sh
echo '{"tool_input":{"file_path":"test.go"}}' | ./scripts/go-vet.sh
echo '{"tool_input":{"command":"git commit"}}' | ./scripts/go-precommit.sh

# Security hooks - run from hooks/security/
echo '{"tool_input":{"command":"git commit"}}' | python3 ./scripts/check_secrets.py

# Exit codes: 0 = pass, 2 = block operation
```

## Hook Configuration

Hooks are defined in `hooks.json` files. Key events:
- `PostToolUse Write` → runs after file creation (e.g., `go fmt`)
- `PostToolUse Edit` → runs after file edit (e.g., `go vet`)
- `PreToolUse Bash` → runs before shell commands (e.g., pre-commit checks)

Scripts receive tool input as JSON on stdin, must exit 0 to allow or 2 to block.

## Language-Specific Agents

| Language | Implementation | Review | Testing |
|----------|---------------|--------|---------|
| **Go** | implementer | reviewer, optimizer | (integrated) |
| **TypeScript** | craftsman | code-reviewer | test-architect, test-runner |
| **Python** | code-writer | code-pedant | test-runner |

Cross-language utilities in `agents/general/`: git-ops, github-cli, web-search, web-fact-gatherer, gh-codebase-researcher, skill-decomposer.

## Key Constraints

- **TypeScript**: Launch craftsman + test-architect TOGETHER (prevents reward hacking)
- **Python**: Use `code-writer` for writing/refactoring, `code-pedant` for rigorous review, `test-runner` for testing
- **Go**: Hooks auto-run `go fmt`/`go vet` on file changes; pre-commit runs `golangci-lint`
- **Git ops**: Require APPROVE + tests PASSED
- **Security**: Pre-commit hook scans for API keys, tokens, and hardcoded secrets
