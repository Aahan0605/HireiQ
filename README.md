<div align="center">

  <img src="https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&q=80&w=1200&h=400" alt="HireIQ Banner" width="100%" style="border-radius: 12px;"/>

  <br /><br />

  <h1>🚀 HireIQ — Intelligent Hiring Platform</h1>

  <p>
    <b>A production-ready, AI-powered Applicant Tracking System built with FastAPI + React.<br/>
    Ranks candidates using TF-IDF, Cosine Similarity, Max-Heap, Merge Sort, 0/1 Knapsack DP, BFS, Greedy, KMP, and Rabin-Karp.</b>
  </p>

  <p>
    <a href="#-features">Features</a> •
    <a href="#-algorithms">Algorithms</a> •
    <a href="#-tech-stack">Tech Stack</a> •
    <a href="#-getting-started">Setup</a> •
    <a href="#-api-reference">API</a> •
    <a href="#-architecture">Architecture</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
    <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind" />
    <img src="https://img.shields.io/badge/Vite_5-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E" alt="Vite" />
    <img src="https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Framer_Motion-0055FF?style=for-the-badge&logo=framer&logoColor=white" alt="Framer Motion" />
  </p>

</div>

---

## ✨ Features

| Feature | Description |
| :--- | :--- |
| **📄 Professional PDF Export**| Generates formal, color-coded candidate reports with match categories, scores, and timestamps using `fpdf2` logic |
| **🧠 TF-IDF Job Matching** | Vectorises resume text and job descriptions using a from-scratch `TFIDFVectorizer`, then ranks candidates per job using cosine similarity + max-heap |
| **⚖️ Weighted Score Fusion** | User-configurable weights (Resume, GitHub, LeetCode, Portfolio) stored in-memory and applied to every upload — adjustable live from the Settings page |
| **🐙 Live GitHub Signals** | Fetches real GitHub stats (repos, stars, commit frequency, languages, PRs) via async httpx and computes a 0–100 GitHub score |
| **💼 Job Listings & Matching** | Full CRUD for job postings with TF-IDF + cosine similarity matching and max-heap ranked candidate lists per job |
| **📊 Skill Radar Charts** | Per-candidate radar charts built from actual skill frequency; per-category TF-IDF scores (Frontend / Backend / DevOps / Databases / ML-AI / Systems) in comparison view |
| **🔍 Candidate Comparison** | Select any 2 candidates → side-by-side radar, category dominance analysis, unique skill diff |
| **🛡️ Bias Audit Report** | Full vs blind scoring comparison with delta badges, CSS donut chart, and bias detection banner |
| **📅 Interview Scheduling** | Greedy activity selection maximises non-overlapping interview slots |
| **🎯 Optimal Shortlist** | 0/1 Knapsack DP selects the best candidates within a hiring budget |
| **🗺️ Skill Gap Analysis** | BFS on a skill prerequisite graph finds the shortest learning path from current skills to job requirements |
| **📈 Algorithm Visualizer** | Interactive step-by-step visualisation of all core algorithms (TF-IDF, Heap, Merge Sort, KMP, BFS, Knapsack, Greedy) |
| **🏠 Landing Page** | Public-facing marketing page with hero, features, and pricing sections |


---

## 🧮 Algorithms

Every algorithm is implemented from scratch in `backend/algorithms/` — no sklearn, no external ML libraries.

### 1. TF-IDF + Cosine Similarity — Resume & Job Matching
**File:** `backend/algorithms/tfidf.py` · `backend/algorithms/cosine_similarity.py`

Converts resume text and job descriptions into sparse TF-IDF vectors, then measures the angle between them.

```
TF(word, doc)  = count of word in doc / total words in doc
IDF(word, all) = log(total docs / (1 + docs containing word)) + 1
cosine(A, B)   = (A · B) / (‖A‖ × ‖B‖)
```

- **Time:** O(N × L × V) to fit, O(min|A|,|B|) per similarity
- **Why not BERT:** Requires 400MB+ models; TF-IDF is fully explainable and deterministic
- **Why not Euclidean distance:** Penalises longer resumes unfairly; cosine is length-independent

### 2. Max-Heap — Candidate Ranking
**File:** `backend/algorithms/heap.py`

Wraps Python's `heapq` (min-heap) with negated scores for max-heap behaviour. Supports `push O(log n)`, `top_k O(k log n)`, `get_all_ranked O(n log n)`.

- **Why not sort():** Heap gives top-K in O(k log n) without sorting the entire list
- **Tie-breaking:** `seq` counter ensures FIFO stability for equal scores

### 3. Merge Sort + Rank Delta — Score Re-ranking
**File:** `backend/algorithms/merge_rank.py`

Sorts candidates by fusion score using divide-and-conquer. Tracks `rank_delta = original_index - final_index` — powers the animated `+2 / -1` badges on the Candidates page.

- **Time:** O(n log n) guaranteed · **Space:** O(n)
- **Why not QuickSort:** Unstable (equal scores swap unpredictably); worst case O(n²)

