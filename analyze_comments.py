import json
import sys

try:
    with open('latest_comments.json', 'r') as f:
        comments = json.load(f)

    # Filter for comments newer than the Cycle 7 batch (approx 10:35Z)
    # Using 10:40:00Z to ensure we only see completely new feedback
    cutoff = '2025-12-05T10:40:00Z'
    new_comments = [c for c in comments if c.get('created_at', '') > cutoff]
    
    print(f"Total comments: {len(comments)}")
    print(f"New comments (Cycle 8?): {len(new_comments)}")

    # Sort by created_at
    new_comments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    for c in new_comments[:10]:
        print("-" * 40)
        print(f"Date: {c.get('created_at')}")
        print(f"File: {c.get('path')}")
        print(f"Line: {c.get('line') or c.get('original_line')}")
        print(f"Body: {c.get('body')}")

except Exception as e:
    print(f"Error: {e}")
