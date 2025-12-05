import json
import sys

TARGET_REVIEW_ID = 3545329757

def main():
    try:
        with open('all_reviews.json', 'r') as f:
            reviews = json.load(f)
        with open('all_comments.json', 'r') as f:
            comments = json.load(f)
            
        # Find the target review
        target_review = next((r for r in reviews if r['id'] == TARGET_REVIEW_ID), None)
        
        if not target_review:
            print(f"Target review ID {TARGET_REVIEW_ID} not found.")
            # Fallback: just show recent reviews? No, let's list IDs to debug.
            print("Available Review IDs (first 10):")
            for r in reviews[:10]:
                print(f"{r['id']} - {r['submitted_at']}")
            return

        target_date = target_review['submitted_at']
        print(f"Target Review Found: {TARGET_REVIEW_ID} at {target_date}")
        
        # Filter reviews since target (inclusive)
        relevant_reviews = [r for r in reviews if r['submitted_at'] >= target_date]
        relevant_review_ids = {r['id'] for r in relevant_reviews}
        
        print(f"Found {len(relevant_reviews)} reviews since {target_date}")
        
        # Filter comments belonging to these reviews
        # Note: 'pull_request_review_id' links comment to review
        relevant_comments = [c for c in comments if c.get('pull_request_review_id') in relevant_review_ids]
        
        print(f"Found {len(relevant_comments)} comments in these reviews.")
        print("="*60)
        
        for c in relevant_comments:
            print(f"File: {c['path']}")
            print(f"Line: {c.get('line')}")
            print(f"Review ID: {c.get('pull_request_review_id')}")
            print(f"Body:\n{c['body']}")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
