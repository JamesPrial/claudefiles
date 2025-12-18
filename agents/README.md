# Agents

Agents are specialized AI assistants designed to handle specific aspects of software development workflows. Each agent has a focused role and domain expertise, enabling parallel execution of complex tasks through the wave pattern workflow.

## Overview

Agents work together in coordinated waves:
- **Wave 1**: Exploration and architecture (parallel analysis)
- **Wave 2**: Implementation
- **Wave 3**: Review and testing (parallel validation)

This structure allows Claude Code to tackle complex tasks efficiently by delegating specialized work to purpose-built agents.

## Cross-Language Comparison

| Role | TypeScript | Go | Python | General |
|------|------------|----|---------| --------|
| **Exploration** | - | explorer | - | gh-codebase-researcher |
| **Architecture** | - | architect | slash-command-architect | skill-decomposer |
| **Implementation** | craftsman, quick-impl | implementer | code-writer | - |
| **Review** | code-reviewer | reviewer | code-pedant | - |
| **Testing** | test-architect, test-runner | - | test-runner | - |
| **Optimization** | - | optimizer | - | - |
| **Git/GitHub** | - | - | - | git-ops, github-cli |
| **Web/Research** | - | - | - | web-search, web-fact-gatherer |

## Available Agents

### TypeScript (`typescript/`)

- **craftsman** - Careful implementation with attention to code quality
- **code-reviewer** - Reviews TypeScript code for quality, patterns, and issues
- **test-architect** - Designs comprehensive test strategies
- **test-runner** - Executes and validates test suites
- **quick-impl** - Rapid prototyping and implementation

### Go (`golang/`)

- **explorer** - Analyzes codebases and investigates requirements
- **architect** - Designs system architecture and interfaces
- **implementer** - Implements Go code following best practices
- **reviewer** - Reviews Go code for correctness and style
- **optimizer** - Performance analysis and optimization

### Documentation (`docs/`)

- **docs-architect** - Structures and creates comprehensive documentation

### Python (`python/`)

- **code-writer** - Clean, simple Python implementation following PEP 8 and Zen of Python
- **code-pedant** - Rigorous code review focused on type safety and eliminating AI sloppiness
- **test-runner** - Executes Python tests and reports only failures and errors
- **slash-command-architect** - Designs type-safe Python scripts for Claude Code slash commands

### General Utilities (`general/`)

- **git-ops** - Git operations specialist for commits, branches, and repo management
- **github-cli** - GitHub CLI operations for PRs, issues, and repository tasks
- **web-search** - Web search for factual information and documentation
- **web-fact-gatherer** - Gathers structured data from web sources as JSON
- **gh-codebase-researcher** - Researches open-source implementations via GitHub
- **skill-decomposer** - Decomposes complex skills into efficient, layered components

## Usage

Agents are invoked through the parallel wave pattern defined in `CLAUDE.md`. Use TodoWrite to track progress across agent workflows, and leverage parallel execution when agents have no dependencies.

See individual agent files for detailed role descriptions and capabilities.
