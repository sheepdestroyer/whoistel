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
    parser.add_argument('since', help='Filter reviews after this date (ISO 8601 format)', nargs='?', default="2026-01-02T00:17:24Z")
    parser.add_argument('--timeout', type=int, default=1200, help='Timeout in seconds')
    return parser.parse_args()

def fetch_reviews(pr_number, temp_dir):
    output_path = os.path.join(temp_dir, "reviews_temp.json")
    try:
        # Fetch reviews using list args instead of shell=True for security
        subprocess.run(
            ["gh", "api", f"repos/sheepdestroyer/whoistel/pulls/{pr_number}/reviews"],
            check=True,
            stdout=open(output_path, 'w'),
            stderr=subprocess.PIPE,
            text=True
        )
        with open(output_path) as f:
            return json.load(f)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching reviews: {e.stderr}", file=sys.stderr)
        return []
    except json.JSONDecodeError:
        print("Error decoding JSON response", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return []

def main():
    args = parse_args()
    print(f"Polling for reviews newer than {args.since} for {args.timeout}s...")

    with tempfile.TemporaryDirectory() as temp_dir:
        start = time.time()
        
        while time.time() - start < args.timeout:
            reviews = fetch_reviews(args.pr_number, temp_dir)
            new_reviews = []
            
            for r in reviews:
                # Basic ISO comparison (strings work if format is consistent Z)
                if r.get('submitted_at') and r['submitted_at'] > args.since:
                    new_reviews.append(r)
            
            if new_reviews:
                print(f"\nFound {len(new_reviews)} new reviews!")
                # Output to stdout JSON for the agent to capture, instead of a file
                print(json.dumps(new_reviews, indent=2))
                sys.exit(0)
            
            print(".", end="", flush=True)
            time.sleep(30)

    print("\nTimeout: No new reviews detected.")
    sys.exit(1)

if __name__ == "__main__":
    main()
