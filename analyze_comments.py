import json

try:
    with open('inline_comments.json', 'r') as f:
        comments = json.load(f)

    print(f"Total comments: {len(comments)}")
    
    # Sort by id (assuming higher id is newer) or created_at
    comments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    last_5 = comments[:5]
    
    for c in last_5:
        print("-" * 40)
        print(f"Date: {c.get('created_at')}")
        print(f"File: {c.get('path')}")
        print(f"Line: {c.get('line') or c.get('original_line')}")
        print(f"Body: {c.get('body')}")

except Exception as e:
    print(f"Error: {e}")
