import json
import sys

try:
    filename = sys.argv[1] if len(sys.argv) > 1 else 'pr29_full_debug.json'
    with open(filename, 'r') as f:
        data = json.load(f)
        
    print(f"Total reviews: {len(data.get('reviews', []))}")
    print(f"Total comments: {len(data.get('comments', []))}")
    
    print("\n--- REVIEWS ---")
    for r in data.get('reviews', []):
        print(f"ID: {r.get('id')} | Author: {r.get('author', {}).get('login')} | Date: {r.get('submittedAt')} | Commit: {r.get('commit', {}).get('oid')}")
        
    print("\n--- COMMENTS ---")
    for c in data.get('comments', []):
        print(f"ID: {c.get('id')} | Author: {c.get('author', {}).get('login')} | Date: {c.get('createdAt')}")
        
except FileNotFoundError:
    print(f"Error: {filename} not found")
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON format - {e}")
except KeyError as e:
    print(f"Error: Unexpected JSON structure - missing key {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
