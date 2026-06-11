# <div align="center"><img src="https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&q=80&w=1200&h=400" alt="HireIQ Banner" width="100%" style="border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);"/></div>

<div align="center">

# 🚀 HireIQ — AI-Powered Hiring Intelligence Platform

[![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](#)
[![Vite](https://img.shields.io/badge/Vite_5-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E)](#)
[![Tailwind](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](#)

<h3>A secure, production-grade, AI-powered Applicant Tracking System (ATS) that helps recruiters discover, evaluate, rank, and hire the best candidates faster than traditional methods.</h3>

<p align="center">
  <a href="#-product-highlights">Highlights</a> •
  <a href="#-core-features">Features</a> •
  <a href="#-system-architecture">Architecture</a> •
  <a href="#-getting-started">Installation</a> •
  <a href="#-api-endpoints">API Docs</a> •
  <a href="#-saas--monetization">Pricing</a> •
  <a href="#-design-system">Design System</a>
</p>

</div>

---

## 🌟 Product Highlights

| Feature | Description |
| :--- | :--- |
| **🧠 AI Resume Parsing** | TF-IDF + Cosine Similarity scoring with ATS Intelligence reports |
| **📋 Kanban Hiring Pipeline** | Drag-and-drop candidate cards through 6-stage recruitment columns |
| **🔍 Advanced Filters** | Filter by match score, experience years, education tier, and skill tags |
| **🐙 GitHub Profile Sync** | Real-time webhook integration to pull commit frequency, stars, and languages |
| **🕵️ Blind Review Mode** | Anonymize candidate identities to eliminate demographic hiring bias |
| **⚡ ATS Resume Intelligence** | Completeness scores, ATS optimization scores, career progression analysis |
| **📊 Interactive Radar Charts** | Visual skill distribution graphs powered by Recharts |
| **💳 SaaS Billing Portal** | Mock B2B pricing tiers (Free / Pro / Enterprise) with credit card checkout |
| **🎨 Constellation Background** | GPU-accelerated 60 FPS HTML5 Canvas particle system with mouse interactivity |
| **📈 CSV & PDF Reports** | Export full candidate data as styled PDF reports or ATS-compatible CSV |

---

## ✨ Core Features

> [!TIP]
> HireIQ replaces traditional, slow, manual resume screening with secure pipelines, customizable matching parameters, and real-time signals.

### 🧠 AI-Driven Resume Matching & Intelligence
*   **Semantic Matching**: Instantly vectorizes and scores resumes against job descriptions using TF-IDF + Cosine Similarity.
*   **ATS Resume Intelligence**: Calculates Completeness Score, ATS Optimization Score, Career Progression tier, Key Strengths, Development Gaps, and Potential Concerns.
*   **Generative Q&A Blueprints**: Leverages Google Gemini models to construct custom behavioral and technical interview questions based on candidate skill gaps.

### 📋 Visual Hiring Kanban Board
*   **Pipeline Management**: Drag-and-drop candidate cards across 6 stages: `Screening` → `Shortlisted` → `Interviewing` → `Offer` → `Hired` / `Rejected`.
*   **Real-time Persistence**: Stage changes are saved to SQLite/Supabase via PATCH API and localStorage for offline resilience.
*   **View Toggle**: Switch between traditional List View and visual Kanban Board with a single click.

### 🔍 Advanced Recruiter Filters
*   **Score Range Slider**: Filter candidates by minimum match score (0–100%).
*   **Experience Filter**: Set minimum years of professional experience.
*   **Education Tier Dropdown**: Filter by Bachelors, Masters, or Ph.D.
*   **Skill Tag Selection**: Multi-select from dynamically extracted skill tags across all candidates.

### 🐙 Live Developer Signals
*   **Webhook Syncing**: Integrates with candidate GitHub profiles to pull repository activity, contributions, stars, and languages.
*   **Fused Scoring**: Computes a dynamic rating by blending resume parsing metrics, GitHub contributions, and portfolio presence.

### 📅 Smart Pipeline Optimization
*   **Automated Scheduling**: Employs an optimal slot-matching selection algorithm (Greedy Activity Selection) to design back-to-back, conflict-free interview blocks.
*   **Smart Cohort Shortlisting**: Maximizes candidate match quality under resource constraints using dynamic programming (0/1 Knapsack).

### 🛡️ Bias Audit & Detection
*   **Blind Auditing**: Automatically runs blind profile scoring alongside normal scoring to identify differences in parameters (e.g. location, names) to ensure fair hiring.
*   **Anonymization Engine**: Toggle blind mode to mask all candidate identities across the platform.

### 💳 SaaS Monetization Portal
*   **Usage Tracking**: Visual progress bars showing CV upload quota consumption.
*   **Pricing Tiers**: Gorgeous B2B comparison cards for Free, Pro ($79/mo), and Enterprise plans.
*   **Mock Checkout**: Glassmorphic credit card validation form with real-time card preview.

---

## 🛠️ Getting Started

### 📋 Prerequisites
*   **Node.js** (v18+)
*   **Python** (3.9+)

### 1️⃣ Clone and Navigate
```bash
git clone https://github.com/Aahan0605/HireiQ.git
cd HireiQ
```

### 2️⃣ Initialize the Backend
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add environment variables (optional for Gemini Q&A)
echo "GEMINI_API_KEY=your_gemini_key_here" >> .env
echo "JWT_SECRET_KEY=your_secure_jwt_secret" >> .env

# Run development server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
*   **API Docs**: Access [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger page.

### 3️⃣ Initialize the Frontend
Open a new terminal session in the root folder:
```bash
cd frontend
npm install
npm run dev
```
*   **App UI**: Access [http://localhost:6901](http://localhost:6901) on your local browser.
*   **Sign Up**: Register a new recruiter account directly on the Sign Up page.
*   **First-time setup**: Register via `/register`. To seed an admin: `python backend/scripts/seed_admin.py --email you@yourdomain.com`

---

## 📂 System Architecture

```
HireiQ/
├── backend/
│   ├── api/
│   │   ├── core/         # JWT Security, Guards, Dependencies
│   │   └── routes/       # Auth, Candidates, Jobs, Reports, Settings
│   ├── db/               # Supabase Connector & Local SQLite Hybrid Layer
│   ├── algorithms/       # Greedy Scheduler, Knapsack Shortlist, BFS Skill Graph
│   ├── parser/           # PDF Plumber resume parser & Feature extraction
│   └── scratch/          # Development scratch, integration tests & seed scripts
├── frontend/
│   └── src/
│       ├── context/      # Global Authentication State Provider
│       ├── lib/          # API fetch wrapper & Tilt effects
│       ├── components/   # ConstellationBackground, MagneticCard, HeroSection
│       └── pages/        # Dashboard, Candidates (List + Kanban), Analyze, Settings (Scoring + Billing), Landing
└── data/                 # Sample resumes and job descriptions

> [!NOTE]
> The `backend/scratch/` directory contains development utilities, seeding modules, and integration test scripts (e.g. `test_checkout.py`, `test_members.py`) for verifying server routing and DB migrations. It is excluded in `.gitignore` and not intended for production deployment.
```

---

## 📡 API Endpoints

| Category | Method | Endpoint | Description |
| :--- | :---: | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/register` | Register new recruiter account |
| **Auth** | `POST` | `/api/v1/auth/login` | Login and obtain JWT token |
| **Candidates** | `GET` | `/api/v1/candidates` | List all tracked candidates |
| **Candidates** | `GET` | `/api/v1/candidates/{id}` | Get single candidate profile |
| **Candidates** | `PATCH` | `/api/v1/candidates/{id}` | Update candidate fields (e.g., pipeline stage) |
| **Candidates** | `DELETE` | `/api/v1/candidates/{id}` | Delete a candidate |
| **Candidates** | `POST` | `/api/v1/candidates/upload-resume` | Upload PDF and analyze in background |
| **Candidates** | `POST` | `/api/v1/candidates/upload-bulk` | Batch upload up to 1000 resumes |
| **Candidates** | `POST` | `/api/v1/candidates/{id}/generate-qa` | AI-generated interview questions |
| **Candidates** | `POST` | `/api/v1/candidates/{id}/webhook/github-sync` | Sync GitHub profile signals |
| **Jobs** | `GET` | `/api/v1/jobs` | List all open positions |
| **Reports** | `GET` | `/api/v1/reports/candidates/pdf` | Export candidates as styled PDF |
| **Reports** | `GET` | `/api/v1/reports/candidates/csv` | Export candidates as ATS CSV |
| **Settings** | `GET/POST` | `/api/v1/settings/weights` | Get/set scoring algorithm weights |
| **Settings** | `POST` | `/api/v1/settings/thresholds` | Set match classification thresholds |

---

## 💰 SaaS & Monetization

| Plan | Price | Features |
| :--- | :---: | :--- |
| **Free** | $0/mo | 5 CV uploads, basic TF-IDF scoring, list view, blind audit |
| **Pro** | $79/mo | Unlimited uploads, Kanban board, advanced filters, GitHub sync, AI Q&A |
| **Enterprise** | Custom | Custom weights, DB sync, PDF/CSV reports, priority support SLA |

---

## 🎨 Design System

HireIQ is styled with a premium **Glassmorphism & Neon Dark** layout:

| Token | Value | Usage |
| :--- | :--- | :--- |
| `--bg` | `#07070E` | Page background |
| `--surface` | `#0D0D1A` | Card backgrounds |
| `--surface-2` | `#141428` | Elevated surfaces |
| `--mint` | `#4DFFA4` | Primary accent (emerald) |
| `--violet` | `#10b981` | Secondary accent |
| `--rose` | `#FF6B8A` | Error / danger states |
| `--amber` | `#FFB347` | Warning / bias alerts |

**Typography**: Bricolage Grotesque (headings) + Instrument Sans (body) + Geist Mono (code)

---

## 🧪 Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite 5, Tailwind CSS, Framer Motion, Recharts, Lucide Icons |
| **Backend** | FastAPI, Python 3.9+, Pydantic, SQLite, Supabase (optional) |
| **AI/ML** | TF-IDF + Cosine Similarity, Google Gemini API, pdfplumber |
| **Auth** | JWT (PyJWT), bcrypt password hashing |
| **Algorithms** | Merge Sort (ranking), Greedy Activity Selection (scheduling), 0/1 Knapsack (shortlisting), BFS (skill graph) |

---

<div align="center">
  <sub>© 2026 HireIQ · AI-Powered Hiring Intelligence Platform · Built with ❤️</sub>
</div>
