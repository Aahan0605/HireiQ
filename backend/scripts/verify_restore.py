import argparse
import sys
import os

# Parse args first, before importing local modules that check environment variables on import
parser = argparse.ArgumentParser(description="Sanity check for restored Supabase project")
parser.add_argument("--url", required=True, help="Restored Supabase project URL")
parser.add_argument("--key", required=True, help="Restored Supabase API key (anon or service_role)")
parser.add_argument("--expected-candidates", type=int, help="Expected candidate count")
parser.add_argument("--prod-url", help="Production Supabase project URL for comparison")
parser.add_argument("--prod-key", help="Production Supabase API key for comparison")
parser.add_argument("--encryption-key", help="Symmetric field encryption key")
args = parser.parse_args()

# Load env variables from .env if present
from dotenv import load_dotenv
load_dotenv()

# Override FIELD_ENCRYPTION_KEY if provided as argument
if args.encryption_key:
    os.environ["FIELD_ENCRYPTION_KEY"] = args.encryption_key

# Now import supabase and decryption utilities
from supabase import create_client

try:
    # Set sys.path so we can import api modules
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from api.core.encryption import decrypt_field
except Exception as e:
    print(f"[-] Could not import decrypt_field: {e}")
    sys.exit(1)

def check_table_exists_and_count(client, table_name):
    try:
        res = client.table(table_name).select("*", count="exact").limit(0).execute()
        return True, res.count
    except Exception as e:
        return False, str(e)

