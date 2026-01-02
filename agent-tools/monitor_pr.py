import json
import time
import subprocess
import sys
import argparse

def get_current_commit():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

def check_for_reviews(pr_number):
    try:
        result = subprocess.run(
            ["gh", "pr", "view", str(pr_number), "--json", "reviews"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        reviews = data.get("reviews", [])
        
        # Filter for reviews that are relevant (e.g., NOT DISMISSED)
        # matching_reviews = [r for r in reviews if r.get('commit', {}).get('oid') == commit_sha]
        # FIX: Do not filter by commit SHA, as reviews might come in for previous commits
        matching_reviews = reviews

        if matching_reviews:
            return matching_reviews[-1]
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR reviews: {e.stderr}", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print("Error decoding GitHub response", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error in monitor: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description='Monitor PR for reviews')
    parser.add_argument('pr_number', type=int, help='PR number to monitor')
    args = parser.parse_args()

    commit = get_current_commit()
    print(f"Monitoring reviews for PR {args.pr_number} on commit: {commit}")
    
    start_time = time.time()
    timeout = 10 * 60  # 10 minutes
    
    while time.time() - start_time < timeout:
        if review := check_for_reviews(args.pr_number):
            print(json.dumps(review, indent=2))
            sys.exit(0)
        
        time.sleep(30)
        print(".", end="", flush=True)
    
    print("\n\nTimeout: No review detected after 10 minutes.")
    sys.exit(1)

if __name__ == "__main__":
    main()
