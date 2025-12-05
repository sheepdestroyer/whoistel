
import json
import os

target_review_id = 3545329757

def check_status():
    with open('all_reviews.json') as f:
        reviews = json.load(f)
    with open('all_comments.json') as f:
        comments = json.load(f)

    # Find start time
    start_time = next((r['submitted_at'] for r in reviews if r['id'] == target_review_id), None)
    if not start_time:
        print("Target review not found")
        return

    print(f"Checking reviews since: {start_time}")
    
    # Filter content
    relevant_reviews = [r for r in reviews if r['submitted_at'] >= start_time]
    review_ids = {r['id'] for r in relevant_reviews}
    relevant_comments = [c for c in comments if c.get('pull_request_review_id') in review_ids]

    print(f"Found {len(relevant_comments)} comments to verify.")

    # Check files
    for c in relevant_comments:
        path = c['path']
        body = c['body']
        line = c.get('line')
        
        print(f"\n--- Checking {path}:{line} ---")
        print(f"Comment: {body[:100]}...")
        
        if not os.path.exists(path):
            print(f"File {path} DOES NOT EXIST (Good if it was a file to delete, Bad otherwise)")
            continue
            
        with open(path) as f:
            content = f.read()
            
        # Heuristics for verification
        if "auth_status.txt" in path or "gh_help.txt" in path or "manual_" in path:
             print("STATUS: FAIL - Sensitive/Temp file exists!")
        elif "setup_db_connection" in body and "contextlib.closing" in body:
             if "with closing(setup_db_connection())" in content:
                 print("STATUS: PASS - closing() used")
             else:
                 print("STATUS: FAIL - closing() NOT used")
        elif "kwargs in-place" in body:
             if "kwargs['conn'] = new_conn" in content and "del kwargs['conn']" in content:
                 print("STATUS: PASS - Optimization present")
             else:
                 print("STATUS: FAIL - Optimization missing")
        elif "strip()" in body:
             if ".strip()" in content:
                 print("STATUS: PASS - strip() present")
             else:
                 print("STATUS: FAIL - strip() missing")
        elif "uniquement des chiffres" in body:
             if "uniquement des chiffres après nettoyage" in content:
                 print("STATUS: PASS - Error message updated")
             else:
                 print("STATUS: FAIL - Error message outdated")
        elif ".gitignore" in path:
             if "auth_status.txt" in content:
                 print("STATUS: PASS - .gitignore updated")
             else:
                 print("STATUS: FAIL - .gitignore missing entries")
        else:
             print("STATUS: MANUAL CHECK REQUIRED")

if __name__ == "__main__":
    check_status()