def run_verification():
    print("=" * 60)
    print(" HIREIQ RESTORE VERIFICATION RUNNER ")
    print("=" * 60)
    
    # 1. Connect to restored client
    try:
        restored_client = create_client(args.url, args.key)
        print("[+] Successfully initialized restored Supabase client.")
    except Exception as e:
        print(f"[-] Failed to initialize restored Supabase client: {e}")
        return False

    failures = []
    
    # 2. Check all tables exist and get counts
    tables_to_check = ["recruiters", "jobs", "candidates", "interviews", "candidate_notes"]
    counts = {}
    
    print("\n--- Checking Table Presence and Record Counts ---")
    for tbl in tables_to_check:
        exists, result = check_table_exists_and_count(restored_client, tbl)
        if exists:
            counts[tbl] = result
            print(f"[PASS] Table '{tbl}' exists. Record count: {result}")
        else:
            failures.append(f"Table '{tbl}' does not exist or cannot be queried: {result}")
            print(f"[FAIL] Table '{tbl}' - Error: {result}")
            
    # 3. Check candidate count matches expected or production
    print("\n--- Verifying Candidate Count ---")
    prod_candidates_count = None
    if args.prod_url and args.prod_key:
        try:
            prod_client = create_client(args.prod_url, args.prod_key)
            exists, result = check_table_exists_and_count(prod_client, "candidates")
            if exists:
                prod_candidates_count = result
                print(f"[+] Retrieved candidate count from production: {prod_candidates_count}")
            else:
                print(f"[WARN] Failed to query production candidates count: {result}")
        except Exception as e:
            print(f"[WARN] Failed to query production candidates count: {e}")
            
    expected_count = args.expected_candidates
    if expected_count is None and prod_candidates_count is not None:
        expected_count = prod_candidates_count
        
    if "candidates" in counts:
        actual_count = counts["candidates"]
        if expected_count is not None:
            if actual_count == expected_count:
                print(f"[PASS] Candidate count matches expected ({expected_count}).")
            else:
                failures.append(f"Candidate count mismatch. Expected: {expected_count}, Actual: {actual_count}")
                print(f"[FAIL] Candidate count mismatch. Expected: {expected_count}, Actual: {actual_count}")
        else:
            print(f"[INFO] Skipping candidate count comparison (no expected count or production count available). Current: {actual_count}")
            
    # 4. Fetch one candidate and decrypt resume_text
    print("\n--- Testing Data Integrity and Decryption ---")
    if "candidates" in counts:
        try:
            # Try to find one candidate with encrypted raw_text (starting with Fernet prefix 'gAAAAA')
            res = restored_client.table("candidates").select("id, full_name, raw_text").like("raw_text", "gAAAAA%").limit(1).execute()
            if res.data:
                cand = res.data[0]
                cand_id = cand.get("id")
                name = cand.get("full_name") or "Unknown"
                raw_text = cand.get("raw_text") or ""
                
                decrypted = decrypt_field(raw_text)
                if decrypted == "[unable to decrypt]":
                    failures.append("Decryption failed. Obtained '[unable to decrypt]' placeholder.")
                    print(f"[FAIL] Decryption failed for candidate {name} (ID: {cand_id}). Check encryption key.")
                elif not decrypted.strip():
                    failures.append("Decryption returned empty string.")
                    print(f"[FAIL] Decryption returned empty string for candidate {name} (ID: {cand_id}).")
                else:
                    print(f"[PASS] Decrypted candidate text successfully. Length: {len(decrypted)} chars.")
                    snippet = decrypted[:60].replace('\n', ' ')
                    print(f"       Snippet: '{snippet}...'")
            else:
                print("[INFO] No existing encrypted candidate records (starting with 'gAAAAA') found in database.")
                print("[+] Performing active write/read round-trip encryption validation...")
                
                # Import encrypt_field dynamically
                from api.core.encryption import encrypt_field
                import uuid
                
                # Fetch a valid recruiter/organization_id to satisfy foreign key constraints
                rec_res = restored_client.table("recruiters").select("id").limit(1).execute()
                rec_id = rec_res.data[0]["id"] if rec_res.data else None
                
                test_id = str(uuid.uuid4())
                test_text = "Staging Restore Test Content for Encryption Decryption Sanity Check"
                encrypted_text = encrypt_field(test_text)
                
                test_candidate = {
                    "id": test_id,
                    "full_name": "Restore Test Dummy",
                    "email": "restore_test_dummy@example.com",
                    "raw_text": encrypted_text,
                    "match_score": 0.0,
                    "completeness_score": 0.0,
                    "ats_score": 0.0,
                    "pipeline_stage": "screening",
                    "stage": "screening",
                    "github_url": "",
                    "github_stars": 0,
                    "github_languages": [],
                    "github_commits_last_year": 0,
                    "blind_score": 0.0,
                    "interview_questions": [],
                    "summary": "Dummy",
                    "insights": {},
                    "experience_years": 0
                }
                if rec_id:
                    test_candidate["recruiter_id"] = rec_id
                    
                # Insert
                restored_client.table("candidates").insert(test_candidate).execute()
                
                # Retrieve
                fetched_res = restored_client.table("candidates").select("id, raw_text").eq("id", test_id).execute()
                if fetched_res.data:
                    fetched_raw = fetched_res.data[0].get("raw_text") or ""
                    decrypted = decrypt_field(fetched_raw)
                    if decrypted == test_text:
                        print("[PASS] Active round-trip encryption/decryption check passed.")
                    else:
                        failures.append(f"Decryption mismatch. Expected '{test_text}', Got '{decrypted}'")
                        print(f"[FAIL] Active round-trip encryption/decryption check failed.")
                else:
                    failures.append("Failed to retrieve temporary test candidate.")
                    print("[FAIL] Failed to retrieve temporary test candidate.")
                    
                # Clean up
                restored_client.table("candidates").delete().eq("id", test_id).execute()
                print("[+] Active validation completed and cleaned up.")
                
        except Exception as e:
            failures.append(f"Error testing encryption/decryption logic: {e}")
            print(f"[FAIL] Error testing encryption/decryption: {e}")
    else:
        print("[INFO] Candidates table check failed, skipping decryption test.")
        
    # Summary
    print("\n" + "=" * 60)
    print(" VERIFICATION SUMMARY ")
    print("=" * 60)
    if not failures:
        print("\n   >>>  ALL SANITY CHECKS PASSED SUCCESSFULLY  <<<\n")
        return True
    else:
        print(f"\n   >>>  VERIFICATION FAILED WITH {len(failures)} ERROR(S)  <<<")
        for f in failures:
            print(f"   - {f}")
        print()
        return False

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
