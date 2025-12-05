import json
import sys

try:
    with open('comments_c26.json', 'r') as f:
        comments = json.load(f)
    
    # Filter for newest comments.
    cutoff = "2025-12-05T15:15:00Z"
    
    new_comments = [c for c in comments if c.get('created_at', '') > cutoff]
    
    print(f"Found {len(new_comments)} new comments.")
    
    for c in new_comments:
        print("="*60)
        print(f"File: {c.get('path')}")
        print(f"Line: {c.get('line')}")
        print(f"Body:\n{c.get('body')}")
        print("="*60)

except Exception as e:
    print(f"Error: {e}")
