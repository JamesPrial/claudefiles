#!/usr/bin/env python3
"""
Security hook to detect secrets in staged files before git commit.

This hook runs as a PreToolUse hook on Bash commands containing "git commit".
It scans staged files for hardcoded secrets, API keys, and .env values.

Exit codes:
    0 - No secrets detected, commit proceeds
    2 - Secrets detected OR error occurred, commit blocked (fail-closed)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from enum import IntEnum
from pathlib import Path
from typing import TypedDict


class ExitCode(IntEnum):
    """Exit codes for the security hook."""

    SUCCESS = 0
    BLOCKED = 2


class ToolInput(TypedDict, total=False):
    """Type definition for tool input from Claude hooks."""

    command: str


class HookInput(TypedDict, total=False):
    """Type definition for hook input from stdin."""

    tool_name: str
    tool_input: ToolInput | dict[str, object] | str | None


# Configuration
MIN_SECRET_LENGTH: int = 8
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
SUBPROCESS_TIMEOUT: int = 30  # 30 seconds

# Common non-secret values to skip
SKIP_VALUES: frozenset[str] = frozenset({
    'true', 'false', 'yes', 'no', 'on', 'off',
    'development', 'production', 'staging', 'test',
    'localhost', '127.0.0.1', '0.0.0.0',
    'utf-8', 'utf8', 'none', 'null',
})

# Binary file extensions to skip (lowercase for case-insensitive matching)
BINARY_EXTENSIONS: frozenset[str] = frozenset({
    '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip',
    '.wasm', '.exe', '.dll', '.so', '.pyc', '.class',
    '.woff', '.woff2', '.ttf', '.eot', '.ico',
    '.mp3', '.mp4', '.mov', '.tar', '.gz', '.7z',
    '.bin', '.dat', '.db', '.sqlite', '.sqlite3',
})

# Environment file patterns to skip
ENV_FILE_NAMES: frozenset[str] = frozenset({
    '.env', '.env.local', '.env.production', '.env.development',
    '.env.test', '.env.staging', '.env.example',
})

# Pre-compiled secret patterns to detect (compiled once at module load)
SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Generic secrets
    (re.compile(r'(?i)(secret|token)\s*[:=]\s*[\'"]?[a-zA-Z0-9_\-]{20,}'), "secret/token"),
    # AWS
    (re.compile(r'(?i)(aws_access_key_id|aws_secret_access_key)\s*[:=]'), "AWS credentials"),
    (re.compile(r'AKIA[0-9A-Z]{16}'), "AWS Access Key ID"),
    # OpenAI
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), "OpenAI API key"),
    (re.compile(r'sk-proj-[a-zA-Z0-9]{20,}'), "OpenAI project API key"),
    # Google
    (re.compile(r'AIza[0-9A-Za-z\-_]{35}'), "Google API key"),
    # GitHub
    (re.compile(r'ghp_[a-zA-Z0-9]{36}'), "GitHub Personal Access Token"),
    (re.compile(r'gho_[a-zA-Z0-9]{36}'), "GitHub OAuth Token"),
    (re.compile(r'ghu_[a-zA-Z0-9]{36}'), "GitHub User Token"),
    (re.compile(r'ghs_[a-zA-Z0-9]{36}'), "GitHub Server Token"),
    (re.compile(r'ghr_[a-zA-Z0-9]{36}'), "GitHub Refresh Token"),
    # Bearer tokens
    (re.compile(r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}'), "Bearer token"),
    # Private keys
    (re.compile(r'-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----'), "Private key"),
    # Slack
    (re.compile(r'xox[baprs]-[a-zA-Z0-9\-]{10,}'), "Slack token"),
    # Stripe
    (re.compile(r'sk_live_[a-zA-Z0-9]{24,}'), "Stripe secret key"),
    (re.compile(r'rk_live_[a-zA-Z0-9]{24,}'), "Stripe restricted key"),
    # SendGrid
    (re.compile(r'SG\.[a-zA-Z0-9_\-]{20,}\.[a-zA-Z0-9_\-]{20,}'), "SendGrid API key"),
    # Database connection strings
    (re.compile(r'mongodb(\+srv)?://[^:]+:[^@\s]+@'), "MongoDB connection string"),
    (re.compile(r'postgres(ql)?://[^:]+:[^@\s]+@'), "PostgreSQL connection string"),
    (re.compile(r'mysql://[^:]+:[^@\s]+@'), "MySQL connection string"),
    # Anthropic
    (re.compile(r'sk-ant-[a-zA-Z0-9\-]{20,}'), "Anthropic API key"),
]


def parse_env_file(env_path: Path) -> dict[str, str]:
    """Parse a .env file and return a dictionary of key-value pairs."""
    env_vars: dict[str, str] = {}

    if not env_path.exists():
        return env_vars

    try:
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove surrounding quotes if present
                    if value and value[0] in ('"', "'") and value[-1] == value[0]:
                        value = value[1:-1]

                    if key and value:
                        env_vars[key] = value
    except (OSError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {env_path}: {e}", file=sys.stderr)

    return env_vars


def filter_env_values(env_vars: dict[str, str]) -> dict[str, str]:
    """Filter .env values to only include those that should be checked as secrets."""
    filtered: dict[str, str] = {}

    for key, value in env_vars.items():
        # Skip short values (likely not secrets)
        if len(value) < MIN_SECRET_LENGTH:
            continue

        # Skip common non-secret values
        if value.lower() in SKIP_VALUES:
            continue

        # Skip numeric-only values
        if value.isdigit():
            continue

        filtered[key] = value

    return filtered


def is_env_file(file_path: str) -> bool:
    """Check if a file is an environment file that should be skipped."""
    # Handle both Unix (/) and Windows (\) path separators
    # Manual split is needed because PurePath only recognizes OS-specific separators
    file_name = file_path.replace("\\", "/").split("/")[-1]
    return file_name in ENV_FILE_NAMES or file_name.startswith('.env.')


def is_binary_file(file_path: str) -> bool:
    """Check if a file is a binary file that should be skipped (case-insensitive)."""
    lower_path = file_path.lower()
    return any(lower_path.endswith(ext) for ext in BINARY_EXTENSIONS)


def get_staged_content(file_path: str) -> str | None:
    """Get file content from git staging area to avoid TOCTOU issues."""
    try:
        result = subprocess.run(
            ["git", "show", f":{file_path}"],
            capture_output=True,
            text=True,
            check=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None
    except subprocess.TimeoutExpired:
        print(f"Warning: Timeout reading staged content for {file_path}", file=sys.stderr)
        return None


def get_line_number(content: str, position: int) -> int:
    """Calculate line number for a given position in content."""
    return content[:position].count('\n') + 1


def check_file_for_secrets(
    file_path: str,
    content: str,
    env_patterns: dict[str, re.Pattern[str]],
) -> tuple[list[str], list[str]]:
    """Check a single file for secrets.

    Args:
        file_path: Path to the file being checked
        content: File content to scan
        env_patterns: Pre-compiled patterns for .env values

    Returns:
        Tuple of (pattern_issues, env_issues)
    """
    pattern_issues: list[str] = []
    env_issues: list[str] = []

    # Check for pattern-based secrets (patterns are pre-compiled at module level)
    for compiled_pattern, description in SECRET_PATTERNS:
        for match in compiled_pattern.finditer(content):
            line_num = get_line_number(content, match.start())
            pattern_issues.append(f"{file_path}:{line_num} - Found potential {description}")

    # Check for hardcoded .env values
    for env_key, compiled_pattern in env_patterns.items():
        for match in compiled_pattern.finditer(content):
            line_num = get_line_number(content, match.start())
            env_issues.append(f"{file_path}:{line_num} - Found hardcoded value from .env key '{env_key}'")

    return pattern_issues, env_issues


def is_git_commit_command(command: str) -> bool:
    """Check if the command is a git commit operation."""
    cmd_lower = command.lower()
    return "git" in cmd_lower and "commit" in cmd_lower


def main() -> None:
    """Main entry point for the security hook."""
    # Load hook input from stdin (fail-closed on parse error)
    try:
        input_data: HookInput = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"SECURITY: Hook failed to parse input: {e}", file=sys.stderr)
        sys.exit(ExitCode.BLOCKED)

    # Validate input structure
    tool_name = input_data.get("tool_name", "")
    if not isinstance(tool_name, str):
        tool_name = ""

    tool_input_raw = input_data.get("tool_input")

    if not isinstance(tool_input_raw, dict):
        # Not a valid tool input - allow to proceed (not our concern)
        sys.exit(ExitCode.SUCCESS)

    # Extract command safely with type narrowing
    command_raw = tool_input_raw.get("command")
    command: str = str(command_raw) if command_raw is not None else ""

    # Only check Bash tool with git commit operations
    if tool_name != "Bash":
        sys.exit(ExitCode.SUCCESS)

    if not is_git_commit_command(command):
        sys.exit(ExitCode.SUCCESS)

    # Get project directory (don't chdir - avoid global state mutation)
    project_dir: str | None = os.environ.get("CLAUDE_PROJECT_DIR")
    project_root = Path(project_dir) if project_dir else Path.cwd()

    # Change to project directory for git operations
    original_cwd = Path.cwd()
    if project_dir:
        os.chdir(project_root)

    try:
        _run_secret_check(project_root)
    finally:
        # Restore original directory
        os.chdir(original_cwd)


def _run_secret_check(project_root: Path) -> None:
    """Run the secret check logic.

    Args:
        project_root: Root directory of the project being checked
    """
    # Load and filter .env values for secret detection
    env_path = project_root / ".env"
    env_vars = parse_env_file(env_path)
    secret_env_values = filter_env_values(env_vars)

    # Get staged files (fail-closed on error)
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        staged_files: list[str] = [f for f in result.stdout.strip().split('\n') if f]
    except subprocess.CalledProcessError as e:
        print(f"SECURITY: Failed to get staged files: {e}", file=sys.stderr)
        sys.exit(ExitCode.BLOCKED)
    except subprocess.TimeoutExpired:
        print("SECURITY: Timeout getting staged files", file=sys.stderr)
        sys.exit(ExitCode.BLOCKED)

    if not staged_files:
        sys.exit(ExitCode.SUCCESS)

    # Pre-compile .env value patterns once (avoid recompilation per file)
    env_patterns: dict[str, re.Pattern[str]] = {
        key: re.compile(rf'\b{re.escape(value)}\b')
        for key, value in secret_env_values.items()
    }

    all_pattern_issues: list[str] = []
    all_env_issues: list[str] = []

    # Check each staged file
    for file_path in sorted(staged_files):
        # Skip binary files (case-insensitive)
        if is_binary_file(file_path):
            continue

        # Skip .env files themselves
        if is_env_file(file_path):
            continue

        # Read content from git staging area (not disk - avoids TOCTOU)
        content = get_staged_content(file_path)
        if content is None:
            continue

        # Check staged content size (not disk file size - they can differ!)
        if len(content) > MAX_FILE_SIZE:
            print(f"Warning: Skipping oversized staged content {file_path}", file=sys.stderr)
            continue

        # Skip tiny files (likely empty or minimal templates)
        if len(content) < 10:
            continue

        # Check file for secrets using extracted helper
        pattern_issues, env_issues = check_file_for_secrets(file_path, content, env_patterns)
        all_pattern_issues.extend(pattern_issues)
        all_env_issues.extend(env_issues)

    # If secrets found, block the commit
    if all_pattern_issues or all_env_issues:
        print("\n" + "=" * 60, file=sys.stderr)
        print("SECURITY WARNING: Potential secrets detected in staged files!", file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr)

        if all_pattern_issues:
            print("  Pattern-based detections:", file=sys.stderr)
            for issue in sorted(all_pattern_issues):
                print(f"    - {issue}", file=sys.stderr)
            print("", file=sys.stderr)

        if all_env_issues:
            print("  Hardcoded .env values detected:", file=sys.stderr)
            for issue in sorted(all_env_issues):
                print(f"    - {issue}", file=sys.stderr)
            print("", file=sys.stderr)

        print("Please remove secrets before committing.", file=sys.stderr)
        if all_env_issues:
            print("Use environment variables at runtime instead of hardcoding values.", file=sys.stderr)
        print("Consider using a secrets manager for sensitive credentials.\n", file=sys.stderr)
        sys.exit(ExitCode.BLOCKED)

    sys.exit(ExitCode.SUCCESS)


if __name__ == "__main__":
    main()
