# AI Growth Operator — Project Doc

## Stack
| Layer | Tech |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.10+ |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI | Google Gemini 2.0 Flash Lite |
| RAG | ChromaDB + all-MiniLM-L6-v2 |
| Charts | Plotly → PNG |
| PDFs | ReportLab |

## Quick Start
```bash
chmod +x setup.sh dev.sh
./setup.sh          # one-time
./dev.sh            # start both servers
```
Open http://localhost:3000

## Env Variables (backend/.env)
| Variable | Required | Notes |
|---|---|---|
| DATABASE_URL | Yes | sqlite:///./acrs.db or postgres:// |
| JWT_SECRET_KEY | Yes | random string |
| SECRET_KEY | Yes | random string |
| GEMINI_API_KEY | No | enables AI chatbot |
| SMTP_USER / SMTP_PASSWORD | No | Gmail for email reports |

## CSV Format
```
date,campaign,impressions,clicks,spend,leads
2024-01-01,Campaign A,50000,600,320.50,45
```

## Project Structure
```
ACRS/
├── backend/        # FastAPI — all logic + API
│   ├── main.py     # all endpoints
│   ├── rag.py      # ChromaDB indexer
│   ├── chatbot.py  # Gemini chat
│   ├── intelligence.py
│   ├── data_processor.py
│   ├── visualizer.py
│   ├── report_generator.py
│   └── database/
├── frontend/       # Next.js
│   └── app/
│       ├── page.tsx          # Dashboard
│       ├── ai-engine/        # AI Growth Engine
│       ├── clients/          # Client management
│       ├── reports/          # PDF + Email
│       └── chatbot/          # AI Chatbot
├── setup.sh
└── dev.sh
```
