# <div align="center"><img src="https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&q=80&w=1200&h=400" alt="HireIQ Banner" width="100%" style="border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);"/></div>

<div align="center">

# 🚀 HireIQ — Intelligent Hiring Platform

[![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](#)
[![Vite](https://img.shields.io/badge/Vite_5-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E)](#)
[![Tailwind](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](#)

<h3>A secure, production-grade, AI-powered Applicant Tracking System (ATS) tailored for modern recruitment pipelines.</h3>

<p align="center">
  <a href="#-core-features">Key Features</a> •
  <a href="#-system-architecture">Architecture</a> •
  <a href="#-getting-started">Installation</a> •
  <a href="#-api-endpoints">API Docs</a> •
  <a href="#-design-system">Design System</a>
</p>

</div>

---

## ✨ Core Features

> [!TIP]
> HireIQ replaces traditional, slow, manual resume screening with secure pipelines, customizable matching parameters, and real-time signals.

### 🧠 AI-Driven Resume Matching & Parsing
*   **Semantic Matching**: Instantly vectorizes and scores resumes against job descriptions.
*   **Generative Q&A blueprints**: Leverages Google Gemini models to construct custom behavioral and technical interview questions based on candidate skill gaps.

### 🐙 Live Developer Signals
*   **Webhook Syncing**: Integrates with candidate GitHub profiles to pull repository activity, contributions, stars, and languages.
*   **Fused Scoring**: Computes a dynamic rating by blending resume parsing metrics, GitHub contributions, and portfolio presence.

### 📅 Smart Pipeline Optimization
*   **Automated Scheduling**: Employs an optimal slot-matching selection algorithm (Greedy Activity Selection) to design back-to-back, conflict-free interview blocks.
*   **Smart Cohort Shortlisting**: Maximizes candidate match quality under resource constraints using dynamic programming (0/1 Knapsack).

### 🛡️ Bias Audit & Detection
*   **Blind Auditing**: Automatically runs blind profile scoring alongside normal scoring to identify differences in parameters (e.g. location, names) to ensure fair hiring.

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

# Add environment variables
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
*   **App UI**: Access [http://localhost:3000](http://localhost:3000) on your local browser.
*   **Default Logins**: Use `admin@hireiq.demo` with password `password123` to log in instantly.

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
│   └── parser/           # PDF Plumber resume parser & Feature extraction
├── frontend/
│   └── src/
│       ├── context/      # Global Authentication State Provider
│       ├── lib/          # API fetch wrapper & Tilt effects
│       ├── components/   # Skeletons, Sidebars, Modals
│       └── pages/        # Dashboard, Candidates, Analyze, Settings
```

---

## 📡 API Endpoints

| Category | Method | Endpoint | Description | Auth Required |
| :--- | :---: | :--- | :--- | :---: |
| **Auth** | `POST` | `/api/v1/auth/register` | Register new recruiter account | ❌ |
| **Auth** | `POST` | `/api/v1/auth/login` | Login and obtain JWT token | ❌ |
| **Candidates** | `GET` | `/api/v1/candidates` | List all tracked candidates |  |
| **Candidates** | `POST` | `/api/v1/candidates/upload-resume` | Upload PDF and analyze in background |  |
| **Candidates** | `POST` | `/api/v1/candidates/{id}/generate-qa` | Ask Gemini to generate custom interview questions |  |
| **Jobs** | `GET` | `/api/v1/jobs` | Get list of open positions |  |
| **Reports** | `GET` | `/api/v1/reports/candidates/pdf` | Export candidates report as styled PDF |  |

---

## 🎨 Design System

HireIQ is styled with a custom **Glassmorphism & Neon Dark** layout:

*   **Primary Background**: `#0d0d1a`
*   **Card Surfaces**: `#13131f`
*   **Vibrant Accents**: `#9D74FF` (Violet) & `#22d3ee` (Cyan)
*   **Action Success**: `#22c55e` (Green)
*   **Warnings/Bias Alert**: `#f59e0b` (Amber)

---

<div align="center">
  <sub>© 2025 HireIQ Inc. · Enterprise SaaS Recruitment Platform</sub>
</div>
