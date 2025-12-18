# Skills

Skills are specialized knowledge modules that agents can load to enhance their expertise in specific domains. Each skill provides focused, reference-quality information that helps agents understand patterns, best practices, and common pitfalls.

## What Are Skills?

Skills serve as compact, focused knowledge bases that agents consult when working on domain-specific tasks. Unlike general documentation, skills are:

- **Curated**: Hand-selected patterns and practices that matter most
- **Actionable**: Focused on what to do (and what not to do)
- **Contextual**: Organized around common problem domains
- **Reusable**: Loaded on-demand by multiple agents

Think of skills as expert reference cards that agents can pull up when they need deep knowledge in a specific area.

## Organization Pattern

Skills follow a nested `SKILL.md` pattern for hierarchical organization:

```
skills/
├── README.md              # This file
├── golang/
│   ├── SKILL.md          # Overview of Go skills
│   ├── concurrency/
│   │   └── SKILL.md      # Goroutines, channels, patterns
│   ├── errors/
│   │   └── SKILL.md      # Error handling patterns
│   └── ...
└── other-domains/
    └── ...
```

Each `SKILL.md` file contains:
- Key concepts and terminology
- Common patterns and anti-patterns
- Best practices specific to that domain
- Code examples demonstrating the concepts

## Golang Skills Index

### concurrency/
Patterns for concurrent programming in Go:
- Goroutines lifecycle and management
- Channels (buffered/unbuffered, direction)
- Context for cancellation and deadlines
- Sync primitives (Mutex, RWMutex, WaitGroup)
- Common concurrency patterns (worker pools, fan-in/fan-out)

### errors/
Error handling patterns and practices:
- Error wrapping with `fmt.Errorf` and `%w`
- Sentinel errors for known conditions
- Custom error types
- Error checking patterns
- Error propagation strategies

### interfaces/
Interface design and usage:
- Small, focused interface design
- Interface embedding and composition
- Accepting interfaces, returning structs
- Avoiding interface pollution
- Common standard library interfaces

### nil/
Understanding nil in different Go types:
- Nil pointers and dereferencing safety
- Nil maps (read-safe, write-panic)
- Nil slices vs empty slices
- Nil interfaces (type vs value)
- Safe nil handling patterns

### testing/
Testing patterns and practices:
- Table-driven tests
- Subtests with `t.Run()`
- Test helpers and `t.Helper()`
- Benchmarks and profiling
- Test organization and naming

### linting/
Static analysis and code quality:
- golangci-lint configuration and usage
- staticcheck for bug detection
- go vet for suspicious constructs
- Common linter rules and fixes
- CI/CD integration patterns

## Using Skills

Agents can load skills by referencing them in their configuration. When a skill is loaded, the agent has immediate access to all the patterns and practices defined in that skill's `SKILL.md` file.

For nested skills (like `golang/concurrency`), agents can load either:
- The parent skill (`golang/SKILL.md`) for broad coverage
- Specific child skills (`golang/concurrency/SKILL.md`) for focused expertise
