# Security Hooks

Security hooks are automated scripts that run during tool operations to detect and prevent accidental exposure of sensitive information, credentials, and secrets in committed code.

## What Are Security Hooks?

Security hooks are PreToolUse hooks triggered before git operations to scan staged files for potential secrets, API keys, credentials, and sensitive data. They act as a final security gate before code is committed to the repository.

## Available Hooks

### check-secrets.py
- **Trigger**: Before `Bash` tool use (when command contains "git commit")
- **Purpose**: Detect hardcoded secrets, credentials, and API keys before committing
- **Language**: Python 3
- **Exit Code**: 0 (pass), 2 (block commit or error)
- **Fail-Closed**: Exits with code 2 on errors to ensure safety

## check-secrets.py Detailed Behavior

### Detection Methods

The hook uses two complementary detection strategies:

#### 1. Pattern-Based Detection
Scans for common secret patterns (using pre-compiled regex for performance):
- AWS credentials (`aws_access_key_id`, `AKIA[0-9A-Z]{16}` for Access Key ID, `aws_secret_access_key`)
- OpenAI API keys (`sk-[alphanumeric]{20,}`)
- Google API keys (`AIza[alphanumeric]{35}`)
- GitHub Personal Access Tokens (`ghp_[alphanumeric]{36}`)
- Slack tokens (`xox[baprs]-[alphanumeric]{10,48}`)
- Stripe API keys (`sk_live_[alphanumeric]{20,}` and `pk_live_[alphanumeric]{20,}`)
- SendGrid API keys (`SG\.[alphanumeric]{60,}`)
- Anthropic API keys (`sk-ant-[alphanumeric]{20,}`)
- Bearer tokens (`bearer [alphanumeric]{20,}`)
- Generic secrets/tokens (20+ character strings)
- Private keys (RSA, DSA key headers)
- Database connection strings (postgresql://, mysql://, mongodb://, etc.)

#### 2. Hardcoded .env Value Detection
- Parses `.env` file for environment variable values
- Filters to only check potentially sensitive values (8+ characters, non-boolean, non-null)
- Searches staged files for exact matches using word boundaries to reduce false positives
- Reads from git staging area (not disk) to ensure correct file state at commit time (TOCTOU fix)
- Reports when environment variables are hardcoded instead of referenced at runtime

### Processing Pipeline

```
1. Extract tool operation (Bash command with "git commit")
2. Validate file size limits (10MB max per file)
3. Parse .env file (if present)
4. Get list of staged files (from git diff --cached)
5. For each staged file:
   - Skip binary files (.png, .jpg, .gif, .pdf, .zip)
   - Skip .env files themselves
   - Skip files exceeding 10MB limit
   - Read content from git staging area (not disk)
   - Check content against pre-compiled secret patterns
   - Check content against hardcoded .env values (with word boundaries)
6. If secrets found:
   - Report all findings with line numbers and context
   - Block commit (exit 2)
   - Provide remediation guidance
7. Exit with code 2 on any errors (fail-closed behavior)
```

### Smart Filtering

The hook filters out false positives:

**Non-Secret Values Skipped:**
- Boolean values: `true`, `false`, `yes`, `no`, `on`, `off`
- Environment names: `development`, `production`, `staging`, `test`
- Common URLs: `localhost`, `127.0.0.1`, `0.0.0.0`
- Encodings: `utf-8`, `utf8`, `none`, `null`

**Value-Length Filtering:**
- Only checks values 8+ characters long
- Short values unlikely to be secrets
- Numeric-only values skipped

**File Filtering:**
- Binary files skipped (extensions: `.png`, `.jpg`, `.jpeg`, `.gif`, `.pdf`, `.zip`)
- `.env` files themselves always skipped (they're supposed to contain secrets)

### Output Format

When secrets are detected, the hook provides structured error output:

```
🚨 SECURITY WARNING: Potential secrets detected in staged files!

  Pattern-based detections:
    ❌ path/to/file.js:42 - Found potential GitHub Personal Access Token
    ❌ config/api.ts:15 - Found potential OpenAI API key

  Hardcoded .env values detected:
    ❌ src/config.py:8 - Found hardcoded value from .env key 'DATABASE_PASSWORD'
    ❌ handlers/auth.go:23 - Found hardcoded value from .env key 'API_SECRET'

⚠️  Please remove secrets before committing.
💡 Use environment variables at runtime instead of hardcoding values from .env.
💡 Consider using a secrets manager for sensitive credentials.
```

## Security Patterns Detected

### Credentials & Tokens
- AWS access keys (AKIA format) and secret keys
- OpenAI API keys (sk- prefix)
- Google API keys (AIza prefix)
- GitHub Personal Access Tokens (ghp_ prefix)
- Slack tokens (xox[baprs] prefix)
- Stripe API keys (sk_live_ and pk_live_ prefixes)
- SendGrid API keys (SG. prefix)
- Anthropic API keys (sk-ant- prefix)
- Bearer tokens in code

### Key Material
- Private keys (RSA, DSA format)
- Database connection strings (postgresql://, mysql://, mongodb://, etc.)
- Any string matching "secret" or "token" pattern with 20+ characters

### Hardcoded Environment Values
- Values from `.env` file embedded directly in source code
- Encourages use of environment variables instead
- Uses word boundaries to reduce false positives

## Hook Configuration

**Location**: `hooks/security/hooks.json` (when configured)

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "matcher": "Bash",
      "script": "./scripts/check-secrets.py"
    }
  ]
}
```

**Hook Trigger Condition:**
- **Event**: PreToolUse (before tool executes)
- **Matcher**: Bash tool
- **Command Filter**: Only triggers when command contains "git commit"

## Exit Codes

- **0**: No secrets detected, commit proceeds
- **2**: Secrets detected, commit is blocked; or error encountered (fail-closed behavior)

## Usage Example

Normal commit (no secrets):
```bash
# User: git commit -m "Add feature"
# → check-secrets.py runs automatically
# → No secrets found
# → Commit proceeds (exit 0)
```

Commit blocked (secrets detected):
```bash
# User: git commit -m "Add API integration"
# → check-secrets.py runs automatically
# → Hardcoded API key found in src/api.py:42
# → Commit blocked (exit 2)
# → User sees security warning with details
# → User must remove secret and try again
```

## Environment Variables

The hook respects these environment variables:

- **CLAUDE_PROJECT_DIR**: Project root directory for .env file lookup

## Remediation Guidance

When the hook detects secrets, users should:

1. **Remove the hardcoded secret** from the file
2. **Use environment variables** instead:
   ```python
   import os
   api_key = os.getenv("API_KEY")
   ```
3. **Ensure secrets are in .env** (only .env is in .gitignore)
4. **Use a secrets manager** for production environments
5. **Try the commit again** after remediation

## Security Best Practices

### For Developers

1. **Never hardcode secrets**: Use environment variables
2. **Check .env is gitignored**: Verify in `.gitignore`
3. **Use separate credentials**: Never share API keys between environments
4. **Rotate exposed secrets**: If accidentally committed, regenerate credentials
5. **Document secret requirements**: List required environment variables in README

### For CI/CD

1. **Inject secrets at deploy time**: Use CI/CD secrets management
2. **Scan commit history**: Use `git-secrets` or similar for existing repos
3. **Automate secret detection**: Enable hooks in development workflows
4. **Audit secret access**: Log who accesses what secrets

## Integration with Development Workflow

The hook runs automatically during development without manual intervention:

```bash
# During any git commit operation
git commit -m "Feature X"
→ check-secrets.py runs pre-commit
→ Secrets detected? Block commit and show warnings
→ No secrets? Commit proceeds normally
```

## Performance Optimizations

The hook is designed for efficiency:

- **Pre-compiled regex patterns**: All patterns compiled once at startup for faster matching
- **File size limits**: Skips files over 10MB to prevent performance degradation
- **Early exits**: Stops scanning after finding issues to minimize processing
- **Efficient staging area access**: Reads directly from git staging area (faster than disk I/O)
- **Type hints**: Comprehensive type annotations for better code clarity and maintainability

## Limitations

The hook makes best-effort attempts but has limitations:

- **Cannot catch all secrets**: Sophisticated obfuscation may evade detection
- **Pattern-based only**: Unknown credential formats won't be caught
- **Context-blind**: Cannot distinguish secrets in comments from actual code
- **False negatives possible**: Some valid code may match secret patterns
- **.env dependent**: Requires .env file to detect hardcoded environment values
- **File size limit**: Very large files (>10MB) are skipped to prevent performance issues

## Creating Similar Hooks

To extend security checks, follow the pattern in `check-secrets.py`:

1. **Read stdin**: Get tool input as JSON
2. **Check relevant operations**: Filter by tool type and operation
3. **Validate content**: Scan files for security issues
4. **Report with context**: Line numbers and issue descriptions
5. **Exit appropriately**: 0 for pass, 2 for block

## Implementation Details

The hook is implemented with the following design principles:

- **Fail-Closed**: Exits with code 2 on any errors to ensure security is maintained
- **Tool-Specific Checking**: Correctly checks for `tool_name == "Bash"` (not Git)
- **TOCTOU Protection**: Reads file content from git staging area instead of disk to ensure consistency
- **Word Boundary Matching**: Uses regex word boundaries (`\b`) in .env value detection to reduce false positives
- **Comprehensive Type Hints**: Full type annotations throughout for clarity and IDE support

## Debugging the Hook

If the hook isn't working as expected:

1. **Check hook configuration**: Verify `hooks.json` is valid
2. **Verify script location**: Ensure path is correct
3. **Verify tool_name matching**: Hook should be configured to trigger on `"Bash"` tool
4. **Test manually**:
   ```bash
   echo '{"tool_name": "Bash", "tool_input": {"command": "git commit -m test"}}' | \
     ./hooks/security/scripts/check-secrets.py
   ```
5. **Check .env file**: Ensure it's readable and properly formatted
6. **Review stderr**: Check for error messages (hook will exit with code 2 on errors)
7. **Check file sizes**: Verify staged files are under 10MB limit

## Related Resources

- See `hooks/README.md` for general hook documentation
- See `CLAUDE.md` for development workflow constraints
- See `.gitignore` for files excluded from git tracking
