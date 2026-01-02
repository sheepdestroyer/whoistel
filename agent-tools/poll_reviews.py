import json
import time
import subprocess
import sys
import tempfile
import os
from datetime import datetime

# Can be overridden by CLI args
LAST_REVIEW_DATE = sys.argv[1] if len(sys.argv) > 1 else "2026-01-02T00:17:24Z"
PR_NUMBER = 29
TIMEOUT = 1200  # 20 minutes

def fetch_reviews(temp_dir):
    output_path = os.path.join(temp_dir, "reviews_temp.json")
    try:
        # Fetch reviews
        subprocess.run(
            f"gh api repos/sheepdestroyer/whoistel/pulls/{PR_NUMBER}/reviews > {output_path}",
            shell=True, check=True, stderr=subprocess.DEVNULL
        )
        with open(output_path) as f:
            return json.load(f)
    except Exception:
        return []

def main():
    print(f"Polling for reviews newer than {LAST_REVIEW_DATE} for {TIMEOUT}s...")

    with tempfile.TemporaryDirectory() as temp_dir:
        start = time.time()
        
        while time.time() - start < TIMEOUT:
            reviews = fetch_reviews(temp_dir)
            new_reviews = []
            
            for r in reviews:
                # Basic ISO comparison (strings work if format is consistent Z)
                if r.get('submitted_at') and r['submitted_at'] > LAST_REVIEW_DATE:
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
