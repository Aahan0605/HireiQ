# <div align="center"><img src="https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&q=80&w=1200&h=400" alt="HireIQ Banner" width="100%" style="border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);"/></div>

<div align="center">

# 🚀 HireIQ — AI-Powered Hiring Intelligence Platform

<h3>A production-grade, secure Applicant Tracking System (ATS) built to automate resume parsing, candidate scoring, and pipeline mapping with complete privacy.</h3>

[![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](#)
[![Vite](https://img.shields.io/badge/Vite_5-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E)](#)
[![Tailwind](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](#)

</div>

---

## ⚡ Product Highlights

| Capability | Description |
| :--- | :--- |
| **🧠 AI Parsing & Scoring** | Advanced feature extraction and parameter-based alignment scoring. |
| **📋 Kanban Pipeline** | Direct drag-and-drop board for candidate status updates. |
| **🔍 Search & Filter** | Live multi-skill search, experience timeline, and education level filters. |
| **🐙 Live GitHub Sync** | Direct profile analysis extracting commit stats, language share, and stars. |
| **🕵️ Blind Review Mode** | Single-toggle anonymization to mask candidate demographic attributes. |
| **⚡ ATS Metrics** | Automated optimization scores, completeness ratings, and structured blueprints. |
| **📅 Optimal Scheduler** | Greedy slot selection to arrange conflict-free interview lineups. |
| **📈 Reports & Exports** | Clean candidate portfolio exports to PDF and structured CSV tables. |

---

## ✨ Core Features

> [!TIP]
> HireIQ bypasses slow, manual CV evaluations by automatically matching candidate profiles against job profiles while tracking actual programming footprint.

### 🧠 High-Fidelity Scoring
- **Dynamic Semantic Matching**: Measures matching alignment using custom criteria and weights defined by recruiters.
- **Generative Blueprints**: Leverages Gemini model integration to build custom technical questions targeting candidate skill gaps.
- **Experience Timeline Extraction**: Extracts and structures timeline arrays directly from the resume and saves them in the database for instant verification.

### 📋 Interactive Boards
- **Stage Management**: Shift candidates seamlessly across `Screening`, `Shortlisted`, `Interviewing`, `Offer`, `Hired`, and `Rejected` columns.
- **Dynamic Deduping**: Dashboard feeds are automatically sorted by entry date and deduplicated to show the newest evaluations.
- **Toggle Layout**: Instant toggle between high-density list tables and Kanban board columns.

### 🐙 Live Signals
- **GitHub Integration**: Direct profiling mapping to verify active repository statistics, PR updates, and language usage.
- **Radar Visuals**: Skill distributions mapped into clean, reactive interactive graphics.

---

## 🛠️ Getting Started

### 🐋 Docker Compose Setup (Recommended)

1. Clone and enter the workspace directory:
   ```bash
   git clone https://github.com/Aahan0605/HireiQ.git
   cd HireiQ
   ```

2. Configure environment credentials inside `.env` in the root directory:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your-service-role-key-here
   GEMINI_API_KEY=your-gemini-api-key-here
   JWT_SECRET_KEY=generate-a-secure-secret-phrase
   ```

3. Launch the container stack:
   ```bash
   docker compose up --build
   ```

4. Populate seed data into the database:
   ```bash
   docker compose exec backend python scripts/seed_demo.py
   ```
   * Access the local frontend dashboard at [http://localhost](http://localhost) using `demo@hireiq.dev` / `Demo1234!`.

---

### 💻 Local Development Setup (Manual)

#### 1. Setup Backend FastAPI
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
* Interactive API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

#### 2. Setup Frontend React
```bash
cd frontend
npm install
npm run dev
```
* Open [http://localhost:6901](http://localhost:6901) to interact with the web dashboard.

---

## 🔒 Security & Field Encryption

To ensure candidate privacy, HireIQ encrypts all resume text before database persistence using Fernet symmetric encryption.

- **Configure Encryption**: Generate a base64 key and define it in your backend environment:
  ```bash
  FIELD_ENCRYPTION_KEY=L9V8Sba4Nr33J_NcEL1w9PYSiaYvTGTicgDzPPtjdn4=
  ```
  > [!IMPORTANT]
  > Decryption requires the same key. Back up your keys securely.

---

## 📡 API Reference

| Category | Endpoint | Method | Purpose |
| :--- | :--- | :---: | :--- |
| **Auth** | `/api/v1/auth/register` | `POST` | Register a recruiter account |
| **Auth** | `/api/v1/auth/login` | `POST` | Login and acquire JWT credentials |
| **Candidates** | `/api/v1/candidates` | `GET` | List candidate profiles with filters |
| **Candidates** | `/api/v1/candidates/{id}` | `GET` | Retrieve detailed candidate profile |
| **Candidates** | `/api/v1/candidates/{id}` | `PATCH` | Edit profile info or pipeline status |
| **Candidates** | `/api/v1/candidates/upload-resume` | `POST` | Ingest and parse single resume |
| **Candidates** | `/api/v1/candidates/upload-bulk` | `POST` | Batch ingest up to 1000 resumes |
| **Candidates** | `/api/v1/candidates/{id}/generate-qa`| `POST` | Generate Gemini interview questions |
| **Candidates** | `/api/v1/candidates/{id}/webhook/github-sync` | `POST` | Process GitHub synced webhooks |
| **Jobs** | `/api/v1/jobs` | `GET` | Get listing of open job positions |
| **Reports** | `/api/v1/reports/candidates/pdf` | `GET` | Export candidates in styled PDF |
| **Reports** | `/api/v1/reports/candidates/csv` | `GET` | Export candidates in raw CSV |
| **Settings** | `/api/v1/settings/weights` | `GET/POST` | Get/set scoring algorithm weights |
| **Settings** | `/api/v1/settings/thresholds` | `POST` | Set match classification thresholds |

---

## 🎨 Design Tokens

| Property | Value | Context |
| :--- | :--- | :--- |
| `--bg` | `#07070E` | Main space background |
| `--surface` | `#0D0D1A` | Card containers |
| `--surface-2` | `#141428` | Menu list highlights |
| `--mint` | `#4DFFA4` | Primary brand accent (emerald) |
| `--violet` | `#10b981` | Accent buttons |
| `--rose` | `#FF6B8A` | Error/rejected labels |
| `--amber` | `#FFB347` | Pending/warning callouts |

---

## 🧪 Tech Stack

- **Frontend**: React 18, Vite 5, Recharts, Framer Motion, Tailwind CSS
- **Backend**: FastAPI, Python 3.9+, Pydantic, Supabase PostgreSQL
- **AI Model**: Google Gemini API integration (bias auditing and Q&A generation)
- **Algorithms**: Merge Sort (ranking), Greedy Activity Selection (interview scheduling), 0/1 Knapsack (shortlisting)

---

<div align="center">
  <sub>© 2026 HireIQ · Automated Recruiter Intelligence Portal</sub>
</div>
