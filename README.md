<div align="center">
  <img src="https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&q=80&w=1200&h=400" alt="HireIQ Banner" width="100%" style="border-radius: 12px;"/>

  <br />
  <br />

  <h1>🚀 HireIQ — Intelligent Hiring Platform</h1>
  
  <p>
    <b>A premium, AI-powered recruitment ATS designed to streamline the modern hiring workflow.</b>
  </p>

  <p>
    <a href="#-key-features">Features</a> •
    <a href="#-tech-stack">Tech Stack</a> •
    <a href="#-getting-started">Installation</a> •
    <a href="#-architecture">Architecture</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
    <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind" />
    <img src="https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E" alt="Vite" />
    <img src="https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  </p>
</div>

---

HireIQ leverages advanced data correlation and machine learning to help engineering teams identify, analyze, and schedule top talent with unprecedented efficiency and reduced human bias.

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **📄 Advanced Document Parsing** | Robust data extraction utilizing high-speed **PyMuPDF** (`fitz`), seamlessly parsing unstructured layouts into chronological structures. |
| **⚡ Chronological Intelligence** | A dual-pass Regex engine that isolates exact Work Experience blocks, extracting timeframes and responsibilities accurately. |
| **🎯 Deterministic Match Scoring** | Dynamic job-match calculations mapping strict role-based technical requirements directly against textual CV density. |
| **📊 Frequency-Mapped Visualizations** | Deep-dive technical competency analyses powered by interactive, frequency-mapped skill radar charts. |
| **🕸️ Social Graphing** | Automatically correlate GitHub, LinkedIn, and personal portfolios to form a holistic engineering profile. |
| **📅 Seamless Scheduling** | Integrated single-click interview scheduling with automated candidate notifications. |

## 🚀 Tech Stack

### Frontend Architecture
* **Core:** React 18 with Vite for lightning-fast HMR and optimized builds.
* **Styling:** Tailwind CSS + Glassmorphism aesthetic for a dark, tactile, premium feel.
* **Motion:** Framer Motion for organic, physics-based micro-interactions.
* **Visualization:** Recharts for dynamic radar and performance charting.
* **Icons & Notifications:** Lucide React & Sonner toast engine.

### Backend Intelligence
* **Core API:** Python-based FastAPI framework for async, high-performance endpoints.
* **Document NLP Engine:** PyMuPDF & deep RegExp routines for robust, layout-agnostic PDF reading and algorithmic scoring mapping.

---

## 🛠️ Getting Started

### Prerequisites
Make sure you have the following installed on your machine:
- Node.js (`v18` or higher) & `npm` / `yarn`
- Python (`3.9` or higher)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/hireiq.git
cd hireiq
```

### 2. Start the Backend API (FastAPI)
HireIQ relies on a Python backend for ML-based resume parsing, skill density extraction, and scoring.
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies and run server
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
> **Note:** The backend will run at `http://localhost:8000`. Keep this terminal window active.

### 3. Start the Frontend Server (Vite Apps)
Open a **new terminal window** in the repository root folder.
```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

### 4. Experience HireIQ
Navigate to `http://localhost:5173` (or the port specified by Vite) in your browser and upload a CV to see the dynamic matching algorithm in action!

---

## 📂 Architecture

```text
hireiq/
├── backend/                # Python / FastAPI ML parsing engine
│   ├── api/                # Core routing endpoints
│   ├── parser/             # CV & NLP extraction algorithms
│   └── requirements.txt    # Python dependencies
├── frontend/               # React / Vite Client
│   ├── src/
│   │   ├── components/     # High-end interactive UI (MagneticCard, Modals)
│   │   ├── pages/          # Primary views (Dashboard, Analyzer, View)
│   │   ├── data/           # Intelligent frontend mock controllers / data processing
│   │   └── lib/            # Shared utilities & animation configs
│   ├── public/             # Static graphics
│   └── tailwind.config.js  # Theming and custom CSS variables
└── README.md
```

## 🎨 Design Philosophy

HireIQ is built with strict adherence to a **"Glassmorphism & Neon Dark"** modern aesthetic:
- **Core Background:** Deep abyss (`#0A0A0B`) ensuring minimal eye strain.
- **Accents:** Violet, Mint, and Rose gradients providing intelligent hierarchy.
- **Interactions:** Magnetic layouts, glowing hover states, and smooth staggered entrance animations for an organic feel.

---

<div align="center">
  <sub>Built with ❤️ by the HireIQ Engineering Team.</sub>
</div>
