"""
Comprehensive test suite for check_secrets.py security hook.

Tests cover:
- .env file parsing and filtering
- Secret pattern detection
- Binary file detection
- Git commit command detection
- Line number calculation
- File content scanning for secrets
- Main function integration tests
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from check_secrets import (
    ExitCode,
    MIN_SECRET_LENGTH,
    SKIP_VALUES,
    SUBPROCESS_TIMEOUT,
    check_file_for_secrets,
    filter_env_values,
    get_line_number,
    get_staged_content,
    is_binary_file,
    is_env_file,
    is_git_commit_command,
    main,
    parse_env_file,
)

if TYPE_CHECKING:
    from collections.abc import Generator


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def env_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary .env file for testing."""
    env_path = tmp_path / ".env"
    yield env_path
    if env_path.exists():
        env_path.unlink()


@pytest.fixture
def sample_env_content() -> str:
    """Standard .env file content for testing."""
    return (
        "API_KEY=secret123456789\n"
        "DB_URL=postgresql://user:pass@localhost\n"
        "DEBUG=true\n"
    )


@pytest.fixture
def empty_env_patterns() -> dict[str, re.Pattern[str]]:
    """Empty env patterns dict with proper typing."""
    return {}


# =============================================================================
# TestParseEnvFile
# =============================================================================


class TestParseEnvFile:
    """Tests for parse_env_file() function."""

    def test_parse_env_file_with_valid_content(
        self, env_file: Path, sample_env_content: str
    ) -> None:
        """Parse a .env file with standard key-value pairs."""
        env_file.write_text(sample_env_content)

        result = parse_env_file(env_file)

        assert result == {
            "API_KEY": "secret123456789",
            "DB_URL": "postgresql://user:pass@localhost",
            "DEBUG": "true",
        }

    def test_parse_env_file_with_quoted_values(self, env_file: Path) -> None:
        """Handle both single and double-quoted values."""
        env_file.write_text(
            "SINGLE_QUOTE='value123456789'\n"
            "DOUBLE_QUOTE=\"value987654321\"\n"
            "NO_QUOTE=plainvalue12345\n"
        )

        result = parse_env_file(env_file)

        assert result["SINGLE_QUOTE"] == "value123456789"
        assert result["DOUBLE_QUOTE"] == "value987654321"
        assert result["NO_QUOTE"] == "plainvalue12345"

    def test_parse_env_file_with_comments(self, env_file: Path) -> None:
        """Skip comment lines starting with #."""
        env_file.write_text(
            "# This is a comment\n"
            "API_KEY=secret123456789\n"
            "  # Another comment\n"
            "DEBUG=false\n"
        )

        result = parse_env_file(env_file)

        assert len(result) == 2
        assert result["API_KEY"] == "secret123456789"
        assert "This is a comment" not in str(result)

    def test_parse_env_file_with_empty_lines(self, env_file: Path) -> None:
        """Skip empty lines and whitespace-only lines."""
        env_file.write_text(
            "API_KEY=secret123456789\n"
            "\n"
            "  \n"
            "DEBUG=true\n"
        )

        result = parse_env_file(env_file)

        assert len(result) == 2

    def test_parse_env_file_with_multiple_equals(self, env_file: Path) -> None:
        """Handle values containing multiple equals signs."""
        env_file.write_text("BASE64_VALUE=aGVsbG8gd29ybGQ=extradata\n")

        result = parse_env_file(env_file)

        assert result["BASE64_VALUE"] == "aGVsbG8gd29ybGQ=extradata"

    def test_parse_env_file_nonexistent(self) -> None:
        """Return empty dict for nonexistent file."""
        result = parse_env_file(Path("/nonexistent/path/.env"))

        assert result == {}

    def test_parse_env_file_with_whitespace_in_values(self, env_file: Path) -> None:
        """Preserve whitespace in values after stripping outer spaces."""
        env_file.write_text("WITH_SPACES=value with spaces inside1234\n")

        result = parse_env_file(env_file)

        assert result["WITH_SPACES"] == "value with spaces inside1234"

    def test_parse_env_file_with_mismatched_quotes(self, env_file: Path) -> None:
        """Handle values with mismatched quotes (don't remove them)."""
        env_file.write_text("MISMATCHED=\"value123456789'\n")

        result = parse_env_file(env_file)

        assert result["MISMATCHED"] == "\"value123456789'"

    def test_parse_env_file_with_empty_value(self, env_file: Path) -> None:
        """Skip entries with empty values."""
        env_file.write_text(
            "EMPTY_KEY=\n"
            "VALID_KEY=value123456789\n"
        )

        result = parse_env_file(env_file)

        assert "EMPTY_KEY" not in result
        assert "VALID_KEY" in result

    def test_parse_env_file_with_no_equals(self, env_file: Path) -> None:
        """Skip lines without equals sign."""
        env_file.write_text(
            "VALID_KEY=value123456789\n"
            "INVALID_LINE_NO_EQUALS\n"
        )

        result = parse_env_file(env_file)

        assert len(result) == 1
        assert "VALID_KEY" in result

    def test_parse_env_file_unicode_error(self, env_file: Path) -> None:
        """Handle files with invalid encoding."""
        # Write binary data that will fail UTF-8 decoding
        env_file.write_bytes(b'\xff\xfe invalid utf-8 \x80\x81')

        result = parse_env_file(env_file)

        assert result == {}