### 4. 0/1 Knapsack DP — Optimal Shortlist
**File:** `backend/algorithms/dp_shortlist.py`

Selects candidates to maximise total score within a hiring budget. Each candidate is either hired (1) or not (0).

```
dp[i][w] = max(dp[i-1][w],  dp[i-1][w-cost[i]] + score[i])
```

- **Time:** O(n × budget) · **Space:** O(n × budget)
- **Why not Greedy:** Greedy by score/cost ratio provably fails for 0/1 variant

### 5. Greedy Activity Selection — Interview Scheduling
**File:** `backend/algorithms/interview_scheduler.py`

Sorts candidates by end time, greedily picks the earliest-finishing non-overlapping interview slot.

- **Time:** O(n log n) · **Proof of optimality:** Exchange argument
- **Why not DP:** Greedy is already optimal here; DP would be over-engineering

### 6. BFS on Skill Graph — Skill Gap Analysis
**File:** `backend/algorithms/skill_graph.py`

Models skills as nodes with prerequisite edges. Multi-source BFS from all current skills finds the shortest learning path to any missing required skill.

- **Time:** O(V + E) · **Why not DFS:** DFS doesn't guarantee shortest path

### 7. KMP String Matching — Skill Keyword Detection
**File:** `backend/algorithms/kmp.py`

Searches for 100+ skill keywords in resume text using the Knuth-Morris-Pratt failure function, avoiding redundant character comparisons.

- **Time:** O(n + m) vs O(n × m) for naive search
- **Used in:** `feature_extractor.py` for all skill and certification detection

### 8. Rabin-Karp — Multi-Pattern Skill Search
**File:** `backend/algorithms/rabin_karp.py`

Rolling-hash based multi-pattern search used alongside KMP for compound skill phrases (e.g. "machine learning", "react native").

- **Time:** O(n + m) average · **Why alongside KMP:** Efficient for multi-keyword batch matching

---

## 🚀 Tech Stack

### Backend
| Layer | Technology |
| :--- | :--- |
| API Framework | FastAPI (async, auto-docs at `/docs`) |
| PDF Processing | pdfplumber, fpdf2 (for exports) |
| HTTP Client | httpx (async GitHub API calls) |
| Algorithms | Pure Python stdlib — no sklearn |
| Server | Uvicorn with `--reload` |

### Frontend
| Layer | Technology |
| :--- | :--- |
| Core | React 18 + Vite 5 |
| Styling | Tailwind CSS — dark theme `#0d0d1a` base |
| Animation | Framer Motion 11 |
| Charts | Recharts (RadarChart, ResponsiveContainer) |
| Routing | React Router v6 |
| Notifications | Sonner toast |
| Icons | Lucide React |
| File Upload | react-dropzone |

---

## 🛠️ Getting Started

### Prerequisites
- **Node.js** `v18+` and `npm`
- **Python** `3.9+`

### 1. Clone
```bash
git clone https://github.com/Aahan0605/HireiQ.git
cd HireiQ
```

### 2. Start the Backend
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

> Backend runs at **`http://localhost:8000`**  
> Interactive API docs at **`http://localhost:8000/docs`**

### 3. Start the Frontend
Open a new terminal in the repo root:
```bash
cd frontend
npm install
npm run dev
```

> Frontend runs at **`http://localhost:5173`** (Vite default)

### 4. Optional — GitHub Token
For higher GitHub API rate limits (60 → 5000 requests/hour), add a token:
```bash
# backend/.env
GITHUB_TOKEN=your_github_personal_access_token
```

---

## 📡 API Reference

Base URL: `http://localhost:8000/api/v1`

### Candidates
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/candidates` | List all candidates |
| `POST` | `/candidates/upload-resume` | Upload PDF → TF-IDF scoring + job matching |
| `GET` | `/candidates/github/{username}` | Live GitHub stats + score |
| `POST` | `/candidates/rank-sorted` | Merge sort candidates by score |
| `POST` | `/candidates/shortlist` | 0/1 Knapsack optimal shortlist |
| `POST` | `/candidates/schedule` | Greedy interview scheduling |
| `POST` | `/candidates/skill-gap` | BFS skill learning path |
| `GET` | `/reports/candidates/pdf` | Generate professional PDF candidate report |
| `GET` | `/reports/candidates/csv` | Legacy CSV candidate export |

### Jobs
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/jobs` | List all job postings |
| `POST` | `/jobs` | Create new job |
| `GET` | `/jobs/{id}` | Get single job |
| `PUT` | `/jobs/{id}` | Update job |
| `DELETE` | `/jobs/{id}` | Delete job |
| `GET` | `/jobs/{id}/matches` | TF-IDF ranked candidates for this job |

