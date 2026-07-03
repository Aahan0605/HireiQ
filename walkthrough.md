# Walkthrough: Resolution of Production Errors & Resume Pipeline Fixes

We have successfully resolved the production issues to ensure high availability, correct CORS, clean error handling, correct database stage state mapping, and robust link extraction from resumes.

---

## ⚡ 1. Render Cold Start Resolution
- **Issue**: Render's free tier spins down the backend container after 15 minutes of inactivity, causing the first request to hang for 30–60 seconds while cold-starting.
- **Solution**: Added a new GitHub Actions cron workflow [keep_alive.yml](file:///Users/aahanajaygajera/Desktop/al&ml/hireiq/.github/workflows/keep_alive.yml) scheduled to run every 10 minutes. It issues a quick `curl` request to the backend health endpoint, keeping the Render container warm indefinitely.

---

## 🔒 2. Console CORS Errors for Vercel Preview Domains
- **Issue**: Branch and pull request deployments on Vercel generate dynamic subdomains (e.g. `https://test-preview-branch.vercel.app`) that were rejected by the backend's strict CORS allowed origins list.
- **Solution**: Created a custom `VercelCORSMiddleware` class in [main.py](file:///Users/aahanajaygajera/Desktop/al&ml/hireiq/backend/api/main.py). It subclassed FastAPI's `CORSMiddleware` and overrode `is_allowed_origin` to dynamically allow any secure origin ending with `.vercel.app` (while fully preserving credential exchange).
- **Result**: Preflight pre-requests and actual requests with dynamic Vercel subdomains now return `200 OK` and correctly echo the corresponding `Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials: true` headers.

---

## 📝 3. 500 Internal Server Errors & Environment Safety
- **Issue**: Unhandled runtime exceptions returned a generic, uninformative 500 error page to the client. Also, missing environment variables at startup could lead to crashes at runtime.
- **Solution**:
  - Added startup configuration validation checks in [main.py](file:///Users/aahanajaygajera/Desktop/al&ml/hireiq/backend/api/main.py) to immediately verify `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`, and `FIELD_ENCRYPTION_KEY` on service startup.
  - Implemented a global exception handler for `Exception` to intercept any unhandled runtime crashes, write the full traceback directly into Render's server logs, and return a clean, non-sensitive JSON response to the client:
    ```json
    {"detail": "An unexpected error occurred. Please check Render logs or try again later."}
    ```

---

## 🔀 4. 404 Rewrite Edge Cases on API Calls
- **Issue**: Vercel rewrite rules in [vercel.json](file:///Users/aahanajaygajera/Desktop/al&ml/hireiq/frontend/vercel.json) mapped `/api/:path*` to Render but did not cover the exact base `/api` path, which could result in a 404 when hitting the root API URL.
- **Solution**: Updated [vercel.json](file:///Users/aahanajaygajera/Desktop/al&ml/hireiq/frontend/vercel.json) to define both `/api` (exact match) and `/api/:path*` (subpath match). Hitting `https://hirei-q.vercel.app/api` now rewrites directly to the backend root (`/`) which yields a clean `200 OK` health status.

---

## ⚡ 5. Resume Upload & Analysis Latency Resolution
- **Issue**: Uploading and analyzing resumes hung or lagged indefinitely under load. Additionally, status synchronization was broken; the placeholder candidate had status `"Screening"` immediately upon creation, leading the frontend to stop polling before the background analysis completed.
- **Solution**:
  - **Status Sync**: Added `Analyzing` state mapping to/from the database `stage` and `pipeline_stage` columns (`analyzing` lower-case). Changing the placeholder candidate's status to `"Analyzing"` ensures the frontend continues to poll correctly.
  - **Timeouts**: Wrapped full candidate scoring in a 45-second timeout, falling back gracefully to resume-only scoring if a timeout or rate limit occurs. Wrapped the secondary blind score computation in a 15-second timeout, falling back to a deterministic offset to avoid blocking the user flow.
  - **Reduced Signal Crawler Timeouts**: Reduced individual external API and crawler timeouts (GitHub API, competitive coding platforms, certifications verifier, and portfolio crawler) from 10.0 seconds to 6.0 seconds.

---

## 🛠️ 6. Database Check Constraint Violation Resolution
- **Issue**: Saving the `"analyzing"` string directly into the database `stage` or `pipeline_stage` columns violated the Supabase `candidates_pipeline_stage_check` check constraint (which restricts valid stages to `screening`, `shortlisted`, `interviewing`, `offer`, `hired`, `rejected`).
- **Solution**:
  - Mapped `"Analyzing"` status to `"screening"` in the database under the hood to satisfy the constraint.
  - Modified `_candidate_to_dict` in [candidates.py](file:///Users/aahanajaygajera/Desktop/al&ml/hireiq/backend/api/routes/candidates.py) to dynamically output `"status": "Analyzing"` when the candidate summary is `"Analyzing resume, please wait..."`.
  - This keeps the database constraint valid while preserving the frontend polling logic.

---

## 🔗 7. Hyperlink PDF Link Extraction
- **Issue**: Resumes created in Canva or Microsoft Word hide candidate GitHub and LinkedIn profile links in document hyperlink annotations rather than plain text. Pure regex searches failed to extract these hidden profiles.
- **Solution**:
  - Updated [resume_parser.py](file:///Users/aahanajaygajera/Desktop/al&ml/hireiq/backend/parser/resume_parser.py) to extract all document link annotations (`/URI`) using `pypdf`.
  - Added fallback checks to extract the username from these links if regex search on plain text returns empty.

---

## 💬 8. Frontend Interface Polish
- **Issue**: The "AI Interview Agent Simulation" UI card was a mock/scripted experience that added bloat to the candidate page.
- **Solution**:
  - Modified [CandidateProfile.jsx](file:///Users/aahanajaygajera/Desktop/al&ml/hireiq/frontend/src/pages/CandidateProfile.jsx) to completely remove the AI Interview Simulation card.
  - Cleaned up unused React states (`chatMessages`, `chatInput`, `chatLoading`, `interviewScorecard`, `interviewCompleted`) and handlers (`handleStartInterview`, `handleSendMessage`).
  - Enhanced the GitHub webhook sync response mapping to correctly sync `github` and `linkedin` fields in the local state.

---

## 🔍 9. End-to-End Live Verification of Resume Upload & Analysis
We executed the browser-based Playwright verification script against the deployed production site (`https://hirei-q.vercel.app`), verifying:
1. **Successful Authentication & Upload**: Logged in with a test recruiter account and uploaded a sample resume.
2. **State Transition & Polling**: The frontend displayed the `"Analyzing"` state and polled the backend correctly without any premature page transitions.
3. **Database Insertion & Background Execution**: The backend successfully created a candidate row, ran the 360° scoring pipeline, and stored the correct details:
   - **Name**: parsed from the resume document
   - **GitHub Profile**: extracted from the resume hyperlink
   - **LinkedIn Profile**: extracted from the resume hyperlink
   - **GitHub Languages**: `["Jupyter Notebook", "Python", "TypeScript"]`
4. **Correct Resume Analysis**: The name extraction (the parsed candidate name) and extracted resume features successfully propagated to the generated AI executive summary, replacing the old placeholder text (a filename-derived placeholder).

---

## 🔒 10. Email Verification Enforced Unconditionally
- **Issue**: Accounts registered on the website could bypass email verification if the backend environment was missing SMTP or Resend API keys. This defaulted to setting `is_verified` to `True`.
- **Solution**: Modified [auth.py](file:///Users/aahanajaygajera/Desktop/al&ml/hireiq/backend/api/routes/auth.py) to set `"is_verified": False` unconditionally on every account registration.
- **Verification**: Created a test account on the live server and verified that initial login attempts fail with `401 Unauthorized` and the message `"Please verify your email before logging in."`, only succeeding after token verification.

---

## 📂 11. GitHub Repository Count Display Mismatch Resolution
- **Issue**: When loading the candidate profile page, the frontend calls the GitHub signals proxy endpoint `/candidates/github/{username}`. Due to GitHub API unauthenticated rate limits on Render's shared IP block, this endpoint was falling back to a simulated profile generating random repository counts (e.g. `11` or `18` instead of the actual `7`).
- **Solution**:
  - Updated `get_github_signals` in [candidates.py](file:///Users/aahanajaygajera/Desktop/al&ml/hireiq/backend/api/routes/candidates.py) to first query the Supabase `candidates` table for the target GitHub handle (`github_url` field).
  - If a matching candidate profile with cached insights is found, the backend returns the stored data directly instead of requesting the live rate-limited GitHub API.
- **Verification**: Tested against the live deployed endpoint, verifying it correctly returns the the cached value for the test GitHub handle.
