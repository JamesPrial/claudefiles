---
name: package
description: Package claudefiles components into a Claude Code plugin
allowed-tools: Read, Glob, Write, Bash, TodoWrite, AskUserQuestion
---

# /plugin/package

Package this repository as a Claude Code plugin.

## Workflow

1. **Determine scope**: Ask user for full package or subset (Go, TypeScript, Python, Security)

2. **Create structure**:
   - Create `.claude-plugin/` directory
   - Generate `plugin.json` manifest

3. **Validate**:
   - Ensure all hook scripts are executable
   - Verify all paths exist
   - Test with `claude plugin install . --scope local`

## Usage

```
/plugin/package              # Interactive - asks what to include
/plugin/package --full       # Full repo package
/plugin/package --go         # Go components only
/plugin/package --typescript # TypeScript components only
```

## Skills Used

- plugin-packager (core packaging)
- plugin-packager/subset (language subsets)
- plugin-packager/hooks (hook handling)
- plugin-packager/validation (error fixes)
