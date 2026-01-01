import json
import time
import subprocess
import sys

def get_current_commit():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

def check_for_reviews(commit_sha):
    try:
        result = subprocess.run(
            ["gh", "pr", "view", "27", "--json", "reviews"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        reviews = data.get("reviews", [])
        
        matching_reviews = [
            r for r in reviews 
            if r.get('commit', {}).get('oid') == commit_sha
        ]
        
        if matching_reviews:
            return matching_reviews[-1]
        return None
    except Exception as e:
        return None

def main():
    commit = get_current_commit()
    print(f"Monitoring reviews for commit: {commit}")
    
    start_time = time.time()
    timeout = 10 * 60
    
    while time.time() - start_time < timeout:
        if review := check_for_reviews(commit):
            print("\nREVIEW DETECTED!")
            print(f"State: {review.get('state')}")
            print(f"Body: {review.get('body')}")
            
            body_lower = review.get('body', '').lower()
            state = review.get('state', '')
            
            if state == 'APPROVED' or "looks good" in body_lower or "lgtm" in body_lower or "ready to merge" in body_lower:
                print("\nVERDICT: READY TO MERGE")
            else:
                print("\nVERDICT: CHANGES REQUESTED (Likely)")
            
            sys.exit(0)
        
        time.sleep(30)
        print(".", end="", flush=True)

if __name__ == "__main__":
    main()
