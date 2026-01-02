#!/usr/bin/env python3
"""
Unified helper script for managing the GitHub PR review cycle, 
including triggering reviews, monitoring feedback, and verifying fixes.
"""
import json
import time
import subprocess
import sys
import os
import argparse
from datetime import datetime

# Centralized constants
DEFAULT_OWNER = os.environ.get("GH_OWNER", "sheepdestroyer")
DEFAULT_REPO = os.environ.get("GH_REPO", "whoistel")

def run_gh_api(path, paginate=True):
    """Executes a GitHub API call using the gh CLI and returns the JSON response."""
    cmd = ["gh", "api", path]
    if paginate:
        cmd.append("--paginate")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error calling GitHub API: {e.stderr}", file=sys.stderr)
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON from GitHub API at {path}", file=sys.stderr)
        return []

def get_all_feedback(pr_number, owner=DEFAULT_OWNER, repo=DEFAULT_REPO):
    """Fetches Reviews, Inline Comments, and Issue Comments from GitHub."""
    base_path = f"repos/{owner}/{repo}"
    reviews = run_gh_api(f"{base_path}/pulls/{pr_number}/reviews")
    inline_comments = run_gh_api(f"{base_path}/pulls/{pr_number}/comments")
    issue_comments = run_gh_api(f"{base_path}/issues/{pr_number}/comments")
    return {
        "reviews": reviews,
        "inline_comments": inline_comments,
        "issue_comments": issue_comments
    }

def filter_feedback_since(feedback, since_iso):
    """Filters results to items newer than since_iso."""
    new_items = []
    
    def process_items(items, label):
        count = 0
        for item in items:
            # GitHub uses multiple keys for timestamps; we take the most relevant one
            ts = item.get('submitted_at') or item.get('updated_at') or item.get('created_at')
            if ts and ts > since_iso:
                new_items.append({**item, '_type': label})
                count += 1
        return count

    counts = {
        "reviews": process_items(feedback['reviews'], 'review_summary'),
        "inline": process_items(feedback['inline_comments'], 'inline_comment'),
        "general": process_items(feedback['issue_comments'], 'issue_comment')
    }
    return new_items, counts

def cmd_trigger(args):
    """Triggers reviews from Gemini and CodeRabbit."""
    print(f"Triggering reviews for PR #{args.pr_number}...", file=sys.stderr)
    subprocess.run(["gh", "pr", "comment", str(args.pr_number), "--body", "/gemini review"], check=True)
    subprocess.run(["gh", "pr", "comment", str(args.pr_number), "--body", "@coderabbitai review"], check=True)
    subprocess.run(["gh", "pr", "comment", str(args.pr_number), "--body", "@sourcery-ai review"], check=True)
    print("Reviews triggered successfully.", file=sys.stderr)

def cmd_fetch(args):
    """One-shot fetch of all new feedback."""
    feedback = get_all_feedback(args.pr_number, args.owner, args.repo)
    new_items, counts = filter_feedback_since(feedback, args.since)
    
    if new_items:
        print(f"Found new feedback: {counts}", file=sys.stderr)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(new_items, f, indent=2)
            print(f"Written to {args.output}", file=sys.stderr)
        else:
            print(json.dumps(new_items, indent=2))
    else:
        print(f"No new feedback since {args.since}.", file=sys.stderr)

def cmd_monitor(args):
    """Polls for new feedback until timeout."""
    print(f"Monitoring PR #{args.pr_number} for activity since {args.since}...", file=sys.stderr)
    
    if args.initial_wait > 0:
        print(f"Waiting {args.initial_wait}s before first check...", file=sys.stderr)
        time.sleep(args.initial_wait)

    start_time = time.time()
    while time.time() - start_time < args.timeout:
        feedback = get_all_feedback(args.pr_number, args.owner, args.repo)
        new_items, counts = filter_feedback_since(feedback, args.since)
        
        if new_items:
            print(f"\nNew Feedback Detected: {counts}", file=sys.stderr)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(new_items, f, indent=2)
                print(f"Successfully written to {args.output}", file=sys.stderr)
            else:
                print(json.dumps(new_items, indent=2))
            sys.exit(0)
            
        print(".", end="", flush=True, file=sys.stderr)
        time.sleep(args.interval)

    print("\nTimeout reached. No new feedback detected.", file=sys.stderr)
    sys.exit(1)

def cmd_verify(args):
    """Heuristic verification of local files against recent comments."""
    # This logic is adapted from the old verify_comments.py
    if not os.path.exists(args.file):
        print(f"Error: JSON feedback file '{args.file}' not found. Run 'fetch' first.", file=sys.stderr)
        sys.exit(1)
        
    with open(args.file) as f:
        comments = json.load(f)

    print(f"Verifying {len(comments)} feedback items against local files...", file=sys.stderr)
    
    for c in comments:
        path = c.get('path')
        body = c.get('body', '')
        line = c.get('line')
        
        if not path:
            continue

        # Prevent path traversal attacks by ensuring the path is within the project
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        full_path = os.path.abspath(os.path.join(project_root, path))

        if not full_path.startswith(project_root) or not os.path.exists(full_path):
            continue

        print(f"\n[{path}:{line}] {body[:60]}...", file=sys.stderr)
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Heuristics
        if "new_kwargs = kwargs.copy()" in content:
            print("  STATUS: PASS - Safe decorator kwargs handling found", file=sys.stderr)
        elif "with closing(setup_db_connection())" in content:
             print("  STATUS: PASS - setup_db_connection wrapped in closing", file=sys.stderr)
        elif "uniquement des chiffres après nettoyage" in content:
             print("  STATUS: PASS - CLI error message updated", file=sys.stderr)
        else:
             print("  STATUS: MANUAL VERIFICATION REQUIRED", file=sys.stderr)

def main():
    """Main entry point for pr_helper.py CLI."""
    parser = argparse.ArgumentParser(description='Unified PR Review Cycle Helper')
    parser.add_argument('--owner', default=DEFAULT_OWNER, help='GitHub repository owner')
    parser.add_argument('--repo', default=DEFAULT_REPO, help='GitHub repository name')
    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')

    # Trigger
    p_trigger = subparsers.add_parser('trigger', help='Trigger new reviews from bots')
    p_trigger.add_argument('pr_number', type=int)

    # Fetch
    p_fetch = subparsers.add_parser('fetch', help='One-shot fetch of new feedback')
    p_fetch.add_argument('pr_number', type=int)
    p_fetch.add_argument('--since', default="1970-01-01T00:00:00Z", help='ISO 8601 timestamp')
    p_fetch.add_argument('--output', help='File path to write JSON results')

    # Monitor
    p_monitor = subparsers.add_parser('monitor', help='Poll for new feedback until timeout')
    p_monitor.add_argument('pr_number', type=int)
    p_monitor.add_argument('--since', default="1970-01-01T00:00:00Z")
    p_monitor.add_argument('--timeout', type=int, default=1200)
    p_monitor.add_argument('--initial-wait', type=int, default=180)
    p_monitor.add_argument('--interval', type=int, default=120)
    p_monitor.add_argument('--output', help='File path to write JSON results')

    # Verify
    p_verify = subparsers.add_parser('verify', help='Heuristic verification of local fixes')
    p_verify.add_argument('file', help='JSON file containing comments (from fetch/monitor)')

    args = parser.parse_args()

    if args.command == 'trigger': cmd_trigger(args)
    elif args.command == 'fetch': cmd_fetch(args)
    elif args.command == 'monitor': cmd_monitor(args)
    elif args.command == 'verify': cmd_verify(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
