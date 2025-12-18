#!/usr/bin/env python3
import json
import sys
import re
import subprocess
import os

def parse_env_file(env_path):
    """Parse a .env file and return a dictionary of key-value pairs."""
    env_vars = {}
    
    if not os.path.exists(env_path):
        return env_vars
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
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
    except (IOError, UnicodeDecodeError):
        pass
    
    return env_vars

def filter_env_values(env_vars):
    """Filter .env values to only include those that should be checked as secrets."""
    # Common non-secret values to skip
    skip_values = {
        'true', 'false', 'yes', 'no', 'on', 'off',
        'development', 'production', 'staging', 'test',
        'localhost', '127.0.0.1', '0.0.0.0',
        'utf-8', 'utf8', 'none', 'null'
    }
    
    filtered = {}
    for key, value in env_vars.items():
        # Skip short values (likely not secrets)
        if len(value) < 8:
            continue
        
        # Skip common non-secret values
        if value.lower() in skip_values:
            continue
        
        # Skip numeric-only values
        if value.isdigit():
            continue
        
        filtered[key] = value
    
    return filtered

def main():
    # Load hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    
    # Only check Git commit operations
    if tool_name != "Git" or "commit" not in command.lower():
        sys.exit(0)
    
    # Change to project directory if available
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        os.chdir(project_dir)
    
    # Load and filter .env values for secret detection
    env_path = os.path.join(project_dir, ".env") if project_dir else ".env"
    env_vars = parse_env_file(env_path)
    secret_env_values = filter_env_values(env_vars)
    
    # Get staged files
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        staged_files = [f for f in result.stdout.strip().split('\n') if f]
    except subprocess.CalledProcessError:
        sys.exit(0)
    
    if not staged_files:
        sys.exit(0)
    
    # Secret patterns to detect
    secret_patterns = [
        (r'(?i)(secret|token)\s*[:=]\s*[\'"]?[a-zA-Z0-9_\-]{20,}', "secret/token"),
        (r'(?i)(aws_access_key_id|aws_secret_access_key)\s*[:=]', "AWS credentials"),
        (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API key"),
        (r'AIza[0-9A-Za-z\-_]{35}', "Google API key"),
        (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token"),
        (r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}', "Bearer token"),
        (r'-----BEGIN (RSA |DSA )?PRIVATE KEY-----', "Private key"),
    ]
    
    issues = []
    
    # Check each staged file
    for file_path in staged_files:
        # Skip binary files and certain extensions
        if any(file_path.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip']):
            continue
        
        # Skip .env files themselves
        if file_path.endswith('.env') or '/.env' in file_path:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for pattern-based secrets
                for pattern, description in secret_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(f"{file_path}:{line_num} - Found potential {description}")
                
                # Check for hardcoded .env values
                for env_key, env_value in secret_env_values.items():
                    if env_value in content:
                        # Find all occurrences and report line numbers
                        lines = content.split('\n')
                        for line_num, line in enumerate(lines, 1):
                            if env_value in line:
                                issues.append(f"{file_path}:{line_num} - Found hardcoded value from .env key '{env_key}'")
        except (UnicodeDecodeError, FileNotFoundError, PermissionError):
            continue
    
    # If secrets found, block the commit
    if issues:
        print("🚨 SECURITY WARNING: Potential secrets detected in staged files!\n", file=sys.stderr)
        
        # Separate pattern-based and .env value detections
        pattern_issues = [i for i in issues if "hardcoded value from .env" not in i]
        env_issues = [i for i in issues if "hardcoded value from .env" in i]
        
        if pattern_issues:
            print("  Pattern-based detections:", file=sys.stderr)
            for issue in pattern_issues:
                print(f"    ❌ {issue}", file=sys.stderr)
            print("", file=sys.stderr)
        
        if env_issues:
            print("  Hardcoded .env values detected:", file=sys.stderr)
            for issue in env_issues:
                print(f"    ❌ {issue}", file=sys.stderr)
            print("", file=sys.stderr)
        
        print("⚠️  Please remove secrets before committing.", file=sys.stderr)
        if env_issues:
            print("💡 Use environment variables at runtime instead of hardcoding values from .env.", file=sys.stderr)
        print("💡 Consider using a secrets manager for sensitive credentials.\n", file=sys.stderr)
        sys.exit(2)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
