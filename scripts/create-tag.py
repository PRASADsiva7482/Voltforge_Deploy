#!/usr/bin/env python3
"""
=============================================================================
VoltForge Unified Git Tag & Release Manager
Standardized Tag Rule:
  Format: v<Major>.<Sprint>.<Bugs>-<env>-<YYYYMMDD><Count:03d>
  Example: v1.0.0-dev-20260923001
           v1.0.0-qa-20260923001

Components Supported:
  • ui       (Voltforge_UI)
  • bl       (Voltforge_BL)
  • ai       (Voltforge_AI)
  • keycloak (keycloak-26.4.7)
  • all      (All 4 components simultaneously)
=============================================================================
"""

import os
import sys
import re
import datetime
import subprocess
import argparse

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

REPO_MAP = {
    "ui": os.path.join(ROOT_DIR, "Voltforge_UI"),
    "bl": os.path.join(ROOT_DIR, "Voltforge_BL"),
    "ai": os.path.join(ROOT_DIR, "Voltforge_AI"),
    "keycloak": os.path.join(ROOT_DIR, "keycloak-26.4.7"),
}


def get_existing_tags(repo_dir):
    """Retrieve all git tags from repository."""
    try:
        res = subprocess.run(
            ["git", "-C", repo_dir, "tag", "-l"],
            capture_output=True,
            text=True,
            check=True
        )
        return [t.strip() for t in res.stdout.splitlines() if t.strip()]
    except Exception as e:
        print(f"[!] Warning: Unable to read tags from {repo_dir}: {e}")
        return []


def generate_tag(repo_dir, major=1, sprint=0, bugs=0, env="dev", custom_date=None, force_count=None):
    """
    Generate tag conforming to standard rule:
    v<Major>.<Sprint>.<Bugs>-<env>-<YYYYMMDD><count:03d>
    """
    date_str = custom_date or datetime.datetime.now().strftime("%Y%m%d")
    base_prefix = f"v{major}.{sprint}.{bugs}-{env}-{date_str}"

    if force_count is not None:
        count = int(force_count)
    else:
        existing_tags = get_existing_tags(repo_dir)
        # Find all tags matching base_prefix followed by 3 digits
        pattern = re.compile(rf"^{re.escape(base_prefix)}(\d{{3}})$")
        matched_counts = []
        for tag in existing_tags:
            m = pattern.match(tag)
            if m:
                matched_counts.append(int(m.group(1)))
        
        count = (max(matched_counts) + 1) if matched_counts else 1

    return f"{base_prefix}{count:03d}"


def create_and_push_tag(repo_key, repo_dir, tag, push=False):
    """Create local tag and optionally push to origin."""
    print(f"\n[*] Repository: {repo_key.upper()} ({repo_dir})")
    print(f"    Target Tag: {tag}")

    # Check if working directory is clean or has commits
    try:
        res = subprocess.run(
            ["git", "-C", repo_dir, "status", "-s"],
            capture_output=True,
            text=True
        )
        if res.stdout.strip():
            print("    [!] Notice: Repository has uncommitted local modifications.")
    except Exception:
        pass

    try:
        # Create tag
        subprocess.run(
            ["git", "-C", repo_dir, "tag", tag],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"    [+] Created local git tag: {tag}")
    except subprocess.CalledProcessError as e:
        print(f"    [!] Error creating tag '{tag}': {e.stderr.strip()}")
        return False

    if push:
        print(f"    [*] Pushing tag '{tag}' to origin...")
        try:
            subprocess.run(
                ["git", "-C", repo_dir, "push", "origin", tag],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"    [+] Tag '{tag}' pushed successfully to GitHub! CI/CD triggered.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"    [!] Error pushing tag '{tag}': {e.stderr.strip()}")
            return False
    else:
        print(f"    [i] Tag created locally. Push with: git -C {repo_dir} push origin {tag}")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="VoltForge Standardized Tag & Release Tool (v<Major>.<Sprint>.<Bugs>-<env>-<YYYYMMDD><Count>)"
    )
    parser.add_argument(
        "--repo",
        choices=["ui", "bl", "ai", "keycloak", "all"],
        default="all",
        help="Target repository to tag (ui, bl, ai, keycloak, or all)"
    )
    parser.add_argument("--major", type=int, default=1, help="Major version (default: 1)")
    parser.add_argument("--sprint", type=int, default=0, help="Sprint index (default: 0)")
    parser.add_argument("--bugs", type=int, default=0, help="Bug / fix counter (default: 0)")
    parser.add_argument("--env", choices=["dev", "qa", "prod"], default="dev", help="Release stage (dev, qa, prod; default: dev)")
    parser.add_argument("--date", type=str, default=None, help="Custom date YYYYMMDD (default: current date)")
    parser.add_argument("--count", type=int, default=None, help="Force specific 3-digit counter (default: auto-increment)")
    parser.add_argument("--push", action="store_true", help="Automatically push tag to origin to trigger CI/CD pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Print generated tag without creating or pushing it")

    args = parser.parse_args()

    targets = list(REPO_MAP.keys()) if args.repo == "all" else [args.repo]

    print("=" * 65)
    print("  VoltForge Tag Rule: v<Major>.<Sprint>.<Bugs>-<env>-<YYYYMMDD><Count>")
    print(f"  Configuration: Major=v{args.major} | Sprint={args.sprint} | Bugs={args.bugs} | Env={args.env}")
    print("=" * 65)

    for target in targets:
        repo_dir = REPO_MAP[target]
        if not os.path.exists(repo_dir):
            print(f"[!] Directory not found for {target}: {repo_dir}")
            continue

        tag = generate_tag(
            repo_dir,
            major=args.major,
            sprint=args.sprint,
            bugs=args.bugs,
            env=args.env,
            custom_date=args.date,
            force_count=args.count
        )

        if args.dry_run:
            print(f"  -> [{target.upper()}]: {tag} (dry-run)")
        else:
            create_and_push_tag(target, repo_dir, tag, push=args.push)

    print("\n" + "=" * 65)
    print("  Done.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
