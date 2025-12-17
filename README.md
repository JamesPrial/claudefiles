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

- **agents/**: TypeScript-focused development agents
  - `quick-impl.md`: Fast implementation agent
  - `ts-test-runner.md`: TypeScript test execution agent
  - `typescript-code-reviewer.md`: Code review agent for TypeScript
  - `typescript-craftsman.md`: TypeScript implementation specialist
  - `typescript-test-architect.md`: Test design and architecture agent

- **commands/**: Custom slash commands
  - `implement.md`: Implementation command workflow

- **golang-workflow/**: Complete Go development plugin
  - **agents/**: Go-specific agents (architect, explorer, implementer, optimizer, reviewer)
  - **commands/**: Go workflow commands
  - **skills/**: Organized Go best practices and patterns
    - Testing (table tests, subtests, benchmarks, helpers)
    - Error handling (wrapping, checking, sentinel errors)
    - Interfaces (design, embedding, avoiding pollution)
    - Nil handling (pointers, maps, slices, interfaces)
    - Concurrency (goroutines, channels, context, sync primitives)

### Usage

These files are meant to be used with Claude Code's agent, command, and skill systems. They can be placed in project-level `.claude/` directories or at the user level for global access.