# =============================================================================
# TestFilterEnvValues
# =============================================================================


class TestFilterEnvValues:
    """Tests for filter_env_values() function."""

    def test_filter_env_values_removes_short_values(self) -> None:
        """Filter out values shorter than MIN_SECRET_LENGTH."""
        env_vars: dict[str, str] = {
            "SHORT": "abc",
            "LONG": "this_is_a_long_secret_value_that_should_not_be_filtered",
        }

        result = filter_env_values(env_vars)

        assert "SHORT" not in result
        assert "LONG" in result

    def test_filter_env_values_removes_skip_values(self) -> None:
        """Filter out common non-secret values from SKIP_VALUES."""
        env_vars: dict[str, str] = {
            "ENV_TYPE": "production",
            "DEBUG": "true",
            "SECRET_KEY": "super_secret_key_that_is_very_long",
        }

        result = filter_env_values(env_vars)

        assert "ENV_TYPE" not in result
        assert "DEBUG" not in result
        assert "SECRET_KEY" in result

    def test_filter_env_values_removes_numeric_values(self) -> None:
        """Filter out numeric-only values."""
        env_vars: dict[str, str] = {
            "PORT": "3000",
            "DATABASE_POOL_SIZE": "20",
            "API_KEY": "sk-proj-ABC123456789DEF123456789",
        }

        result = filter_env_values(env_vars)

        assert "PORT" not in result
        assert "DATABASE_POOL_SIZE" not in result
        assert "API_KEY" in result

    def test_filter_env_values_case_insensitive_matching(self) -> None:
        """Skip values matching SKIP_VALUES regardless of case."""
        env_vars: dict[str, str] = {
            "ENV1": "PRODUCTION",
            "ENV2": "Localhost",
            "ENV3": "True",
            "SECRET": "actual_secret_key_that_is_quite_long",
        }

        result = filter_env_values(env_vars)

        assert "ENV1" not in result
        assert "ENV2" not in result
        assert "ENV3" not in result
        assert "SECRET" in result

    def test_filter_env_values_preserves_valid_secrets(self) -> None:
        """Preserve values that pass all filters."""
        long_suffix = "a" * 25
        env_vars: dict[str, str] = {
            "API_KEY": f"sk-ant-{long_suffix}",
            "DB_PASSWORD": "MyComplex!Pass#123456789",
            "TOKEN": "ghp_" + "A" * 36,
        }

        result = filter_env_values(env_vars)

        assert len(result) == 3
        assert all(key in result for key in env_vars)

    def test_filter_env_values_empty_input(self) -> None:
        """Handle empty env_vars dict."""
        result = filter_env_values({})

        assert result == {}

    def test_filter_env_values_all_filtered(self) -> None:
        """Return empty dict when all values are filtered."""
        env_vars: dict[str, str] = {
            "SHORT": "abc",
            "ENV": "development",
            "PORT": "5432",
        }

        result = filter_env_values(env_vars)

        assert result == {}


