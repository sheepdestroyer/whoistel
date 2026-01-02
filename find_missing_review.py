import json
import os

try:
    with open('pr29_full_debug.json', 'r') as f:
        data = json.load(f)
        
    print(f"Total reviews: {len(data.get('reviews', []))}")
    print(f"Total comments: {len(data.get('comments', []))}")
    
    print("\n--- REVIEWS ---")
    for r in data.get('reviews', []):
        print(f"ID: {r.get('id')} | Author: {r.get('author', {}).get('login')} | Date: {r.get('submittedAt')} | Commit: {r.get('commit', {}).get('oid')}")
        
    print("\n--- COMMENTS ---")
    for c in data.get('comments', []):
        print(f"ID: {c.get('id')} | Author: {c.get('author', {}).get('login')} | Date: {c.get('createdAt')}")
        
except Exception as e:
    print(f"Error: {e}")
