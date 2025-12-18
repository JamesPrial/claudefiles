# Python Agents

Python agents provide specialized capabilities for Python development workflows, including code implementation, code review, test execution, and command orchestration.

## Overview

Python agents follow the same wave pattern coordination as other language agents, enabling parallel execution and focused responsibility areas within Python development tasks.

## Available Agents

### code-writer
- **Role**: Careful implementation with attention to code quality
- **Responsibility**: Writes Python code following best practices and project conventions
- **Used in**: Phase 2 (implementation) of development workflow
- **Characteristics**: Prioritizes readability, maintainability, and adherence to Python standards

### code-pedant
- **Role**: Detailed code review with focus on quality standards
- **Responsibility**: Reviews Python code for correctness, style, patterns, and potential issues
- **Used in**: Phase 3 (review) of development workflow
- **Focus areas**: Code patterns, Python idioms, error handling, type hints, documentation

### test-runner
- **Role**: Test execution specialist for Python test suites
- **Responsibility**: Executes Python tests and reports results clearly
- **Used in**: Phase 3 (validation) of development workflow
- **Characteristics**: Minimal context, focused on test execution and result reporting only

### slash-command-architect
- **Role**: Command design and orchestration for CLI operations
- **Responsibility**: Designs and implements slash commands for Claude Code integration
- **Used in**: Workflow orchestration and user-facing CLI features
- **Characteristics**: Bridges user intent to specialized agent capabilities

## Usage Pattern

Python agents are coordinated by an orchestrator agent following the parallel wave pattern:

1. **Wave 1**: Exploration and analysis agents examine requirements and codebase
2. **Wave 2**: Parallel implementation with code-writer agent
3. **Wave 3**: Parallel review with code-pedant and test-runner agents

## Integration with Workflow

These agents integrate into the standard development workflow defined in CLAUDE.md:

- **code-writer** and test agents are launched together to prevent reward hacking
- **code-pedant** groups related code changes for efficient review
- **test-runner** provides clean test results without polluting main context
- **slash-command-architect** enables user-facing automation through command interfaces

## Context Strategy

Each agent is provided with minimal, focused context:

| Agent | Needs | Does NOT need |
|-------|-------|---------------|
| code-writer | Implementation plan, file locations, specific feedback | Full reviewer output, test logs |
| code-pedant | Files changed, summary of changes | Full plan, test output |
| test-runner | Nothing beyond "run tests" | Any context—just run and report |
| slash-command-architect | Command specification and use cases | Implementation details, test output |

## Cross-Language Comparison

| Role | TypeScript | Go | Python | Documentation |
|------|------------|----|--------|--------------|
| **Implementation** | craftsman, quick-impl | implementer | code-writer | - |
| **Review** | code-reviewer | reviewer | code-pedant | - |
| **Testing** | test-architect, test-runner | - | test-runner | - |
| **Commands** | - | - | slash-command-architect | docs-architect |

See `agents/README.md` for the complete cross-language agent overview.