# =============================================================================
# TestIsEnvFile
# =============================================================================


class TestIsEnvFile:
    """Tests for is_env_file() function."""

    @pytest.mark.parametrize(
        "file_path",
        [
            ".env",
            "/path/to/.env",
            "project/.env.local",
            ".env.production",
            ".env.development",
            ".env.test",
            ".env.staging",
            ".env.example",
            ".env.custom",
            ".env.anything",
            ".env.new_environment",
            "/home/user/project/.env",
            "/var/app/.env.production",
        ],
    )
    def test_is_env_file_returns_true(self, file_path: str) -> None:
        """Detect files that should be treated as .env files."""
        assert is_env_file(file_path) is True

    @pytest.mark.parametrize(
        "file_path",
        [
            ".envrc",
            "env.txt",
            ".env-backup",
            "constants.js",
            ".env_old",
            "/home/user/.env_config/constants.js",
        ],
    )
    def test_is_env_file_returns_false(self, file_path: str) -> None:
        """Reject non-.env files."""
        assert is_env_file(file_path) is False

    def test_is_env_file_windows_paths(self) -> None:
        """Handle Windows-style paths."""
        assert is_env_file("C:\\project\\.env") is True
        assert is_env_file("C:\\project\\.env.local") is True


# =============================================================================
# TestIsBinaryFile
# =============================================================================


class TestIsBinaryFile:
    """Tests for is_binary_file() function."""

    @pytest.mark.parametrize(
        "file_path",
        [
            "image.png",
            "photo.jpg",
            "picture.jpeg",
            "animated.gif",
            "report.pdf",
            "archive.zip",
            "program.exe",
            "library.dll",
            "library.so",
            "compiled.pyc",
            "compiled.class",
            "font.woff",
            "font.woff2",
            "font.ttf",
            "data.tar",
            "data.gz",
            "data.7z",
            "database.db",
            "database.sqlite",
            "database.sqlite3",
            "music.mp3",
            "video.mp4",
            "video.mov",
            "/home/user/images/photo.jpg",
        ],
    )
    def test_is_binary_file_returns_true(self, file_path: str) -> None:
        """Detect binary file formats."""
        assert is_binary_file(file_path) is True

    @pytest.mark.parametrize(
        "file_path",
        [
            "script.py",
            "code.js",
            "config.json",
            "document.txt",
            "README.md",
            "/home/user/scripts/script.py",
        ],
    )
    def test_is_binary_file_returns_false(self, file_path: str) -> None:
        """Reject text and source files."""
        assert is_binary_file(file_path) is False

    def test_is_binary_file_case_insensitive(self) -> None:
        """Extension matching should be case-insensitive."""
        assert is_binary_file("image.PNG") is True
        assert is_binary_file("image.png") is True
        assert is_binary_file("archive.ZIP") is True
        assert is_binary_file("photo.JPG") is True
        assert is_binary_file("photo.Jpg") is True


# =============================================================================
# TestIsGitCommitCommand
# =============================================================================


class TestIsGitCommitCommand:
    """Tests for is_git_commit_command() function."""

    @pytest.mark.parametrize(
        "command",
        [
            "git commit",
            'git commit -m "message"',
            'git commit -am "message"',
            'git commit -m "fix" --amend',
            "git commit --allow-empty",
            'git commit -S "key" -m "msg"',
            "GIT COMMIT",
            'Git Commit -m "msg"',
            "gIT cOMMIT",
            "/usr/bin/git commit",
            "C:\\git\\git.exe commit",
        ],
    )
    def test_is_git_commit_command_returns_true(self, command: str) -> None:
        """Detect git commit commands."""
        assert is_git_commit_command(command) is True

    @pytest.mark.parametrize(
        "command",
        [
            "git push",
            "git pull",
            "git add file.txt",
            "git status",
            'commit -m "msg"',
            "just commit",
            "",
            "git",
        ],
    )
    def test_is_git_commit_command_returns_false(self, command: str) -> None:
        """Reject non-commit git commands."""
        assert is_git_commit_command(command) is False


