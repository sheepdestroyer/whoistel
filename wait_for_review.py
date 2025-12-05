import json
import time
import subprocess
import sys
import os

REQUIRED_COMMIT = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
print(f"Waiting for review on commit: {REQUIRED_COMMIT}")

def get_latest_review_for_commit(commit_sha):
    try:
        result = subprocess.run(
            ["gh", "pr", "view", "27", "--json", "reviews"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        reviews = data.get("reviews", [])
        
        # Filter for reviews on the specific commit
        # The structure is review['commit']['oid']
        
        matching_reviews = [
            r for r in reviews 
            if r.get('commit', {}).get('oid') == commit_sha
        ]
        
        if matching_reviews:
            return matching_reviews[-1] # Return the latest one for this commit
            
        return None
    except Exception as e:
        print(f"Error fetching reviews: {e}", file=sys.stderr)
        return None

def main():
    start_time = time.time()
    timeout_minutes = 10
    
    print(f"Polling for reviews on commit {REQUIRED_COMMIT}...")
    
    while time.time() - start_time < (timeout_minutes * 60):
        review = get_latest_review_for_commit(REQUIRED_COMMIT)
        if review:
            print("\nREVIEW RECEIVED!")
            print(f"State: {review.get('state')}")
            print(f"Submitted At: {review.get('submittedAt')}")
            print("Body:")
            print(review.get('body'))
            
            # Simple heuristic for "Ready to merge"
            body_lower = review.get('body', '').lower()
            state = review.get('state', '')
            
            if state == 'APPROVED' or "looks good" in body_lower or "lgtm" in body_lower or "ready to merge" in body_lower:
                print("\nVERDICT: READY TO MERGE")
            else:
                print("\nVERDICT: CHANGES REQUESTED (Likely)")
                
            return
        
        time.sleep(30)
        print(".", end="", flush=True)
    
    print("\nTimeout waiting for review.")
    sys.exit(1)

if __name__ == "__main__":
    main()
