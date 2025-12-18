# General Utility Agents

General utility agents provide cross-language, domain-agnostic capabilities for orchestration, research, information gathering, and workflow automation. These agents enable complex multi-step tasks through specialized expertise in specific domains.

## Overview

General agents are not language-specific and serve as supporting agents for main development workflows. They handle tasks like source code analysis, web research, information synthesis, and git operations that apply across all project types.

## Available Agents

### git-ops
- **Role**: Git operations orchestrator and commit coordinator
- **Responsibility**: Manages git operations including commits, pushes, and branch management
- **Used in**: Phase 6 (finalization) of development workflow
- **Characteristics**: Handles version control coordination after code changes are approved and tested
- **Context needs**: Brief summary for commit messages, not full iteration history

### github-cli
- **Role**: GitHub API interaction and management
- **Responsibility**: Interacts with GitHub for PR management, issue handling, and repository operations
- **Used in**: PR creation, issue tracking, and repository management workflows
- **Characteristics**: Bridges Claude Code to GitHub platform features
- **Integration**: Works with gh command-line tool for API operations

### web-search
- **Role**: Web research and information gathering
- **Responsibility**: Searches the web for current information, documentation, and external context
- **Used in**: Research phases, documentation lookup, version checking
- **Characteristics**: Provides up-to-date information beyond knowledge cutoff
- **Source tracking**: Returns sources for all information gathered

### web-fact-gatherer
- **Role**: Structured information collection from web sources
- **Responsibility**: Gathers and validates factual information from web resources
- **Used in**: Requirement validation, compatibility checking, pattern research
- **Characteristics**: Focuses on accuracy and source verification
- **Output**: Structured facts with source attribution

### gh-codebase-researcher
- **Role**: Systematic codebase analysis and architecture research
- **Responsibility**: Investigates existing codebases to understand patterns, architecture, and dependencies
- **Used in**: Phase 0 (exploration) and architecture analysis phases
- **Characteristics**: Deep exploration of project structure, patterns, and conventions
- **Compared to explorer**: Works across languages, focuses on architectural patterns

### skill-decomposer
- **Role**: Task decomposition and skill requirement analysis
- **Responsibility**: Breaks down complex tasks into manageable work units
- **Used in**: Phase 1 planning and work unit definition
- **Characteristics**: Identifies prerequisite skills and optimal decomposition strategies
- **Output**: Structured work unit definitions with dependencies

## Usage Patterns

General agents are used at specific phases of the development workflow:

**Phase 0 (Exploration)**
- **gh-codebase-researcher**: Investigates existing patterns and architecture
- **web-search**: Looks up external dependencies and documentation

**Phase 1 (Planning)**
- **skill-decomposer**: Breaks down the task into work units
- **web-fact-gatherer**: Validates requirements and compatibility

**Phase 6 (Finalization)**
- **git-ops**: Manages commits and pushes
- **github-cli**: Creates PRs and manages related issues

**Ad-hoc Operations**
- **web-search**: Look up current information
- **github-cli**: Manage PRs and issues at any time

## Integration with Development Workflow

General agents support the parallel wave pattern but operate independently:

1. **Exploration Phase**: gh-codebase-researcher, web-search agents
2. **Planning Phase**: skill-decomposer, web-fact-gatherer agents
3. **Finalization Phase**: git-ops, github-cli agents
4. **Throughout**: web-search for just-in-time information gathering

## Cross-Cutting Characteristics

All general utility agents share these traits:

- **Language-agnostic**: Work across TypeScript, Go, Python, and other languages
- **Utility-focused**: Support main agents rather than directly implementing features
- **Minimal coupling**: Can be used independently or in combination
- **Read-only**: Most agents perform only read operations (except git-ops and github-cli which handle intended modifications)
- **Source attribution**: Provide clear references when gathering external information

## Context Strategy

General agents receive context appropriate to their specific role:

| Agent | Primary Context | Does NOT need |
|-------|-----------------|---------------|
| git-ops | Brief summary for commit message | Full iteration history, detailed implementation plans |
| github-cli | PR/issue specification | Implementation details, code changes |
| web-search | Specific search queries | Project code, implementation context |
| web-fact-gatherer | Topic/fact to validate | Code implementation, detailed architecture |
| gh-codebase-researcher | Task description, investigation goals | Implementation plans, review feedback |
| skill-decomposer | Task description, project constraints | Code examples, detailed architecture |

## Orchestration

General agents are typically launched by the main orchestrator agent when needed:

- **Parallel launches**: Multiple research agents can be launched together
- **Sequential launches**: git-ops follows all other phases
- **Conditional launches**: github-cli launches only when PR creation is needed

See `agents/README.md` for the complete agent ecosystem overview.
