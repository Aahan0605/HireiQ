import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.supabase_client import fetch_candidate_by_id

async def main():
    from db.supabase_client import fetch_all_candidates
    print("Fetching all candidates...")
    try:
        candidates = await fetch_all_candidates()
        print(f"Found {len(candidates)} candidates:")
        import pprint
        for c in candidates:
            print("---")
            print(f"ID: {c.get('id')}, Name: {c.get('name')}")
            pprint.pprint(c)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