### Settings
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/settings/weights` | Get current scoring weights |
| `POST` | `/settings/weights` | Update weights (applied to next upload) |
| `GET` | `/settings/thresholds` | Get match thresholds |
| `POST` | `/settings/thresholds` | Update Strong / Match / Weak thresholds |

---

## 📂 Architecture

```
HireiQ/
├── backend/
│   ├── algorithms/
│   │   ├── tfidf.py              # From-scratch TF-IDF vectoriser
│   │   ├── cosine_similarity.py  # Sparse cosine similarity + Jaccard
│   │   ├── heap.py               # Max-heap candidate ranking
│   │   ├── merge_rank.py         # Merge sort + rank delta tracking
│   │   ├── dp_shortlist.py       # 0/1 Knapsack DP shortlisting
│   │   ├── interview_scheduler.py# Greedy activity selection
│   │   ├── skill_graph.py        # BFS skill prerequisite graph
│   │   ├── kmp.py                # KMP string matching
│   │   └── rabin_karp.py         # Rabin-Karp multi-pattern search
│   ├── api/
│   │   ├── routes/
│   │   │   ├── candidates.py     # Upload, GitHub, rank, shortlist, schedule
│   │   │   ├── jobs.py           # CRUD + TF-IDF job matching
│   │   │   ├── reports.py        # Report generation endpoints
│   │   │   └── settings.py       # Weights + thresholds (active_weights store)
│   │   ├── main.py               # FastAPI app + CORS + router registration
│   │   └── models.py             # Pydantic request/response models
│   ├── engine/
│   │   ├── score_fusion.py       # Weighted multi-signal score orchestrator
│   │   ├── bias_auditor.py       # Full vs blind scoring comparison
│   │   ├── matcher.py            # JD ↔ resume matching engine
│   │   └── ranker.py             # Final ranking logic
│   ├── parser/
│   │   ├── resume_parser.py      # PDF/TXT extraction + text cleaning
│   │   └── feature_extractor.py  # KMP skill detection, experience, education
│   ├── signals/
│   │   ├── github_signal.py      # Async GitHub API + score_github()
│   │   ├── coding_signal.py      # Codeforces / LeetCode / CodeChef
│   │   ├── linkedin_signal.py    # LinkedIn signal extraction
│   │   ├── cert_verifier.py      # Certification verification
│   │   └── portfolio_crawler.py  # Portfolio URL analysis
│   ├── config.py                 # Scoring weights, role profiles, thresholds
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── DashboardLayout.jsx  # Shared sidebar + page wrapper
│       │   ├── MagneticCard.jsx     # 3D tilt card component
│       │   ├── StatCard.jsx         # Animated metric card
│       │   ├── RecentCandidates.jsx # Dashboard recent analyses list
│       │   ├── SkillGapCard.jsx     # Skill gap + learning path display
│       │   ├── AlgorithmLegend.jsx  # Floating algorithm reference button
│       │   ├── HeroSection.jsx      # Landing page hero
│       │   ├── FeaturesSection.jsx  # Landing page features grid
│       │   ├── PricingSection.jsx   # Landing page pricing tiers
│       │   └── GrainOverlay.jsx     # CSS grain texture overlay
│       ├── pages/
│       │   ├── Landing.jsx          # Public marketing landing page
│       │   ├── Dashboard.jsx        # Overview + 4 metric cards + modals
│       │   ├── Candidates.jsx       # List + merge sort + compare bar
│       │   ├── CandidateProfile.jsx # Full profile + GitHub stats + recommended roles
│       │   ├── Analyze.jsx          # PDF upload + analysis progress
│       │   ├── Jobs.jsx             # Job listings + post modal
│       │   ├── JobMatches.jsx       # TF-IDF ranked candidates per job
│       │   ├── CompareView.jsx      # Side-by-side radar + category scores
│       │   ├── BiasReport.jsx       # Bias audit + donut chart
│       │   ├── AlgorithmVisualizer.jsx # Step-by-step algorithm visualisation
│       │   ├── Settings.jsx         # Live weight sliders + threshold config
│       │   └── SignIn.jsx           # Auth page
│       ├── data/
│       │   └── candidates.js        # Local store + addCandidateFromCV()
│       └── lib/
│           ├── animations.js        # Framer Motion variants
│           └── hooks.js             # useMagneticTilt, useCountUp, useIntersection
│
├── docker-compose.yml
└── README.md
```

---

## 🎨 Design System

HireIQ uses a strict **Glassmorphism & Neon Dark** aesthetic:

| Token | Value | Usage |
| :--- | :--- | :--- |
| Base background | `#0d0d1a` | All page backgrounds |
| Card background | `#13131f` | All card surfaces |
| Border | `white/10` | All card borders |
| Primary accent | `#9D74FF` (violet) | Active states, CTAs |
| Secondary accent | `#22d3ee` (cyan) | Comparison, GitHub |
| Success | `#22c55e` (green) | Strong match, verified |
| Warning | `#f59e0b` (amber) | Bias detected, warnings |

---

<div align="center">
  <sub>Built with ❤️ for the HireIQ Engineering Team · DAA Project 2025</sub>
</div>
