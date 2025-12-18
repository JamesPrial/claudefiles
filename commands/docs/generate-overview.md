# Generate Repository Overview

Analyze the current repository structure and generate a comprehensive AI-generated overview section for the README.md file.

## Instructions

1. **Explore the repository structure**:
   - List all top-level directories and their purposes
   - Identify key configuration files (.claude/, plugins, package.json, etc.)
   - Scan for agents, commands, skills, hooks, and other Claude Code components

2. **Analyze the codebase**:
   - Read key files to understand the project's purpose
   - Identify programming languages and frameworks used
   - Understand the organization patterns (agents/, commands/, skills/, etc.)

3. **Generate the documentation**:
   - Create a "What's Here" or similar section header
   - Include a brief introduction to the repository
   - Document the directory structure with descriptions
   - Explain each major component (agents, commands, skills, plugins)
   - Add usage notes if applicable
   - Keep the tone professional and informative

4. **Update the README.md**:
   - Find the existing README.md file
   - Add the AI-generated overview section after any human-written introduction
   - Use a clear separator (like `---`) before the AI-generated content
   - Preserve all existing content
   - Format using proper Markdown

5. **Review and commit**:
   - Show the user what was added
   - If requested, commit the changes with a descriptive message

## Output Format

The generated overview should include:

```markdown
---

## What's Here (AI-generated summary)

[Brief introduction paragraph]

### Structure

- **directory-name/**: Description
  - `file.md`: Specific file description
  - Additional subdirectories and key files

### Usage

[Information about how to use these files]
```

## Notes

- Focus on Claude Code-specific components (agents, commands, skills, hooks)
- Be descriptive but concise
- Maintain consistency with existing documentation style
- Don't duplicate information that's already in the README
