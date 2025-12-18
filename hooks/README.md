# Hooks

Hooks are automated scripts that run in response to tool use events in Claude Code. They enable enforcement of code quality standards, automated formatting, linting, and pre-commit checks without manual intervention.

## What Are Hooks?

Hooks are shell scripts triggered automatically when agents use specific tools:
- **PreToolUse**: Runs before a tool executes (e.g., pre-commit checks)
- **PostToolUse**: Runs after a tool completes (e.g., auto-formatting)

Hooks receive tool input via stdin as JSON and can:
- Validate or transform file operations
- Run linters and formatters automatically
- Enforce quality gates before commits
- Exit with non-zero status to block the operation

## Configuration

Hooks are configured via `hooks.json`:

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "matcher": "Write",
      "script": "./scripts/go-fmt.sh"
    }
  ]
}
```

Fields:
- **event**: When to trigger (`PreToolUse` or `PostToolUse`)
- **matcher**: Which tool to match (`Write`, `Edit`, `Bash`, etc.)
- **script**: Path to the shell script to execute (relative to hooks directory)

## Available Hooks

### Go Development Hooks

The `golang/` directory contains hooks for Go code quality:

#### **`scripts/go-fmt.sh`**
- **Trigger**: After `Write` tool use
- **Purpose**: Automatically format Go files with `go fmt`
- **Behavior**:
  - Extracts `file_path` from tool input JSON
  - Checks if file ends with `.go`
  - Runs `go fmt` on the file
  - Exits with status 2 if formatting fails

```bash
# Example trigger
Write(file_path="/path/to/main.go", content="package main...")
# → Automatically runs: go fmt /path/to/main.go
```

#### **`scripts/go-vet.sh`**
- **Trigger**: After `Edit` tool use
- **Purpose**: Run static analysis on edited Go code
- **Behavior**:
  - Extracts `file_path` from tool input JSON
  - Checks if file ends with `.go`
  - Runs `go vet ./...` on the entire package
  - Reports issues to stderr and exits with status 2 if vet fails

```bash
# Example trigger
Edit(file_path="/path/to/handler.go", old_string="...", new_string="...")
# → Automatically runs: cd /path/to && go vet ./...
```

#### **`scripts/go-precommit.sh`**
- **Trigger**: Before `Bash` tool use (when command contains "git commit")
- **Purpose**: Run `golangci-lint` before allowing commits
- **Behavior**:
  - Extracts `command` from tool input JSON
  - Checks if command matches `git commit` pattern
  - Runs `golangci-lint run` if available
  - Blocks commit (exit 2) if linting issues are found
  - Gracefully skips if `golangci-lint` is not installed

```bash
# Example trigger
Bash(command="git commit -m 'Add feature'")
# → Automatically runs: golangci-lint run
# → If linting passes, commit proceeds
# → If linting fails, commit is blocked
```

## Hook Configuration

**Location**: `hooks/golang/hooks.json`

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "matcher": "Write",
      "script": "./scripts/go-fmt.sh"
    },
    {
      "event": "PostToolUse",
      "matcher": "Edit",
      "script": "./scripts/go-vet.sh"
    },
    {
      "event": "PreToolUse",
      "matcher": "Bash",
      "script": "./scripts/go-precommit.sh"
    }
  ]
}
```

## Hook Script Structure

All hooks follow a consistent pattern:

```bash
#!/bin/bash
set -euo pipefail

# 1. Read stdin (contains tool input as JSON)
input=$(cat)

# 2. Extract relevant fields using jq (with grep fallback)
if command -v jq &> /dev/null; then
    field=$(echo "$input" | jq -r '.field_name // empty')
else
    field=$(echo "$input" | grep -oP '"field_name"\s*:\s*"\K[^"]+' || echo "")
fi

# 3. Validate or filter (exit 0 if not applicable)
if [ -z "$field" ]; then
    exit 0
fi

# 4. Execute the actual operation
if ! output=$(some-command 2>&1); then
    echo "Error message" >&2
    echo "$output" >&2
    exit 2  # Non-zero blocks the operation
fi

exit 0  # Success
```

## Exit Codes

- **0**: Success, operation proceeds
- **1**: Standard error (operation typically proceeds)
- **2**: Failure, operation is blocked (for PreToolUse) or reported (for PostToolUse)

## Benefits of Hooks

1. **Automatic enforcement**: No need to remember to run formatters/linters
2. **Consistency**: All code changes follow the same quality standards
3. **Fast feedback**: Issues caught immediately when files are modified
4. **Integration**: Works seamlessly with agent workflows
5. **Prevention**: Pre-commit hooks block bad commits before they happen

## Creating Custom Hooks

To create a new hook:

1. **Create a shell script** in the appropriate `scripts/` directory:
   ```bash
   #!/bin/bash
   set -euo pipefail

   input=$(cat)
   # Extract fields and implement logic
   # Exit 0 for success, 2 for failure
   ```

2. **Make it executable**:
   ```bash
   chmod +x scripts/my-hook.sh
   ```

3. **Register in hooks.json**:
   ```json
   {
     "event": "PostToolUse",
     "matcher": "Write",
     "script": "./scripts/my-hook.sh"
   }
   ```

4. **Test it**: Trigger the tool and verify the hook runs

## Hook Best Practices

- **Fast execution**: Hooks should complete quickly to avoid blocking agents
- **Clear error messages**: Report what failed and how to fix it
- **Graceful degradation**: Handle missing tools (like `jq` or `golangci-lint`)
- **Selective matching**: Only process relevant files (e.g., check file extension)
- **Idempotent**: Safe to run multiple times on the same input
- **Silent success**: Only output on errors (stderr)

## Debugging Hooks

If a hook isn't working:

1. Check the JSON configuration is valid
2. Verify the script path is correct (relative to hooks directory)
3. Ensure the script is executable (`chmod +x`)
4. Test the script manually with sample JSON input:
   ```bash
   echo '{"file_path": "/path/to/file.go"}' | ./scripts/go-fmt.sh
   ```
5. Check stderr output for error messages

## Integration with Commands

Hooks work automatically during command execution:

```bash
/golang/implement Add user service

# During implementation:
# - Write tool creates main.go → go-fmt.sh runs automatically
# - Edit tool modifies handler.go → go-vet.sh runs automatically
# - git commit triggered → go-precommit.sh runs automatically
```

The combination of commands (orchestration) + hooks (quality enforcement) ensures high-quality code without manual intervention.
