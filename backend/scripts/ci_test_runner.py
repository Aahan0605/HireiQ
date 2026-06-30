import subprocess
import os
import sys
import json
import urllib.request
import urllib.parse
import ssl
import time

def run_tests():
    print("Starting Pytest execution via CI Test Runner...")
    # Run pytest capturing stdout and stderr
    # PYTHONPATH is already current directory if we run from backend/
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    print(result.stdout)
    return result.returncode, result.stdout

def upload_log(log_content):
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("[CI Test Runner] Missing SUPABASE_URL or SUPABASE_KEY. Skipping log upload.")
        return
        
    try:
        context = ssl._create_unverified_context()
        
        # 1. Fetch a valid recruiter_id
        url_rec = f"{supabase_url}/rest/v1/recruiters?select=id&limit=1"
        req_rec = urllib.request.Request(
            url_rec,
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}"
            }
        )
        rec_id = None
        with urllib.request.urlopen(req_rec, context=context) as response:
            recs = json.loads(response.read().decode())
            if recs:
                rec_id = recs[0]["id"]
                
        if not rec_id:
            print("[CI Test Runner] No recruiters found in database to link candidate log. Skipping.")
            return
            
        # 2. Insert candidate with log
        url_cand = f"{supabase_url}/rest/v1/candidates"
        payload = {
            "full_name": "CI Run Log",
            "email": f"ci-run-{int(time.time())}@example.com",
            "raw_text": f"CI Pytest Log:\n\n{log_content}",
            "recruiter_id": rec_id,
            "insights": {"log": log_content},
            "stage": "screening",
            "pipeline_stage": "screening"
        }
        
        req_cand = urllib.request.Request(
            url_cand,
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            data=json.dumps(payload).encode()
        )
        
        with urllib.request.urlopen(req_cand, context=context) as response:
            res_data = json.loads(response.read().decode())
            print(f"[CI Test Runner] Log uploaded successfully. Candidate ID: {res_data[0].get('id')}")
            
    except Exception as e:
        print(f"[CI Test Runner] Failed to upload log to Supabase: {e}")

def main():
    exit_code, log_content = run_tests()
    
    # Only upload logs if the test execution failed
    if exit_code != 0:
        print(f"[CI Test Runner] Pytest failed with exit code {exit_code}. Uploading log to Supabase...")
        upload_log(log_content)
    else:
        print("[CI Test Runner] Pytest passed successfully!")
        
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
