# claudefiles

take everything here as a proof of concept, i just need a place to centralize so i can pick the best lol

I'll try to make it obvious what is or isnt human written, but definitely at least assume its all slop until proven/told otherwise, thanks

Feel free to ask any questions or suggestions tho, and, if you see any slop you want to fix, by all means, I'll probably accept it, but this isnt my `master user level .claude` or anything, at least not yet, thats actually mostly empty, here's why:

most of this this stuff is just a few prompts to make, and i was lazy and figured it was better to just keep remaking them project level, so i can collect them and compare. that's what this is for, or will be for, at the moment

i have no idea which one's the best, and im gonna have to resolve naming collisions probably, but, i think it's safe to say i'm already over-engineering the canonical truth of slop, so, enjoy!

---

## What's Here (AI-generated summary)

This repository contains Claude Code configuration files, agents, commands, and skills for software development workflows.

### Structure

The repository now follows a component-first organization:

```
claudefiles/
├── agents/
│   ├── typescript/  (5 agents)
│   │   ├── quick-impl.md
│   │   ├── ts-test-runner.md
│   │   ├── typescript-code-reviewer.md
│   │   ├── typescript-craftsman.md
│   │   └── typescript-test-architect.md
│   ├── golang/      (5 agents)
│   │   ├── go-architect.md
│   │   ├── go-explorer.md
│   │   ├── go-implementer.md
│   │   ├── go-optimizer.md
│   │   └── go-reviewer.md
│   └── docs/        (1 agent)
│       └── readme-commit-agent.md
├── commands/
│   ├── typescript/  (1 command)
│   │   └── implement.md
│   ├── golang/      (1 command)
│   │   └── go-workflow.md
│   └── docs/        (1 command)
│       └── readme-docs-commit.md
├── hooks/
│   └── golang/      (hooks.json + 3 scripts)
│       ├── hooks.json
│       ├── go-fmt-on-save.sh
│       ├── go-vet-on-save.sh
│       └── go-test-on-commit.sh
└── skills/
    └── golang/      (6 categories, nested SKILL.md)
        ├── testing/
        ├── error-handling/
        ├── interfaces/
        ├── nil-handling/
        ├── concurrency/
        └── context/
```

#### Components

- **agents/**: Development agents organized by language/domain
  - **typescript/**: TypeScript implementation, testing, and review agents
  - **golang/**: Go architecture, exploration, implementation, optimization, and review agents
  - **docs/**: Documentation-focused agents

- **commands/**: Custom slash commands for workflow automation
  - **typescript/**: TypeScript implementation workflows
  - **golang/**: Go development workflows
  - **docs/**: Documentation commit workflows

- **hooks/**: Event-driven automation scripts
  - **golang/**: Go-specific hooks for formatting, vetting, and testing

- **skills/**: Best practices and patterns organized by language
  - **golang/**: Comprehensive Go patterns including testing, error handling, interfaces, nil handling, concurrency, and context management

### Usage

These files are meant to be used with Claude Code's agent, command, and skill systems. They can be placed in project-level `.claude/` directories or at the user level for global access.
