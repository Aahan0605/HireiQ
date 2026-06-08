<div align="center">

  <img src="https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&q=80&w=1200&h=400" alt="HireIQ Banner" width="100%" style="border-radius: 12px;"/>

  <br /><br />

  <h1>🚀 HireIQ — Intelligent Hiring Platform</h1>

  <p>
    <b>A production-ready, AI-powered Applicant Tracking System built for modern hiring teams.<br/>
    Accelerate your recruitment process with intelligent candidate matching, AI-driven Q&A generation, live GitHub syncing, and optimal scheduling.</b>
  </p>

  <p>
    <a href="#-features">Features</a> •
    <a href="#-core-technologies">Technologies</a> •
    <a href="#-getting-started">Setup</a> •
    <a href="#-api-reference">API</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
    <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind" />
    <img src="https://img.shields.io/badge/Vite_5-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E" alt="Vite" />
    <img src="https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase" />
  </p>

</div>

---

## ✨ Features

| Feature | Description |
| :--- | :--- |
| **🧠 AI-Driven Resume Matching** | Vectorises resume text and job descriptions to intelligently rank candidates based on semantic relevance to the role |
| **🤖 Generative Interview Q&A** | Automatically generates tailored interview questions based on the candidate's resume and job requirements using Gemini AI |
| **🐙 Live GitHub Syncing** | Fetches real-time GitHub stats (repos, stars, languages, PRs) via webhook integration to compute an accurate developer score |
| **⚖️ Weighted Score Fusion** | User-configurable weights (Resume, GitHub, Portfolio) applied dynamically to every profile — adjustable live from the Settings |
| **💼 Comprehensive ATS Pipeline** | Full CRUD for job postings, candidate pipelines, shortlisting, and hiring workflows |
| **📊 Skill Radar Charts** | Per-candidate visual radar charts highlighting strengths across Frontend, Backend, DevOps, Data, and Systems |
| **🔍 Candidate Comparison** | Select any 2 candidates for a side-by-side radar, category dominance analysis, and unique skill diffs |
| **🛡️ Bias Audit & Detection** | Full vs blind scoring comparison with delta badges, highlighting potential hiring biases and ensuring fairness |
| **📅 Automated Interview Scheduling** | Intelligently maximises non-overlapping interview slots using optimal scheduling logic |
| **🎯 Smart Shortlisting** | Automatically selects the best mix of candidates that maximise quality while staying within your hiring budget |
| **📄 Professional PDF Export**| Generates formal, color-coded candidate reports with match categories, scores, and AI insights |
| **🏠 Marketing & SaaS Landing** | Public-facing marketing page with hero, features, value propositions, and subscription pricing sections |


---

## 🧠 Core Technologies & AI Engines

Our proprietary matching engines and AI integrations ensure unbiased, highly accurate candidate rankings and streamlined workflows.

### 1. Vectorized Candidate Matching
Converts resume text and job descriptions into sparse TF-IDF vectors, measuring semantic similarity to ensure the best candidates float to the top automatically.

### 2. Generative AI Q&A Engine (Gemini)
Leverages Google's Gemini LLM to parse a candidate's background against the job description to generate highly specific, technical, and behavioral interview questions tailored to their exact profile.

### 3. Dynamic Candidate Ranking
Employs efficient priority queues and sorting logic to maintain real-time leaderboards of applicants as their external signals (like GitHub commits) are updated via webhooks.

### 4. Smart Budget Shortlisting
Uses dynamic programming logic (0/1 Knapsack) to select a cohort of candidates that provides the maximum total value while respecting your company's hiring bandwidth and budget constraints.

### 5. Automated Scheduling Engine
Sorts candidates by availability and optimally schedules back-to-back interviews, completely removing the back-and-forth of calendar management.

### 6. Robust Database Architecture
Utilizes Supabase (PostgreSQL) for scalable cloud persistence, with a seamless fallback to local SQLite, ensuring zero downtime even in disconnected environments.

---

## 🚀 Tech Stack

### Backend
| Layer | Technology |
| :--- | :--- |
| API Framework | FastAPI (async, auto-docs at `/docs`) |
| Generative AI | Google Gemini API (`google-generativeai`) |
| Database | Supabase (PostgreSQL) + SQLite Fallback |
| External APIs | httpx (async GitHub API + Webhooks calls) |
| Server | Uvicorn with `--reload` |

### Frontend
| Layer | Technology |
| :--- | :--- |
| Core | React 18 + Vite 5 |
| Styling | Tailwind CSS — Dark Theme `#0d0d1a` |
| Animation | Framer Motion 11 |
| Charts | Recharts (RadarChart, ResponsiveContainer) |
| Routing | React Router v6 |
| Notifications | Sonner toast |
| Icons | Lucide React |

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

# Add your Gemini API Key
echo "GEMINI_API_KEY=your_api_key_here" >> .env

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

> Frontend runs at **`http://localhost:5173`**

### 4. Environment Variables
To fully utilize all features, configure your `.env` in the `backend/` directory:
```env
GEMINI_API_KEY=your_gemini_api_key
GITHUB_TOKEN=optional_github_token_for_higher_limits
SUPABASE_URL=optional_supabase_url
SUPABASE_KEY=optional_supabase_key
```

---

## 📡 API Reference

Base URL: `http://localhost:8000/api/v1`

### Core Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/candidates` | List all tracked candidates |
| `POST` | `/candidates/upload-resume` | Upload PDF → Parse + match against jobs |
| `POST` | `/candidates/{id}/generate-qa`| Generate AI interview questions using Gemini |
| `POST` | `/candidates/{id}/webhook/github-sync`| Trigger live GitHub signal sync |
| `POST` | `/candidates/shortlist` | Intelligent shortlisting within budget |
| `POST` | `/candidates/schedule` | Automated interview scheduling |

---

## 🎨 Design System

HireIQ uses a strict **Glassmorphism & Neon Dark** aesthetic for a premium SaaS feel:

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
  <sub>© 2025 HireIQ Inc. · Intelligent SaaS Hiring Platform</sub>
</div>
