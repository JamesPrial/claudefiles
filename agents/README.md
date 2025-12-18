# Agents

Agents are specialized AI assistants designed to handle specific aspects of software development workflows. Each agent has a focused role and domain expertise, enabling parallel execution of complex tasks through the wave pattern workflow.

## Overview

Agents work together in coordinated waves:
- **Wave 1**: Exploration and architecture (parallel analysis)
- **Wave 2**: Implementation
- **Wave 3**: Review and testing (parallel validation)

This structure allows Claude Code to tackle complex tasks efficiently by delegating specialized work to purpose-built agents.

## Cross-Language Comparison

| Role | TypeScript | Go | Documentation |
|------|------------|----|--------------|
| **Exploration** | - | explorer | - |
| **Architecture** | - | architect | docs-architect |
| **Implementation** | craftsman, quick-impl | implementer | - |
| **Review** | code-reviewer | reviewer | - |
| **Testing** | test-architect, test-runner | - | - |
| **Optimization** | - | optimizer | - |

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

## Usage

Agents are invoked through the parallel wave pattern defined in `CLAUDE.md`. Use TodoWrite to track progress across agent workflows, and leverage parallel execution when agents have no dependencies.

See individual agent files for detailed role descriptions and capabilities.
