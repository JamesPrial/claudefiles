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
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Final, TypedDict


class ExitCode(IntEnum):
    """Exit codes for the security hook."""

    SUCCESS = 0
    BLOCKED = 2


# Configuration constants
MIN_SECRET_LENGTH: Final[int] = 8
MAX_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
SUBPROCESS_TIMEOUT_SECONDS: Final[int] = 30

# Common non-secret values to skip
SKIP_VALUES: Final[frozenset[str]] = frozenset({
    "true", "false", "yes", "no", "on", "off",
    "development", "production", "staging", "test",
    "localhost", "127.0.0.1", "0.0.0.0",
    "utf-8", "utf8", "none", "null",
})

# Binary file extensions to skip
BINARY_EXTENSIONS: Final[frozenset[str]] = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip",
    ".wasm", ".exe", ".dll", ".so", ".pyc", ".class",
    ".woff", ".woff2", ".ttf", ".eot", ".ico",
    ".mp3", ".mp4", ".mov", ".tar", ".gz", ".7z",
    ".bin", ".dat", ".db", ".sqlite", ".sqlite3",
})

# Environment file patterns to skip
ENV_FILE_NAMES: Final[frozenset[str]] = frozenset({
    ".env", ".env.local", ".env.production", ".env.development",
    ".env.test", ".env.staging", ".env.example",
})


@dataclass(frozen=True, slots=True)
class SecretPattern:
    """A pattern for detecting secrets with its description."""

    pattern: re.Pattern[str]
    description: str


