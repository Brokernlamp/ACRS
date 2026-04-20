# AI Growth Operator

Marketing analytics platform for agencies — predictive insights, budget optimization, AI chatbot, automated reporting.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.10+ |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI | Google Gemini 1.5 Flash |
| RAG | ChromaDB + sentence-transformers (all-MiniLM-L6-v2) |
| Charts | Plotly |
| PDFs | ReportLab |

## Quick Start

**Requirements:** Python 3.10+, Node.js 18+

```bash
git clone <repo-url>
cd ACRS

# 1. Run setup (one time)
chmod +x setup.sh dev.sh
./setup.sh

# 2. Add your Gemini API key (optional — enables AI chatbot)
# Edit backend/.env → GEMINI_API_KEY=your-key-here

# 3. Start
./dev.sh
```

Open **http://localhost:3000**

## Features

| Page | What it does |
|---|---|
| Dashboard | Upload CSV, view KPIs and charts |
| AI Growth Engine | Predictions, budget recommendations, scenario simulator |
| Clients | Manage multiple clients |
| Reports & Email | Download PDF reports, send via email |
| AI Chatbot | Ask questions about your data in natural language |

## CSV Format

```csv
date,campaign,impressions,clicks,spend,leads
2024-01-01,Campaign A,50000,600,320.50,45
2024-01-01,Campaign B,30000,180,150.00,12
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | `sqlite:///./acrs.db` or PostgreSQL URL |
| `JWT_SECRET_KEY` | Yes | Random secret for JWT tokens |
| `SECRET_KEY` | Yes | App secret key |
| `GEMINI_API_KEY` | No | Enables AI chatbot ([get one here](https://makersuite.google.com/app/apikey)) |
| `SMTP_USER` | No | Gmail address for email reports |
| `SMTP_PASSWORD` | No | Gmail App Password |

## Project Structure

```
ACRS/
├── backend/          # FastAPI + all Python logic
│   ├── main.py       # API endpoints
│   ├── rag.py        # ChromaDB vector store
│   ├── chatbot.py    # Gemini chat with RAG
│   ├── intelligence.py
│   ├── data_processor.py
│   ├── visualizer.py
│   ├── report_generator.py
│   └── database/
├── frontend/         # Next.js app
│   ├── app/
│   │   ├── page.tsx          # Dashboard
│   │   ├── ai-engine/        # AI Growth Engine
│   │   ├── clients/          # Client management
│   │   ├── reports/          # Reports & Email
│   │   └── chatbot/          # AI Chatbot
│   ├── components/
│   └── lib/
├── setup.sh          # One-time setup
└── dev.sh            # Start both servers
```
