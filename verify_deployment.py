#!/usr/bin/env python3
"""
Pre-deployment verification script for Telegram Scraper Dashboard.

Run this before pushing to GitHub to ensure all sensitive files are properly excluded
and configuration is correct.

Usage:
    python verify_deployment.py
"""

import json
import os
import sys
from pathlib import Path


def print_status(message: str, status: str = "INFO"):
    """Print a status message with formatting."""
    colors = {
        "INFO": "\033[94m",      # Blue
        "OK": "\033[92m",        # Green
        "WARN": "\033[93m",      # Yellow
        "ERROR": "\033[91m",     # Red
        "RESET": "\033[0m",
    }
    color = colors.get(status, colors["INFO"])
    reset = colors["RESET"]
    icon = {"INFO": "ℹ️ ", "OK": "✓", "WARN": "⚠ ", "ERROR": "✗"}
    print(f"{color}{icon.get(status, '')} {message}{reset}")


def check_sensitive_files():
    """Check that sensitive files exist locally but are in .gitignore."""
    print("\n" + "=" * 60)
    print("CHECKING SENSITIVE FILES")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    
    sensitive_files = {
        base_dir / "khemra_account.json": "Google service account key",
        base_dir / "tg_sessions": "Telegram session directory",
        base_dir / ".streamlit" / "secrets.toml": "Local Streamlit secrets",
    }
    
    all_good = True
    for file_path, description in sensitive_files.items():
        exists = file_path.exists()
        status = "OK" if exists else "WARN"
        symbol = "✓" if exists else "✗"
        print_status(f"{symbol} {description}: {'EXISTS' if exists else 'NOT FOUND (expected for deployment)'}", status)
        if not exists and "Google" in description:
            all_good = False
    
    return all_good


def check_gitignore():
    """Verify that sensitive files are in .gitignore."""
    print("\n" + "=" * 60)
    print("CHECKING .gitignore")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    gitignore_path = base_dir / ".gitignore"
    
    if not gitignore_path.exists():
        print_status("No .gitignore found!", "ERROR")
        return False
    
    with open(gitignore_path, "r") as f:
        gitignore_content = f.read()
    
    required_entries = [
        "khemra_account.json",
        "tg_sessions/",
        ".streamlit/secrets.toml",
        ".env",
    ]
    
    all_present = True
    for entry in required_entries:
        if entry in gitignore_content:
            print_status(f"'{entry}' is in .gitignore", "OK")
        else:
            print_status(f"'{entry}' is MISSING from .gitignore", "ERROR")
            all_present = False
    
    return all_present


def check_code_for_hardcoded_secrets():
    """Check that no hardcoded secrets are in Python files."""
    print("\n" + "=" * 60)
    print("CHECKING FOR HARDCODED SECRETS")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    
    dangerous_patterns = [
        "api_id",
        "api_hash",
        "PRIVATE KEY",
        "private_key",
        "BEGIN CERTIFICATE",
    ]
    
    py_files = list(base_dir.glob("*.py"))
    found_issues = False
    
    for py_file in py_files:
        with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        for pattern in dangerous_patterns:
            # Check if pattern appears to be hardcoded (not in get_deployment_setting or st.secrets)
            if pattern in content:
                # Allow if it's in get_deployment_setting or st.secrets.get
                if "get_deployment_setting" in content or "st.secrets" in content:
                    print_status(f"{py_file.name}: Uses safe secret loading", "OK")
                else:
                    print_status(f"{py_file.name}: May contain hardcoded '{pattern}'", "WARN")
                    found_issues = True
    
    if not found_issues:
        print_status("No obvious hardcoded secrets found", "OK")
    
    return not found_issues


def check_requirements():
    """Check that requirements.txt has essential dependencies."""
    print("\n" + "=" * 60)
    print("CHECKING requirements.txt")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    req_path = base_dir / "requirements.txt"
    
    if not req_path.exists():
        print_status("requirements.txt not found!", "ERROR")
        return False
    
    with open(req_path, "r") as f:
        requirements = f.read()
    
    essential = ["streamlit", "telethon", "gspread", "pandas", "plotly"]
    
    all_present = True
    for pkg in essential:
        if pkg in requirements:
            print_status(f"'{pkg}' found in requirements.txt", "OK")
        else:
            print_status(f"'{pkg}' MISSING from requirements.txt", "WARN")
            all_present = False
    
    return all_present


def check_git_status():
    """Check git status for uncommitted sensitive files."""
    print("\n" + "=" * 60)
    print("CHECKING GIT STATUS")
    print("=" * 60)
    
    try:
        import subprocess
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            print_status("Not a git repository or git not found", "WARN")
            return True
        
        git_status = result.stdout
        
        dangerous_files = [
            "khemra_account.json",
            "secrets.toml",
            ".env",
            ".session",
        ]
        
        all_good = True
        for line in git_status.split("\n"):
            for dangerous in dangerous_files:
                if dangerous in line:
                    print_status(f"DANGER: {line.strip()} - SHOULD NOT BE COMMITTED", "ERROR")
                    all_good = False
        
        if all_good and git_status.strip():
            print_status(f"Git status checked: {len(git_status.split(chr(10)))} items staged", "OK")
        elif not git_status.strip():
            print_status("Git status is clean", "OK")
        
        return all_good
    except Exception as e:
        print_status(f"Could not check git status: {e}", "WARN")
        return True


def check_secrets_template():
    """Check that secrets.toml.example exists."""
    print("\n" + "=" * 60)
    print("CHECKING SECRETS TEMPLATE")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    template_path = base_dir / ".streamlit" / "secrets.toml.example"
    
    if template_path.exists():
        print_status("secrets.toml.example exists", "OK")
        
        with open(template_path, "r") as f:
            content = f.read()
        
        required_keys = [
            "GOOGLE_SHEET_ID",
            "GOOGLE_WORKSHEET_NAME",
            "gcp_service_account",
            "TELEGRAM_API_ID",
            "TELEGRAM_API_HASH",
        ]
        
        all_present = True
        for key in required_keys:
            if key in content:
                print_status(f"Template has '{key}'", "OK")
            else:
                print_status(f"Template missing '{key}'", "WARN")
                all_present = False
        
        return all_present
    else:
        print_status("secrets.toml.example not found!", "ERROR")
        return False


def main():
    """Run all verification checks."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  PRE-DEPLOYMENT VERIFICATION FOR TELEGRAM SCRAPER       ║")
    print("╚" + "=" * 58 + "╝")
    
    checks = [
        ("Sensitive Files", check_sensitive_files),
        (".gitignore Configuration", check_gitignore),
        ("Hardcoded Secrets", check_code_for_hardcoded_secrets),
        ("requirements.txt", check_requirements),
        ("Git Status", check_git_status),
        ("Secrets Template", check_secrets_template),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_status(f"Error during {check_name}: {e}", "ERROR")
            results[check_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for check_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        color_status = "OK" if passed else "ERROR"
        print_status(f"{check_name}: {status}", color_status)
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print_status("✓ ALL CHECKS PASSED! Ready for deployment.", "OK")
        print_status("Next steps:", "INFO")
        print_status("  1. Push code to GitHub: git push origin main", "INFO")
        print_status("  2. Deploy to Streamlit Cloud", "INFO")
        print_status("  3. Add secrets in Streamlit Cloud dashboard", "INFO")
    else:
        print_status("✗ SOME CHECKS FAILED! Fix issues before deployment.", "ERROR")
        print_status("Review the items marked ERROR above.", "WARN")
    
    print()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
