# claudefiles

take everything here as a proof of concept, i just need a place to centralize so i can pick the best lol

I'll try to make it obvious what is or isnt human written, but definitely at least assume its all slop until proven/told otherwise, thanks

Feel free to ask any questions or suggestions tho, and, if you see any slop you want to fix, by all means, I'll probably accept it, but this isnt my `master user level .claude` or anything, at least not yet, thats actually mostly empty, here's why:

most of this this stuff is just a few prompts to make, and i was lazy and figured it was better to just keep remaking them project level, so i can collect them and compare. that's what this is for, or will be for, at the moment

i have no idea which one's the best, and im gonna have to resolve naming collisions probably, but, i think it's safe to say i'm already over-engineering the canonical truth of slop, so, enjoy!

---

## What's Here

Claude Code configuration files: agents, commands, hooks, and skills for software development workflows.

### Structure

```
claudefiles/
├── agents/
│   ├── general/     (6 agents: git-ops, github-cli, web-search, etc.)
│   ├── golang/      (5 agents: architect, explorer, implementer, optimizer, reviewer)
│   ├── python/      (4 agents: code-writer, code-pedant, test-runner, slash-command-architect)
│   ├── typescript/  (5 agents: craftsman, code-reviewer, test-architect, test-runner, quick-impl)
│   └── docs/        (1 agent: docs-architect)
├── commands/
│   ├── docs/        (generate-overview.md)
│   ├── golang/      (implement.md)
│   └── typescript/  (implement.md)
├── hooks/
│   ├── golang/      (go-fmt.sh, go-vet.sh, go-precommit.sh)
│   └── security/    (check-secrets.py)
└── skills/
    └── golang/      (6 categories with nested sub-skills)
        ├── concurrency/   (channels, context, goroutines, sync)
        ├── errors/        (checking, sentinel, wrapping)
        ├── interfaces/    (design, embedding, pollution)
        ├── linting/       (golangci, staticcheck, vet)
        ├── nil/           (interface, map, pointer, slice)
        └── testing/       (benchmarks, helpers, subtests, table)
```

### Components

- **agents/**: Specialized AI assistants by language/domain. `general/` contains cross-language utilities (git, GitHub, web search). Language dirs contain implementation, review, and testing agents.

- **commands/**: Slash commands for workflow automation (`/golang/implement`, `/typescript/implement`, `/docs/generate-overview`)

- **hooks/**: Event-driven scripts that auto-run on tool use. `golang/` runs `go fmt`/`go vet` on file changes. `security/` scans for leaked secrets.

- **skills/**: Reference knowledge as nested SKILL.md files. Currently Go patterns only.

### Usage

Copy to `.claude/` at project or user level. See `CLAUDE.md` for the recommended parallel wave workflow.
