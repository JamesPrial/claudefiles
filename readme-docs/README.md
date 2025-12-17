# README Documentation Generator Plugin

Automated repository documentation generator that creates AI-generated README overviews, structure summaries, and usage guides for your codebase.

## What This Plugin Does

This plugin was created by converting commit `5a70b39` (docs: add AI-generated repository overview to README) into a reusable Claude Code plugin. Instead of manually generating repository documentation, you can now use this plugin to automatically:

- Analyze your repository structure
- Generate comprehensive overviews of your codebase
- Document directory structures and file purposes
- Create "What's Here" sections for READMEs
- Identify and explain Claude Code components (agents, commands, skills, plugins)

## Installation

### From This Repository

```bash
# Copy the plugin to your Claude Code plugins directory
cp -r readme-docs ~/.config/claude-code/plugins/

# Or install via Claude Code
/plugin install /path/to/readme-docs
```

### Usage

The plugin provides two main ways to generate documentation:

#### 1. Using the Command

```bash
/generate-overview
```

This command will:
1. Explore your repository structure
2. Analyze Claude Code components
3. Generate a comprehensive overview
4. Add it to your README.md

#### 2. Using the Agent Directly

Ask Claude to use the `docs-architect` agent:

```
"Can you use the docs-architect agent to generate documentation for this repository?"
```

The agent will systematically analyze your codebase and create structured documentation.

## What Gets Generated

The plugin creates documentation sections like:

```markdown
---

## What's Here (AI-generated summary)

[Brief introduction to your repository]

### Structure

- **directory-name/**: Description of directory purpose
  - `file.md`: Description of specific files
  - Subdirectory information

### Usage

[How to use the files and components in the repository]
```

## Components

### Commands

- **`/generate-overview`**: Main command for generating repository documentation

### Agents

- **`docs-architect`**: Specialized agent for repository analysis and documentation generation
  - Explores repository structure systematically
  - Generates well-formatted Markdown documentation
  - Integrates cleanly with existing READMEs

## Example Output

This plugin generated the documentation you saw in commit `5a70b39`, which included:

- Overview of the repository structure
- Descriptions of agents, commands, and plugins
- Categorized file listings
- Usage information for Claude Code components

## Features

- **Smart Analysis**: Automatically detects Claude Code components, programming languages, and project structure
- **Clean Integration**: Adds AI-generated sections with clear separators
- **Preserves Content**: Never modifies existing documentation
- **Customizable**: Follow existing documentation style and conventions
- **Professional Output**: Clear, structured, scannable documentation

## Origin

This plugin was created by converting the commit that added AI-generated repository overview functionality into a reusable plugin format. The original commit:

```
commit 5a70b39016e004e6a637e1339a55fd8ccf4ed5d2
Author: Claude <noreply@anthropic.com>
Date:   Wed Dec 17 07:02:59 2025 +0000

    docs: add AI-generated repository overview to README

    Add structured documentation under human introduction explaining the
    current repository contents including TypeScript agents, commands,
    and the comprehensive Go development workflow plugin.
```

## License

MIT

## Author

James Prial

## Keywords

`readme`, `documentation`, `repository`, `overview`, `generator`, `ai-docs`
