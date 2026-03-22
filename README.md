# 🛡️ Techfiesta — AI-Powered Plagiarism & Authentication Detector

> **An intelligent, multi-modal plagiarism detection system that goes beyond copy-paste — detecting semantic similarity, structural code cloning, and handwritten submission authenticity.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%2F%20Flask-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![HTML](https://img.shields.io/badge/Frontend-HTML%20%2F%20CSS%20%2F%20JS-orange?style=flat-square&logo=html5)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-blueviolet?style=flat-square)](https://www.trychroma.com/)
[![Sentence Transformers](https://img.shields.io/badge/NLP-Sentence--Transformers-yellow?style=flat-square)](https://www.sbert.net/)
[![Tree-sitter](https://img.shields.io/badge/Code%20Analysis-Tree--sitter%20AST-lightgrey?style=flat-square)](https://tree-sitter.github.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

---

## 📌 Table of Contents

- [About the Project](#-about-the-project)
- [The Problem We Solve](#-the-problem-we-solve)
- [What We Built](#-what-we-built)
- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
  - [Text Plagiarism Detection](#-text-plagiarism-detection)
  - [Code Plagiarism Detection](#-code-plagiarism-detection)
  - [Handwriting to Text](#-handwriting-to-text)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [User Dashboards](#-user-dashboards)
- [Originality Report](#-originality-report-explainable-ai)
- [Getting Started](#-getting-started)
- [API Reference](#-api-reference)
- [Future Enhancements](#-future-enhancements)
- [Contributors](#-contributors)
- [License](#-license)

---

## 🧭 About the Project

**Techfiesta Plagiarism & Authentication Detector** is an AI-powered web application built for academic integrity. It detects plagiarism and verifies originality across **text documents**, **source code**, and **handwritten submissions** — all through a clean, role-based web interface for both students and teachers.

Unlike traditional checkers that rely solely on exact string matches, this system uses **semantic embeddings**, **Abstract Syntax Tree (AST) analysis**, and **vector similarity search** to catch paraphrased, restructured, and obfuscated content that conventional tools miss entirely.

> 🏆 Built for **Techfiesta** — a competitive hackathon project showcasing full-stack AI engineering.

---

## ❌ The Problem We Solve

Traditional plagiarism checkers fall short in critical ways:

| Limitation | Impact |
|---|---|
| Only detect exact copy-paste | Paraphrased content slips through undetected |
| Surface-level code comparison | Renamed variables and reordered logic are invisible |
| Black-box similarity scores | Students and teachers can't understand *why* content was flagged |
| No support for handwritten work | Offline/handwritten submissions can't be verified |
| No LMS integration | Tools don't fit into existing academic workflows |

### ✅ Our Approach

We analyze **semantic meaning**, **logical structure**, and **submission context** to deliver accurate, fair, and fully explainable plagiarism detection — closing every gap that tools like basic diff-checkers leave open.

---

## 🔨 What We Built

- 🌐 **Web-based demo** supporting Text & Code plagiarism detection
- ⚡ **Real-time AI-powered analysis** with immediate results
- 🎓 **Separate Student & Teacher dashboards** with distinct workflows
- 🏫 **LMS-ready architecture** with simulated LTI integration
- 📋 **Explainable originality reports** — no black-box scores, just clear human-readable insights

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔍 Semantic Plagiarism Detection | Catches paraphrasing and meaning-level similarity, not just word matches |
| 🌳 AST-Based Code Analysis | Compares logical structure via Abstract Syntax Trees using Tree-sitter |
| ✍️ Handwriting OCR | Converts handwritten submissions to text for digital plagiarism checks |
| 💬 Citation Suggestion Engine | Recommends proper citations for flagged content |
| 🧠 Explainable AI Reports | Highlights exactly which sections are similar and why |
| 👩‍🏫 Teacher Batch Processing | Analyze entire class submissions at once |
| 📊 Side-by-Side Comparison | Visual diff of flagged submission vs. source material |
| 🗃️ Vector Similarity Storage | ChromaDB stores embeddings for fast, scalable comparisons |
| 🏫 LMS-Ready Design | Architecture designed for Moodle / Canvas integration |

---

## 🧠 How It Works

### 📄 Text Plagiarism Detection

The text analysis pipeline uses **Sentence Transformers** to encode submissions into high-dimensional semantic vectors, then compares them against stored embeddings in ChromaDB using **cosine similarity**.

```
Raw Text Input
      │
      ▼
  Preprocessing
  (tokenization, normalization, stop-word removal)
      │
      ▼
  Sentence Transformer
  (semantic embedding generation)
      │
      ▼
  ChromaDB Vector Search
  (cosine similarity against stored corpus)
      │
      ▼
  Similarity Scoring
  (originality % + flagged section identification)
      │
      ▼
  Citation Suggestion Engine
      │
      ▼
  Explainable Report Generation
```

**Why Semantic Embeddings?**
Simple keyword matching fails when a student writes *"The experiment yielded positive outcomes"* instead of the source's *"The results of the experiment were successful."* Sentence Transformers capture that both sentences mean the same thing — even without sharing a single keyword.

---

### 💻 Code Plagiarism Detection

Code comparison goes far beyond string matching. The system parses submitted code into an **Abstract Syntax Tree (AST)** using **Tree-sitter**, then compares the tree structure — making it robust against:

- Variable renaming (`x` → `myVariable`)
- Comment removal or addition
- Code reordering / restructuring
- Whitespace and formatting changes
- Logic duplication wrapped in different function names

```
Source Code Input
      │
      ▼
  Tree-sitter Parser
  (language-aware AST generation)
      │
      ▼
  AST Normalization
  (strip identifiers, normalize structure)
      │
      ▼
  Structural Fingerprinting
  (hash subtrees for efficient comparison)
      │
      ▼
  Pairwise Similarity Calculation
  (compare against submission corpus)
      │
      ▼
  Similarity Score + Flagged Blocks
```

**Supported Languages:** Python, JavaScript, C, C++, Java *(extensible via Tree-sitter grammars)*

---

### ✍️ Handwriting to Text

For institutions accepting physical or scanned handwritten submissions:

```
Scanned Image / Photo Upload
         │
         ▼
   Image Preprocessing
   (noise reduction, binarization, deskewing)
         │
         ▼
   OCR Engine
   (handwriting recognition → digital text)
         │
         ▼
   Standard Text Plagiarism Pipeline
   (same as text detection flow above)
```

This enables **offline → online submission verification**, ensuring handwritten work is held to the same academic integrity standards as digital submissions.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                         │
│                                                                 │
│   ┌─────────────────────┐      ┌──────────────────────────┐    │
│   │   Student Dashboard │      │    Teacher Dashboard     │    │
│   │                     │      │                          │    │
│   │  - Upload Text/Code │      │  - Batch Upload          │    │
│   │  - View Score       │      │  - Side-by-Side Compare  │    │
│   │  - See Citations    │      │  - Class Analytics       │    │
│   │  - Feedback Panel   │      │  - Export Reports        │    │
│   └──────────┬──────────┘      └──────────────┬───────────┘    │
└──────────────┼──────────────────────────────────┼──────────────┘
               │           REST API               │
               ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND LAYER                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     API GATEWAY                         │   │
│  │              (FastAPI / Flask REST API)                  │   │
│  └──────────┬──────────────────────────────────────────────┘   │
│             │                                                   │
│   ┌─────────┴──────────────────────────────────────────┐       │
│   │                  AI ENGINE                          │       │
│   │                                                     │       │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │       │
│   │  │  Text Module │  │  Code Module │  │  OCR     │  │       │
│   │  │              │  │              │  │  Module  │  │       │
│   │  │ Sentence     │  │ Tree-sitter  │  │          │  │       │
│   │  │ Transformers │  │ AST Parser   │  │ Image→   │  │       │
│   │  │ Cosine Sim   │  │ Struct. Hash │  │ Text     │  │       │
│   │  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  │       │
│   └─────────┴─────────────────┴───────────────┴────────┘       │
│             │                                                   │
│   ┌─────────▼───────────────────────────────────┐              │
│   │            SCORING & EXPLANATION LAYER       │              │
│   │  Originality % | Flagged Sections | Citations│              │
│   └─────────────────────────────────────────────┘              │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                             │
│                                                                 │
│   ┌──────────────────────────┐  ┌──────────────────────────┐   │
│   │       ChromaDB           │  │      JSON Storage        │   │
│   │  (Vector Embeddings)     │  │   (Metadata / Reports)   │   │
│   │  - Text embeddings       │  │   - Submission records   │   │
│   │  - Code fingerprints     │  │   - User sessions        │   │
│   │  - Similarity index      │  │   - Report history       │   │
│   └──────────────────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Data Flow Summary:**
```
User Input → Preprocessing → AI Similarity Engine → ChromaDB Vector Search
          → Scoring + Explanation Layer → Student / Teacher Dashboard
```

---

## 🛠️ Tech Stack

### 🌐 Frontend
| Technology | Purpose |
|---|---|
| HTML5 | Page structure and semantic markup |
| CSS3 | Styling, responsive layout, dashboard UI |
| JavaScript | Client-side interactivity and API calls |

### ⚙️ Backend
| Technology | Purpose |
|---|---|
| Python 3.10+ | Core application language |
| FastAPI / Flask | REST API server and routing |

### 🤖 AI / ML Engine
| Technology | Purpose |
|---|---|
| Sentence-Transformers | Semantic text embeddings (NLP) |
| Cosine Similarity | Vector-space similarity scoring |
| Tree-sitter | AST-based structural code parsing |
| OCR Engine | Handwriting-to-text conversion |

### 🗄️ Storage
| Technology | Purpose |
|---|---|
| ChromaDB | Vector similarity database for embedding storage and search |
| JSON | Lightweight metadata and report persistence |

### 🔧 Languages Breakdown (Repository)
| Language | Share |
|---|---|
| HTML | 52.2% |
| Python | 32.8% |
| CSS | 8.4% |
| JavaScript | 6.6% |

---

## 📁 Project Structure

```
Techfiesta-Plagiarism-Detector/
│
├── backend/
│   ├── main.py                  # FastAPI/Flask app entry point
│   ├── routes/
│   │   ├── text_routes.py       # Text plagiarism API endpoints
│   │   ├── code_routes.py       # Code plagiarism API endpoints
│   │   └── ocr_routes.py        # Handwriting/OCR endpoints
│   │
│   ├── services/
│   │   ├── text_detector.py     # Sentence-Transformers + cosine similarity
│   │   ├── code_detector.py     # Tree-sitter AST parsing + structural comparison
│   │   ├── ocr_service.py       # Handwriting → text conversion
│   │   └── report_generator.py  # Originality report builder
│   │
│   ├── db/
│   │   └── chroma_client.py     # ChromaDB connection and vector operations
│   │
│   └── requirements.txt         # Python dependencies
│
├── chroma_store/                # Persisted ChromaDB vector collections
│   ├── text_embeddings/         # Stored text submission vectors
│   └── code_fingerprints/       # Stored AST structural fingerprints
│
├── frontend/
│   ├── index.html               # Landing / login page
│   ├── student/
│   │   ├── dashboard.html       # Student submission interface
│   │   ├── result.html          # Originality score + report view
│   │   └── student.css
│   │
│   ├── teacher/
│   │   ├── dashboard.html       # Teacher batch analysis panel
│   │   ├── compare.html         # Side-by-side similarity viewer
│   │   └── teacher.css
│   │
│   └── assets/
│       ├── js/
│       │   ├── api.js           # API call handlers
│       │   └── charts.js        # Report visualization
│       └── css/
│           └── common.css
│
├── .gitignore
└── README.md
```

---

## 👥 User Dashboards

### 🎓 Student View

Students interact with a simple, guided upload interface:

1. **Upload** — Submit text (paste or upload `.txt`/`.pdf`), source code, or a scanned handwritten image.
2. **Analyze** — The system processes the submission in real time against the stored corpus.
3. **Results** — View the **Originality Score (%)**, highlighted flagged sections, and matched sources.
4. **Learn** — Receive citation recommendations and actionable feedback to improve academic integrity.
5. **Transparency** — No black-box scores: every flagged section links to the matched source with a clear explanation.

---

### 👩‍🏫 Teacher View

Teachers get a powerful batch analysis and monitoring panel:

1. **Batch Upload** — Submit an entire class's assignments in one operation.
2. **Pairwise Analysis** — See similarity scores across all submission pairs.
3. **Side-by-Side Comparison** — Detailed diff view of any two flagged submissions.
4. **Class Analytics** — Distribution of originality scores, most common flagged sources.
5. **Export** — Download structured originality reports for records or academic hearings.

---

## 📋 Originality Report — Explainable AI

Every submission generates a full, human-readable report:

```
╔══════════════════════════════════════════════════════╗
║            ORIGINALITY REPORT                        ║
╠══════════════════════════════════════════════════════╣
║  Submission:      assignment_2_john.py               ║
║  Analyzed On:     2026-03-21 14:32:00                ║
║  Type:            Code (Python)                      ║
╠══════════════════════════════════════════════════════╣
║  ORIGINALITY SCORE:   63%                            ║
║  SIMILARITY FOUND:    37%                            ║
╠══════════════════════════════════════════════════════╣
║  FLAGGED SECTIONS                                    ║
║  ─────────────────────────────────────────────────── ║
║  [Lines 12–29] → 91% match with submission_03.py    ║
║   Reason: Identical AST structure after variable    ║
║   renaming. Logic flow is structurally identical.   ║
║                                                      ║
║  [Lines 44–51] → 74% match with submission_07.py    ║
║   Reason: Reordered conditional blocks with same    ║
║   underlying logic tree.                            ║
╠══════════════════════════════════════════════════════╣
║  CITATION RECOMMENDATIONS                           ║
║  ─────────────────────────────────────────────────── ║
║  If referencing external sources, cite as:          ║
║  → APA / IEEE / MLA format suggestions              ║
╚══════════════════════════════════════════════════════╝
```

**Report Components:**
- 🔢 **Originality Score (%)** — Overall percentage of original content
- 🧩 **Highlighted Similar Sections** — Exact line ranges flagged, with match percentages
- 📌 **Source References** — The matched submissions or sources
- 🧠 **Explanation** — Human-readable reason for each flag (not just a number)
- 📚 **Citation Recommendations** — Guidance for properly attributing matched content

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- `pip` package manager
- A modern browser (Chrome / Firefox recommended)

---

### 1. Clone the Repository

```bash
git clone https://github.com/Swara-art/Techfiesta-Plagiarism-Detector.git
cd Techfiesta-Plagiarism-Detector
```

---

### 2. Set Up a Virtual Environment (Recommended)

```bash
python -m venv venv

# On macOS / Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

---

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Key packages installed:
- `sentence-transformers` — NLP semantic embedding model
- `chromadb` — Vector similarity database
- `tree-sitter` — AST-based code parser
- `fastapi` / `flask` — Backend web framework
- `uvicorn` — ASGI server (for FastAPI)

---

### 4. Run the Backend Server

**If using FastAPI:**
```bash
uvicorn main:app --reload --port 8000
```

**If using Flask:**
```bash
python main.py
```

The API will be available at: `http://localhost:8000`

---

### 5. Open the Frontend

Open `frontend/index.html` directly in your browser, or serve it with a local server:

```bash
cd ../frontend
python -m http.server 3000
```

Then navigate to: `http://localhost:3000`

---

### 6. Using the Application

**As a Student:**
1. Go to the Student Dashboard
2. Paste or upload your text/code/image
3. Click **Analyze**
4. Review your Originality Report

**As a Teacher:**
1. Go to the Teacher Dashboard
2. Upload a batch of student submissions
3. View pairwise similarity scores
4. Click any pair for a detailed comparison report

---

## 📡 API Reference

### Text Plagiarism Check

```http
POST /api/check/text
Content-Type: application/json

{
  "submission_id": "student_123",
  "content": "Your text content here...",
  "mode": "semantic"
}
```

**Response:**
```json
{
  "originality_score": 78.4,
  "similarity_percentage": 21.6,
  "flagged_sections": [
    {
      "start": 0,
      "end": 142,
      "match_score": 0.89,
      "matched_source": "submission_045",
      "reason": "High semantic similarity detected via cosine distance"
    }
  ],
  "citations": ["Suggested citation format..."]
}
```

---

### Code Plagiarism Check

```http
POST /api/check/code
Content-Type: application/json

{
  "submission_id": "student_123",
  "code": "def bubble_sort(arr): ...",
  "language": "python"
}
```

**Response:**
```json
{
  "originality_score": 55.2,
  "similarity_percentage": 44.8,
  "flagged_blocks": [
    {
      "lines": "12-29",
      "match_score": 0.91,
      "matched_source": "submission_003",
      "reason": "Identical AST structure after identifier normalization"
    }
  ]
}
```

---

### Handwriting OCR + Check

```http
POST /api/check/handwritten
Content-Type: multipart/form-data

file: <image file (.jpg / .png / .pdf)>
submission_id: student_123
```

**Response:**
```json
{
  "extracted_text": "The extracted text from the handwritten image...",
  "originality_score": 82.1,
  "flagged_sections": [...],
  "citations": [...]
}
```

---

## 🔮 Future Enhancements

| Feature | Description |
|---|---|
| 🌍 Multi-Language Detection | Support plagiarism detection across different human languages |
| 🎙️ Voice-to-Text Submission | Analyze spoken/audio submissions for plagiarism |
| ⛓️ Blockchain Authentication | Immutable timestamped submission records for tamper-proof verification |
| 🏫 Direct LMS Integration | Native plugins for Moodle and Canvas |
| 📊 AI Academic Integrity Scoring | Composite scoring model factoring history, patterns, and context |
| 🤖 AI-Content Detection | Flag AI-generated text (GPT, Gemini, etc.) alongside plagiarism |
| 📁 Archive & Batch Export | Export full class reports in PDF/CSV for institutional records |

---

**AI Models & Logic:** NLP Semantic Embeddings (Sentence-Transformers) + AST Structural Analysis (Tree-sitter)

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details.

---

## 🙌 Acknowledgements

- [Sentence-Transformers](https://www.sbert.net/) — for semantic NLP embeddings
- [ChromaDB](https://www.trychroma.com/) — for vector similarity storage
- [Tree-sitter](https://tree-sitter.github.io/) — for language-aware AST parsing
- [FastAPI](https://fastapi.tiangolo.com/) — for the high-performance Python backend

---

<p align="center">
  ⭐ If you found this project useful, please consider starring the repository!<br/>
  Built with ❤️ for academic integrity and fair assessment.
</p>