# Pre-compile all secret patterns at module load time
SECRET_PATTERNS: Final[tuple[SecretPattern, ...]] = tuple(
    SecretPattern(pattern=re.compile(pattern), description=description)
    for pattern, description in [
        # Generic secrets
        (r"(?i)(secret|token)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{20,}", "secret/token"),
        # AWS
        (r"(?i)(aws_access_key_id|aws_secret_access_key)\s*[:=]", "AWS credentials"),
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
        # OpenAI
        (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API key"),
        (r"sk-proj-[a-zA-Z0-9]{20,}", "OpenAI project API key"),
        # Google
        (r"AIza[0-9A-Za-z\-_]{35}", "Google API key"),
        # GitHub
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
        (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
        (r"ghu_[a-zA-Z0-9]{36}", "GitHub User Token"),
        (r"ghs_[a-zA-Z0-9]{36}", "GitHub Server Token"),
        (r"ghr_[a-zA-Z0-9]{36}", "GitHub Refresh Token"),
        # Bearer tokens
        (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Bearer token"),
        # Private keys
        (r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", "Private key"),
        # Slack
        (r"xox[baprs]-[a-zA-Z0-9\-]{10,}", "Slack token"),
        # Stripe
        (r"sk_live_[a-zA-Z0-9]{24,}", "Stripe secret key"),
        (r"rk_live_[a-zA-Z0-9]{24,}", "Stripe restricted key"),
        # SendGrid
        (r"SG\.[a-zA-Z0-9_\-]{22}\.[a-zA-Z0-9_\-]{43}", "SendGrid API key"),
        # Database connection strings
        (r"mongodb(\+srv)?://[^:]+:[^@\s]+@", "MongoDB connection string"),
        (r"postgres(ql)?://[^:]+:[^@\s]+@", "PostgreSQL connection string"),
        (r"mysql://[^:]+:[^@\s]+@", "MySQL connection string"),
        # Anthropic
        (r"sk-ant-[a-zA-Z0-9\-]{20,}", "Anthropic API key"),
    ]
)


class BashToolInput(TypedDict, total=False):
    """TypedDict for Bash tool input structure."""

    command: str
    timeout: int
    description: str


class HookInput(TypedDict, total=False):
    """TypedDict for the hook input JSON structure from Claude Code."""

    tool_name: str
    tool_input: BashToolInput | dict[str, str | int | bool | None]


@dataclass(frozen=True, slots=True)
class SecretIssue:
    """Represents a detected secret issue in a file."""

    file_path: str
    line_number: int
    description: str

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number} - {self.description}"


@dataclass(frozen=True, slots=True)
class ScanResult:
    """Result of scanning files for secrets."""

    pattern_issues: tuple[SecretIssue, ...]
    env_issues: tuple[SecretIssue, ...]

    @property
    def has_issues(self) -> bool:
        """Check if any issues were found."""
        return bool(self.pattern_issues or self.env_issues)

    def merge(self, other: ScanResult) -> ScanResult:
        """Merge two scan results together."""
        return ScanResult(
            pattern_issues=self.pattern_issues + other.pattern_issues,
            env_issues=self.env_issues + other.env_issues,
        )


def parse_env_file(env_path: Path) -> dict[str, str]:
    """Parse a .env file and return a dictionary of key-value pairs.

    Args:
        env_path: Path to the .env file to parse

    Returns:
        Dictionary mapping environment variable names to their values
    """
    env_vars: dict[str, str] = {}

    if not env_path.exists():
        return env_vars

    if not env_path.is_file():
        return env_vars

    try:
        content = env_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"Warning: Could not read {env_path}: {e}", file=sys.stderr)
        return env_vars

    for line in content.splitlines():
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # Parse key=value pairs
        if "=" not in line:
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        # Remove surrounding quotes if present
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]

        if key and value:
            env_vars[key] = value

    return env_vars


def filter_env_values(env_vars: dict[str, str]) -> dict[str, str]:
    """Filter .env values to only include those that should be checked as secrets.

    Args:
        env_vars: Dictionary of environment variables to filter

    Returns:
        Filtered dictionary containing only potential secret values
    """
    return {
        key: value
        for key, value in env_vars.items()
        if (
            len(value) >= MIN_SECRET_LENGTH
            and value.lower() not in SKIP_VALUES
            and not value.isdigit()
        )
    }


def is_env_file(file_path: str) -> bool:
    """Check if a file is an environment file that should be skipped.

    Args:
        file_path: Path to the file to check

    Returns:
        True if the file is an environment file, False otherwise
    """
    file_name = Path(file_path).name
    return file_name in ENV_FILE_NAMES or file_name.startswith(".env.")


def is_binary_file(file_path: str) -> bool:
    """Check if a file is a binary file that should be skipped.

    Args:
        file_path: Path to the file to check

    Returns:
        True if the file has a binary extension, False otherwise
    """
    suffix = Path(file_path).suffix.lower()
    return suffix in BINARY_EXTENSIONS


def run_git_command(
    args: list[str],
    *,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a git command with proper error handling and timeout.

    Args:
        args: Git command arguments (without 'git' prefix)
        cwd: Working directory for the command

    Returns:
        CompletedProcess with the command result

    Raises:
        subprocess.CalledProcessError: If the command fails
        subprocess.TimeoutExpired: If the command times out
    """
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        cwd=cwd,
    )


def get_staged_content(file_path: str, *, cwd: Path | None = None) -> str | None:
    """Get file content from git staging area to avoid TOCTOU issues.

    Args:
        file_path: Path to the file in the staging area
        cwd: Working directory for git commands

    Returns:
        File content as string, or None if the file cannot be read
    """
    try:
        result = run_git_command(["show", f":{file_path}"], cwd=cwd)
        return result.stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def get_line_number(content: str, position: int) -> int:
    """Calculate line number for a given position in content.

    Args:
        content: The full file content
        position: Character position in the content

    Returns:
        1-based line number for the position
    """
    if position < 0:
        return 1
    return content[:position].count("\n") + 1


def check_file_for_secrets(
    file_path: str,
    content: str,
    env_patterns: dict[str, re.Pattern[str]],
) -> ScanResult:
    """Check a single file for secrets.

    Args:
        file_path: Path to the file being checked
        content: File content to scan
        env_patterns: Pre-compiled patterns for .env values

    Returns:
        ScanResult containing any detected issues
    """
    pattern_issues: list[SecretIssue] = []
    env_issues: list[SecretIssue] = []

    # Check for pattern-based secrets
    for secret_pattern in SECRET_PATTERNS:
        for match in secret_pattern.pattern.finditer(content):
            line_num = get_line_number(content, match.start())
            pattern_issues.append(
                SecretIssue(
                    file_path=file_path,
                    line_number=line_num,
                    description=f"Found potential {secret_pattern.description}",
                )
            )

    # Check for hardcoded .env values
    for env_key, compiled_pattern in env_patterns.items():
        for match in compiled_pattern.finditer(content):
            line_num = get_line_number(content, match.start())
            env_issues.append(
                SecretIssue(
                    file_path=file_path,
                    line_number=line_num,
                    description=f"Found hardcoded value from .env key '{env_key}'",
                )
            )

    return ScanResult(
        pattern_issues=tuple(pattern_issues),
        env_issues=tuple(env_issues),
    )


def is_git_commit_command(command: str) -> bool:
    """Check if the command is a git commit operation.

    Args:
        command: The shell command to check

    Returns:
        True if this appears to be a git commit command
    """
    cmd_lower = command.lower()
    return "git" in cmd_lower and "commit" in cmd_lower


def parse_hook_input(raw_input: object) -> HookInput | None:
    """Parse and validate hook input from stdin.

    Args:
        raw_input: Raw parsed JSON input

    Returns:
        Validated HookInput or None if invalid
    """
    if not isinstance(raw_input, dict):
        return None

    # Validate required structure
    tool_name = raw_input.get("tool_name")
    if not isinstance(tool_name, str):
        return None

    tool_input = raw_input.get("tool_input")
    if tool_input is not None and not isinstance(tool_input, dict):
        return None

    return HookInput(
        tool_name=tool_name,
        tool_input=tool_input if tool_input is not None else {},
    )


def extract_command_from_input(hook_input: HookInput) -> str:
    """Extract the command string from hook input.

    Args:
        hook_input: Validated hook input

    Returns:
        The command string, or empty string if not found
    """
    tool_input = hook_input.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    if command is None:
        return ""

    return str(command)


def get_staged_files(cwd: Path | None = None) -> list[str] | None:
    """Get list of staged files from git.

    Args:
        cwd: Working directory for git commands

    Returns:
        List of staged file paths, or None on error
    """
    try:
        result = run_git_command(["diff", "--cached", "--name-only"], cwd=cwd)
        files = result.stdout.strip()
        if not files:
            return []
        return [f for f in files.split("\n") if f]
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"SECURITY: Failed to get staged files: {e}", file=sys.stderr)
        return None


def compile_env_patterns(env_values: dict[str, str]) -> dict[str, re.Pattern[str]]:
    """Compile regex patterns for environment variable values.

    Args:
        env_values: Dictionary of env var names to their values

    Returns:
        Dictionary of env var names to compiled patterns
    """
    patterns: dict[str, re.Pattern[str]] = {}
    for key, value in env_values.items():
        try:
            patterns[key] = re.compile(rf"\b{re.escape(value)}\b")
        except re.error:
            # Skip values that can't be compiled into valid patterns
            continue
    return patterns


def should_skip_file(file_path: str, cwd: Path | None = None) -> bool:
    """Determine if a file should be skipped during scanning.

    Args:
        file_path: Path to the file to check
        cwd: Working directory for resolving paths

    Returns:
        True if the file should be skipped, False otherwise
    """
    if is_binary_file(file_path):
        return True

    if is_env_file(file_path):
        return True

    # Check file size on disk (approximate check before reading from staging)
    try:
        full_path = Path(cwd, file_path) if cwd else Path(file_path)
        if full_path.exists() and full_path.is_file():
            file_size = full_path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                print(f"Warning: Skipping oversized file {file_path}", file=sys.stderr)
                return True
    except OSError:
        # If we can't stat the file, don't skip - let git show handle it
        pass

    return False


def print_security_warning(scan_result: ScanResult) -> None:
    """Print security warning with detected issues.

    Args:
        scan_result: The scan result containing issues to report
    """
    separator = "=" * 60
    print(f"\n{separator}", file=sys.stderr)
    print("SECURITY WARNING: Potential secrets detected in staged files!", file=sys.stderr)
    print(f"{separator}\n", file=sys.stderr)

    if scan_result.pattern_issues:
        print("  Pattern-based detections:", file=sys.stderr)
        for issue in sorted(scan_result.pattern_issues, key=str):
            print(f"    - {issue}", file=sys.stderr)
        print("", file=sys.stderr)

    if scan_result.env_issues:
        print("  Hardcoded .env values detected:", file=sys.stderr)
        for issue in sorted(scan_result.env_issues, key=str):
            print(f"    - {issue}", file=sys.stderr)
        print("", file=sys.stderr)

    print("Please remove secrets before committing.", file=sys.stderr)
    if scan_result.env_issues:
        print(
            "Use environment variables at runtime instead of hardcoding values.",
            file=sys.stderr,
        )
    print("Consider using a secrets manager for sensitive credentials.\n", file=sys.stderr)


def scan_staged_files(
    staged_files: list[str],
    env_patterns: dict[str, re.Pattern[str]],
    cwd: Path | None = None,
) -> ScanResult:
    """Scan all staged files for secrets.

    Args:
        staged_files: List of staged file paths
        env_patterns: Compiled patterns for env values
        cwd: Working directory for git commands

    Returns:
        Combined scan result from all files
    """
    combined_result = ScanResult(pattern_issues=(), env_issues=())

    for file_path in sorted(staged_files):
        if should_skip_file(file_path, cwd):
            continue

        content = get_staged_content(file_path, cwd=cwd)
        if content is None:
            continue

        # Skip tiny files (likely empty or minimal templates)
        if len(content) < 10:
            continue

        file_result = check_file_for_secrets(file_path, content, env_patterns)
        combined_result = combined_result.merge(file_result)

    return combined_result


def main() -> int:
    """Main entry point for the security hook.

    Returns:
        Exit code (0 for success, 2 for blocked)
    """
    # Load hook input from stdin (fail-closed on parse error)
    try:
        raw_input: object = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"SECURITY: Hook failed to parse input: {e}", file=sys.stderr)
        return ExitCode.BLOCKED

    hook_input = parse_hook_input(raw_input)
    if hook_input is None:
        # Not a valid hook input structure - allow to proceed (not our concern)
        return ExitCode.SUCCESS

    # Only check Bash tool
    if hook_input.get("tool_name") != "Bash":
        return ExitCode.SUCCESS

    command = extract_command_from_input(hook_input)
    if not is_git_commit_command(command):
        return ExitCode.SUCCESS

    # Determine working directory (avoid os.chdir - it mutates global state)
    project_dir_str = os.environ.get("CLAUDE_PROJECT_DIR")
    working_dir: Path | None = Path(project_dir_str) if project_dir_str else None

    # Load and filter .env values for secret detection
    env_path = (working_dir / ".env") if working_dir else Path(".env")
    env_vars = parse_env_file(env_path)
    secret_env_values = filter_env_values(env_vars)

    # Get staged files (fail-closed on error)
    staged_files = get_staged_files(cwd=working_dir)
    if staged_files is None:
        return ExitCode.BLOCKED

    if not staged_files:
        return ExitCode.SUCCESS

    # Pre-compile .env value patterns once
    env_patterns = compile_env_patterns(secret_env_values)

    # Scan all staged files
    scan_result = scan_staged_files(staged_files, env_patterns, cwd=working_dir)

    # If secrets found, block the commit
    if scan_result.has_issues:
        print_security_warning(scan_result)
        return ExitCode.BLOCKED

    return ExitCode.SUCCESS


if __name__ == "__main__":
    sys.exit(main())