# =============================================================================
# TestGetLineNumber
# =============================================================================


class TestGetLineNumber:
    """Tests for get_line_number() function."""

    def test_get_line_number_first_position(self) -> None:
        """Line number for position 0 should be 1."""
        content = "first line\nsecond line\n"

        assert get_line_number(content, 0) == 1

    def test_get_line_number_middle_of_first_line(self) -> None:
        """Position in middle of first line should return line 1."""
        content = "first line\nsecond line\n"

        assert get_line_number(content, 5) == 1

    def test_get_line_number_after_first_newline(self) -> None:
        """Position right after first newline should be line 2."""
        content = "first line\nsecond line\n"

        assert get_line_number(content, 11) == 2

    def test_get_line_number_middle_of_second_line(self) -> None:
        """Position in middle of second line should return line 2."""
        content = "first line\nsecond line\n"

        assert get_line_number(content, 15) == 2

    def test_get_line_number_multiple_lines(self) -> None:
        """Calculate correct line numbers for multi-line content."""
        content = "line1\nline2\nline3\nline4\n"

        assert get_line_number(content, 0) == 1
        assert get_line_number(content, 6) == 2
        assert get_line_number(content, 12) == 3
        assert get_line_number(content, 18) == 4

    def test_get_line_number_no_newlines(self) -> None:
        """Content without newlines should always be line 1."""
        content = "single line content"

        assert get_line_number(content, 0) == 1
        assert get_line_number(content, 10) == 1
        assert get_line_number(content, len(content) - 1) == 1

    def test_get_line_number_empty_content(self) -> None:
        """Empty content at position 0 should be line 1."""
        assert get_line_number("", 0) == 1

    def test_get_line_number_consecutive_newlines(self) -> None:
        """Handle consecutive newlines (empty lines)."""
        content = "line1\n\n\nline4\n"

        assert get_line_number(content, 0) == 1
        assert get_line_number(content, 6) == 2
        assert get_line_number(content, 7) == 3
        assert get_line_number(content, 8) == 4


# =============================================================================
# TestGetStagedContent
# =============================================================================


class TestGetStagedContent:
    """Tests for get_staged_content() function."""

    def test_get_staged_content_success(self) -> None:
        """Return file content from git staging area on success."""
        expected_content = "file content here"
        mock_result = MagicMock()
        mock_result.stdout = expected_content

        with patch("check_secrets.subprocess.run", return_value=mock_result):
            result = get_staged_content("test.py")

        assert result == expected_content

    def test_get_staged_content_failure(self) -> None:
        """Return None when git command fails."""
        with patch(
            "check_secrets.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "git"),
        ):
            result = get_staged_content("nonexistent.py")

        assert result is None

    def test_get_staged_content_timeout(self) -> None:
        """Return None when git command times out."""
        with patch(
            "check_secrets.subprocess.run",
            side_effect=subprocess.TimeoutExpired("git", SUBPROCESS_TIMEOUT),
        ):
            result = get_staged_content("slow_file.py")

        assert result is None

    def test_get_staged_content_calls_git_correctly(self) -> None:
        """Verify correct git command is called with timeout."""
        mock_result = MagicMock()
        mock_result.stdout = "content"

        with patch("check_secrets.subprocess.run", return_value=mock_result) as mock_run:
            get_staged_content("path/to/file.py")

        mock_run.assert_called_once_with(
            ["git", "show", ":path/to/file.py"],
            capture_output=True,
            text=True,
            check=True,
            timeout=SUBPROCESS_TIMEOUT,
        )


# =============================================================================
# TestCheckFileForSecrets
# =============================================================================


