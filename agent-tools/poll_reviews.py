import json
import time
import subprocess
import sys
import tempfile
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Poll PR for reviews')
    parser.add_argument('pr_number', type=int, help='PR number to monitor')
    parser.add_argument('--since', help='Filter reviews after this date (ISO 8601 format)', default="2026-01-02T00:17:24Z")
    parser.add_argument('--timeout', type=int, default=1200, help='Timeout in seconds')
    parser.add_argument('--initial-wait', type=int, default=180, help='Initial wait in seconds')
    parser.add_argument('--interval', type=int, default=120, help='Polling interval in seconds')
    parser.add_argument('--output', help='Output file path', default=None)
    return parser.parse_args()

def fetch_json(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching: {e}", file=sys.stderr)
        return []

def get_feedback_counts(pr_number):
    reviews = fetch_json(["gh", "api", f"repos/sheepdestroyer/whoistel/pulls/{pr_number}/reviews", "--paginate"])
    comments = fetch_json(["gh", "api", f"repos/sheepdestroyer/whoistel/pulls/{pr_number}/comments", "--paginate"])
    issue_comments = fetch_json(["gh", "api", f"repos/sheepdestroyer/whoistel/issues/{pr_number}/comments", "--paginate"])
    return reviews, comments, issue_comments

def main():
    args = parse_args()
    print(f"Polling PR #{args.pr_number} for activity since {args.since}...", file=sys.stderr)
    
    if args.initial_wait > 0:
        time.sleep(args.initial_wait)

    start_time = time.time()
    
    while time.time() - start_time < args.timeout:
        reviews, comments, is_comments = get_feedback_counts(args.pr_number)
        
        new_items = []
        
        # Helper to check dates
        def check_items(items, type_label):
            count = 0
            for item in items:
                ts = item.get('submitted_at') or item.get('updated_at') or item.get('created_at')
                if ts and ts > args.since:
                    item['_type'] = type_label
                    new_items.append(item)
                    count += 1
            return count

        n_rev = check_items(reviews, 'review_summary')
        n_com = check_items(comments, 'inline_comment')
        n_iss = check_items(is_comments, 'issue_comment')
        
        if new_items:
            print(f"\nNew Feedback Found! (Reviews: {n_rev}, Inline: {n_com}, General: {n_iss})", file=sys.stderr)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(new_items, f, indent=2)
                print(f"Written to {args.output}", file=sys.stderr)
            else:
                print(json.dumps(new_items, indent=2))
            sys.exit(0)
            
        print(".", end="", flush=True, file=sys.stderr)
        time.sleep(args.interval)

    print("\nTimeout: No new feedback detected.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