class TestCheckFileForSecrets:
    """Tests for check_file_for_secrets() function."""

    def test_check_file_for_secrets_no_secrets(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Return empty lists when no secrets are detected."""
        content = "def hello_world():\n    print('Hello, World!')\n"

        pattern_issues, env_issues = check_file_for_secrets(
            "test.py", content, empty_env_patterns
        )

        assert pattern_issues == []
        assert env_issues == []

    def test_check_file_for_secrets_aws_key(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect AWS Access Key ID."""
        content = "config = {\n    'key': 'AKIA2B3C4D5E6F7G8H9I'\n}"

        pattern_issues, env_issues = check_file_for_secrets(
            "config.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any("AWS" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_openai_key(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect OpenAI API key."""
        content = "api_key = 'sk-abcdefghij1234567890'"

        pattern_issues, env_issues = check_file_for_secrets(
            "app.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0

    def test_check_file_for_secrets_github_token(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect GitHub Personal Access Token."""
        token = "ghp_" + "A" * 36
        content = f"token = '{token}'"

        pattern_issues, env_issues = check_file_for_secrets(
            "script.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any("GitHub" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_private_key(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect private key headers."""
        content = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEpAIBAAKCAQEA1234567890abcdef1234567890\n"
            "-----END RSA PRIVATE KEY-----\n"
        )

        pattern_issues, env_issues = check_file_for_secrets(
            "key.pem", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any("Private key" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_database_connection(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect database connection strings with credentials."""
        content = "url = 'postgresql://user:secretpass@localhost/db'"

        pattern_issues, env_issues = check_file_for_secrets(
            "db.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any("PostgreSQL" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_env_value_detection(self) -> None:
        """Detect hardcoded .env values."""
        content = "api_key = 'my_secret_value_123456789'"
        env_patterns: dict[str, re.Pattern[str]] = {
            "API_KEY": re.compile(r"\bmy_secret_value_123456789\b")
        }

        pattern_issues, env_issues = check_file_for_secrets(
            "config.py", content, env_patterns
        )

        assert len(env_issues) > 0
        assert any("hardcoded value" in issue for issue in env_issues)

    def test_check_file_for_secrets_multiple_secrets(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect multiple secrets in one file."""
        anthropic_key = "sk-ant-" + "A" * 30
        github_token = "ghp_" + "B" * 36
        content = f"""
api_key = '{anthropic_key}'
github_token = '{github_token}'
password = 'secret_password_1234567890'
"""

        pattern_issues, env_issues = check_file_for_secrets(
            "secrets.py", content, empty_env_patterns
        )

        assert len(pattern_issues) >= 2

    def test_check_file_for_secrets_line_numbers(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Return correct line numbers in issues."""
        anthropic_key = "sk-ant-" + "x" * 20
        content = f"line1\napi_key = '{anthropic_key}'\nline3\n"

        pattern_issues, env_issues = check_file_for_secrets(
            "app.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any(":2 -" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_slack_token(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect Slack tokens."""
        content = "slack_token = 'xoxb-' + '1' * 10 + '-' + '2' * 10 + '-' + 'a' * 16"

        pattern_issues, env_issues = check_file_for_secrets(
            "slack.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any("Slack" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_stripe_key(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect Stripe secret keys."""
        stripe_key = "sk_live_" + "x" * 25
        content = f"stripe_key = '{stripe_key}'"

        pattern_issues, env_issues = check_file_for_secrets(
            "payment.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any("Stripe" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_bearer_token(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect bearer tokens."""
        content = "Authorization: Bearer AbCdEfGhIjKlMnOpQrStUvWxYz123456"

        pattern_issues, env_issues = check_file_for_secrets(
            "request.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any("Bearer" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_filename_in_output(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Ensure filename is included in issue messages."""
        secret = "sk-ant-" + "x" * 30
        content = f"secret = '{secret}'"

        pattern_issues, env_issues = check_file_for_secrets(
            "myfile.py", content, empty_env_patterns
        )

        assert all("myfile.py" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_sendgrid_key(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect SendGrid API keys."""
        content = (
            "sg_key = 'SG.1234567890abcdef1234567890."
            "abcdefghijklmnopqrstuvwxyz1234567890ABCD'"
        )

        pattern_issues, env_issues = check_file_for_secrets(
            "email.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any("SendGrid" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_anthropic_key(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect Anthropic API keys."""
        key = "sk-ant-" + "x" * 30
        content = f"key = '{key}'"

        pattern_issues, env_issues = check_file_for_secrets(
            "claude.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any("Anthropic" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_env_word_boundary(self) -> None:
        """Only match env values with word boundaries."""
        content = "my_secret_value_123456789_extra"
        env_patterns: dict[str, re.Pattern[str]] = {
            "API_KEY": re.compile(r"\bmy_secret_value_123456789\b")
        }

        pattern_issues, env_issues = check_file_for_secrets(
            "config.py", content, env_patterns
        )

        assert len(env_issues) == 0

    def test_check_file_for_secrets_mongodb_connection(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect MongoDB connection strings."""
        content = "mongo_url = 'mongodb+srv://user:password@cluster.mongodb.net/db'"

        pattern_issues, env_issues = check_file_for_secrets(
            "mongo.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any("MongoDB" in issue for issue in pattern_issues)

    def test_check_file_for_secrets_mysql_connection(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect MySQL connection strings."""
        content = "db_url = 'mysql://username:password@localhost:3306/mydb'"

        pattern_issues, env_issues = check_file_for_secrets(
            "db.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0
        assert any("MySQL" in issue for issue in pattern_issues)


# =============================================================================
# TestSecretPatternEdgeCases
# =============================================================================


class TestSecretPatternEdgeCases:
    """Tests for edge cases in secret pattern detection."""

    def test_secret_pattern_multiple_matches_same_line(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Detect multiple matches on same line."""
        key1 = "sk-ant-" + "x" * 20
        key2 = "sk-ant-" + "y" * 20
        content = f"keys = ['{key1}', '{key2}']"

        pattern_issues, env_issues = check_file_for_secrets(
            "keys.py", content, empty_env_patterns
        )

        assert len(pattern_issues) >= 2

    def test_secret_pattern_case_insensitive(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Secret patterns should handle case variations."""
        content = "SECRET = 'value123456789abcdef'"

        pattern_issues, env_issues = check_file_for_secrets(
            "config.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0

    def test_secret_pattern_in_comments(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Secrets in comments are still detected (better safe)."""
        key = "sk-ant-" + "x" * 20
        content = f"# TODO: Remove this token: {key}"

        pattern_issues, env_issues = check_file_for_secrets(
            "todo.py", content, empty_env_patterns
        )

        assert len(pattern_issues) > 0


# =============================================================================
# TestSecretPatternFalsePositives
# =============================================================================


class TestSecretPatternFalsePositives:
    """Ensure patterns don't match too aggressively."""

    def test_short_sk_prefix_not_matched(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Short sk- prefixed strings shouldn't match OpenAI pattern."""
        content = "key = 'sk-short'"  # Only 5 chars after prefix

        pattern_issues, _ = check_file_for_secrets(
            "test.py", content, empty_env_patterns
        )

        # Should NOT match as OpenAI key (requires 20+ chars after prefix)
        assert not any("OpenAI" in issue for issue in pattern_issues)

    def test_url_with_localhost_not_matched_as_db_connection(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """URLs without credentials shouldn't match."""
        content = "url = 'postgresql://localhost/db'"

        pattern_issues, _ = check_file_for_secrets(
            "test.py", content, empty_env_patterns
        )

        assert not any("PostgreSQL" in issue for issue in pattern_issues)

    def test_short_github_token_not_matched(
        self, empty_env_patterns: dict[str, re.Pattern[str]]
    ) -> None:
        """Short ghp_ prefixed strings shouldn't match."""
        content = "token = 'ghp_short'"  # Less than 36 chars

        pattern_issues, _ = check_file_for_secrets(
            "test.py", content, empty_env_patterns
        )

        assert not any("GitHub" in issue for issue in pattern_issues)


# =============================================================================
# TestMain
# =============================================================================


class TestMain:
    """Tests for main() function entry point."""

    def test_main_non_bash_tool_allows(self) -> None:
        """Non-Bash tools should be allowed through."""
        input_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/some/path"},
        }

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == ExitCode.SUCCESS

    def test_main_non_commit_command_allows(self) -> None:
        """Non-commit git commands should be allowed through."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
        }

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == ExitCode.SUCCESS

    def test_main_invalid_json_blocks(self) -> None:
        """Invalid JSON input should block (fail-closed)."""
        with patch("sys.stdin", StringIO("not valid json")):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == ExitCode.BLOCKED

    def test_main_invalid_tool_input_type_allows(self) -> None:
        """tool_input that is not a dict should allow through."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": "string instead of dict",
        }

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == ExitCode.SUCCESS

    def test_main_git_commit_no_staged_files_allows(self) -> None:
        """Git commit with no staged files should allow through."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
        }

        mock_git_result = MagicMock()
        mock_git_result.stdout = ""

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch("check_secrets.subprocess.run", return_value=mock_git_result):
                with patch("check_secrets.parse_env_file", return_value={}):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        assert exc_info.value.code == ExitCode.SUCCESS

    def test_main_git_commit_with_secrets_blocks(self) -> None:
        """Git commit with secrets in staged files should block."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
        }

        staged_files_result = MagicMock()
        staged_files_result.stdout = "config.py\n"

        staged_content_result = MagicMock()
        secret_key = "sk-ant-" + "x" * 30
        staged_content_result.stdout = f"api_key = '{secret_key}'"

        def mock_subprocess_run(
            cmd: list[str],
            *,
            capture_output: bool = False,
            text: bool = False,
            check: bool = False,
            timeout: int | None = None,
        ) -> MagicMock:
            if "diff" in cmd:
                return staged_files_result
            if "show" in cmd:
                return staged_content_result
            return MagicMock(stdout="")

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch(
                "check_secrets.subprocess.run", side_effect=mock_subprocess_run
            ):
                with patch("check_secrets.parse_env_file", return_value={}):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        assert exc_info.value.code == ExitCode.BLOCKED

    def test_main_git_commit_clean_files_allows(self) -> None:
        """Git commit with clean staged files should allow through."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
        }

        staged_files_result = MagicMock()
        staged_files_result.stdout = "clean.py\n"

        staged_content_result = MagicMock()
        staged_content_result.stdout = "def hello():\n    print('Hello')\n"

        def mock_subprocess_run(
            cmd: list[str],
            *,
            capture_output: bool = False,
            text: bool = False,
            check: bool = False,
            timeout: int | None = None,
        ) -> MagicMock:
            if "diff" in cmd:
                return staged_files_result
            if "show" in cmd:
                return staged_content_result
            return MagicMock(stdout="")

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch(
                "check_secrets.subprocess.run", side_effect=mock_subprocess_run
            ):
                with patch("check_secrets.parse_env_file", return_value={}):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        assert exc_info.value.code == ExitCode.SUCCESS

    def test_main_skips_binary_files(self) -> None:
        """Binary files should be skipped during checking."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
        }

        staged_files_result = MagicMock()
        staged_files_result.stdout = "image.png\ndata.db\n"

        def mock_subprocess_run(
            cmd: list[str],
            *,
            capture_output: bool = False,
            text: bool = False,
            check: bool = False,
            timeout: int | None = None,
        ) -> MagicMock:
            if "diff" in cmd:
                return staged_files_result
            return MagicMock(stdout="")

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch(
                "check_secrets.subprocess.run", side_effect=mock_subprocess_run
            ):
                with patch("check_secrets.parse_env_file", return_value={}):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        assert exc_info.value.code == ExitCode.SUCCESS

    def test_main_skips_env_files(self) -> None:
        """Env files should be skipped during checking."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
        }

        staged_files_result = MagicMock()
        staged_files_result.stdout = ".env\n.env.local\n"

        def mock_subprocess_run(
            cmd: list[str],
            *,
            capture_output: bool = False,
            text: bool = False,
            check: bool = False,
            timeout: int | None = None,
        ) -> MagicMock:
            if "diff" in cmd:
                return staged_files_result
            return MagicMock(stdout="")

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch(
                "check_secrets.subprocess.run", side_effect=mock_subprocess_run
            ):
                with patch("check_secrets.parse_env_file", return_value={}):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        assert exc_info.value.code == ExitCode.SUCCESS

    def test_main_git_diff_failure_blocks(self) -> None:
        """Failure to get staged files should block (fail-closed)."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
        }

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch(
                "check_secrets.subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "git"),
            ):
                with patch("check_secrets.parse_env_file", return_value={}):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        assert exc_info.value.code == ExitCode.BLOCKED

    def test_main_git_diff_timeout_blocks(self) -> None:
        """Timeout getting staged files should block (fail-closed)."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
        }

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch(
                "check_secrets.subprocess.run",
                side_effect=subprocess.TimeoutExpired("git", SUBPROCESS_TIMEOUT),
            ):
                with patch("check_secrets.parse_env_file", return_value={}):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        assert exc_info.value.code == ExitCode.BLOCKED

    def test_main_skips_oversized_staged_content(self) -> None:
        """Files with oversized staged content should be skipped."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
        }

        staged_files_result = MagicMock()
        staged_files_result.stdout = "huge.py\n"

        # Staged content exceeds MAX_FILE_SIZE (10MB)
        huge_content = "x" * (10 * 1024 * 1024 + 1)  # Just over 10MB
        staged_content_result = MagicMock()
        staged_content_result.stdout = huge_content

        def mock_subprocess_run(
            cmd: list[str],
            *,
            capture_output: bool = False,
            text: bool = False,
            check: bool = False,
            timeout: int | None = None,
        ) -> MagicMock:
            if "diff" in cmd:
                return staged_files_result
            if "show" in cmd:
                return staged_content_result
            return MagicMock(stdout="")

        with patch("sys.stdin", StringIO(json.dumps(input_data))):
            with patch(
                "check_secrets.subprocess.run", side_effect=mock_subprocess_run
            ):
                with patch("check_secrets.parse_env_file", return_value={}):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        assert exc_info.value.code == ExitCode.SUCCESS


# =============================================================================
# TestIntegration
# =============================================================================


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_workflow_with_real_env_file(self, tmp_path: Path) -> None:
        """Test complete workflow: parse, filter, and check file."""
        secret_value = "sk-ant-" + "x" * 30
        env_file = tmp_path / ".env"
        env_file.write_text(
            f"API_KEY={secret_value}\n"
            "DEBUG=true\n"
            "PORT=3000\n"
        )

        env_vars = parse_env_file(env_file)
        assert "API_KEY" in env_vars

        secret_vars = filter_env_values(env_vars)
        assert "API_KEY" in secret_vars
        assert "DEBUG" not in secret_vars
        assert "PORT" not in secret_vars

        env_patterns: dict[str, re.Pattern[str]] = {
            key: re.compile(rf"\b{re.escape(value)}\b")
            for key, value in secret_vars.items()
        }
        file_content = f'config = {{"api_key": "{env_vars["API_KEY"]}"}}'

        pattern_issues, env_issues = check_file_for_secrets(
            "config.py", file_content, env_patterns
        )

        assert len(env_issues) > 0

    def test_workflow_skip_env_files(self) -> None:
        """Verify .env files themselves are skipped."""
        assert is_env_file(".env") is True
        assert is_env_file(".env.local") is True
        assert is_env_file(".env.production") is True

    def test_workflow_skip_binary_files(self) -> None:
        """Verify binary files are skipped."""
        assert is_binary_file("image.png") is True
        assert is_binary_file("database.db") is True
        assert is_binary_file("config.json") is False

    def test_workflow_git_commit_trigger(self) -> None:
        """Verify git commit detection for hook trigger."""
        assert is_git_commit_command('git commit -m "test"') is True
        assert is_git_commit_command("git push") is False


# =============================================================================
# Main Entry Point
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
