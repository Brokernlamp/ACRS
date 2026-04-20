# 🚀 AI Growth Operator

**Transform marketing agencies from report generators to AI-powered growth partners.**

An intelligent digital marketing analytics platform that provides predictive analytics, budget optimization, and automated reporting for agencies managing multiple clients.

---

## ✨ Features

### Current (v0.2.0)
- ✅ **Multi-client management** — Manage unlimited clients with individual settings
- ✅ **User authentication** — Secure JWT-based login system
- ✅ **Data persistence** — PostgreSQL/SQLite database with full history
- ✅ **Predictive analytics** — 7-day forecasts for leads, CPL, and CTR
- ✅ **Performance scoring** — AI-powered campaign ranking (0-100 scale)
- ✅ **Budget optimization** — Automated budget allocation recommendations
- ✅ **Anomaly detection** — Pattern recognition and trend analysis
- ✅ **Scenario simulator** — "What-if" budget change modeling
- ✅ **Professional reports** — Client-ready PDF generation
- ✅ **Email delivery** — Automated report distribution
- ✅ **Premium UI** — Modern, responsive dashboard design
- ✅ **Google Gemini integration** — LLM-powered insights (optional)

### Coming Soon
- 🔄 Google Ads API integration (Week 3)
- 🔄 Meta Ads API integration (Week 4)
- 🤖 **AI Chatbot Assistant** (Week 5-6) - Natural language queries with vector search
- 🔄 Real-time alerts (email/Slack)
- 🔄 White-label branding
- 🔄 Scheduled reports
- 🔄 Creative-level tracking
- 🔄 Audience insights

---

## 🏗️ Tech Stack

- **Frontend:** Gradio (Python-based UI)
- **Backend:** Python 3.10+
- **Database:** PostgreSQL / SQLite
- **Auth:** JWT + bcrypt
- **AI:** Google Gemini API (optional)
- **Charts:** Plotly
- **PDFs:** ReportLab

---

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- PostgreSQL (optional, SQLite works for development)
- Git

### Step 1: Clone Repository
```bash
git clone <your-repo-url>
cd ACRS
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

**Required settings:**
```bash
# Minimum configuration
DATABASE_URL=sqlite:///./acrs.db
JWT_SECRET_KEY=your-random-secret-key-here
SECRET_KEY=another-random-secret-key
```

**Optional (for enhanced features):**
```bash
# Google Gemini API (for AI-powered insights)
GEMINI_API_KEY=your-gemini-api-key

# Email delivery
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
```

### Step 5: Initialize Database
```bash
python init_db.py
```

You should see:
```
✅ Database initialized successfully!
Tables created:
  - users
  - clients
  - campaigns
  - campaign_data
  - api_connections
  - alerts
  - reports
```

### Step 6: Run Application
```bash
python app.py
```

Open browser to: **http://localhost:7860**

---

## 🚀 Quick Start Guide

### 1. Create Account
- Click "Register" (coming soon in UI)
- Or use the database directly for now

### 2. Add a Client
```python
# Temporary: Use Python to add first client
from database import SessionLocal, crud

db = SessionLocal()
user = crud.get_user_by_email(db, "your@email.com")
client = crud.create_client(
    db, 
    user_id=user.id,
    name="Acme Corp",
    industry="SaaS",
    target_cpl=50.0,
    monthly_budget=10000.0
)
db.close()
```

### 3. Upload Campaign Data
- Use the provided `sample_data.csv` as a template
- CSV must have columns: `date`, `campaign`, `impressions`, `clicks`, `spend`, `leads`
- Upload via the dashboard

### 4. View Intelligence
- Navigate to "AI Growth Engine" tab
- See predictions, recommendations, and budget optimization
- Run scenario simulations

### 5. Generate Reports
- Go to "Reports & Email" tab
- Download PDF (Standard or AI Growth Strategy)
- Send via email to clients

---

## 📊 CSV Format

Your CSV must include these columns:

| Column | Type | Description |
|--------|------|-------------|
| `date` | Date | YYYY-MM-DD format |
| `campaign` | String | Campaign name |
| `impressions` | Integer | Ad impressions |
| `clicks` | Integer | Ad clicks |
| `spend` | Float | Ad spend in dollars |
| `leads` | Integer | Leads generated |

**Example:**
```csv
date,campaign,impressions,clicks,spend,leads
2024-01-01,Campaign A,50000,600,320.50,45
2024-01-01,Campaign B,30000,180,150.00,12
2024-01-02,Campaign A,52000,650,340.00,50
```

---

## 🔐 Getting API Keys

### Google Gemini API (Optional)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy key to `.env` file: `GEMINI_API_KEY=your-key-here`

**Note:** Gemini is optional. The system works without it using rule-based intelligence.

### Gmail App Password (For Email Reports)
1. Enable 2FA on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate password for "Mail"
4. Copy to `.env`: `SMTP_PASSWORD=your-app-password`

---

## 🗄️ Database

### SQLite (Development)
Default configuration. No setup needed.
```bash
DATABASE_URL=sqlite:///./acrs.db
```

### PostgreSQL (Production)
1. Install PostgreSQL
2. Create database:
```sql
CREATE DATABASE acrs;
CREATE USER acrs_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE acrs TO acrs_user;
```
3. Update `.env`:
```bash
DATABASE_URL=postgresql://acrs_user:your_password@localhost:5432/acrs
```
4. Run `python init_db.py`

---

## 🧪 Testing

### Test with Sample Data
```bash
# Sample data is included
python app.py
# Upload sample_data.csv in the UI
```

### Run Unit Tests (Coming Soon)
```bash
pytest tests/
```

---

## 📁 Project Structure

```
ACRS/
├── app.py                      # Main Gradio application
├── auth.py                     # Authentication system
├── config.py                   # Configuration management
├── init_db.py                  # Database initialization
├── gemini_insights.py          # AI-powered insights
│
├── database/
│   ├── __init__.py            # Database setup
│   ├── models.py              # SQLAlchemy models
│   └── crud.py                # Database operations
│
├── intelligence.py             # Prediction engine
├── data_processor.py           # KPI calculations
├── visualizer.py               # Chart generation
├── report_generator.py         # PDF creation
├── emailer.py                  # Email delivery
├── utils.py                    # Utilities
│
├── sample_data.csv             # Example dataset
├── requirements.txt            # Dependencies
├── .env.example                # Environment template
├── PROJECT.md                  # Technical documentation
└── README.md                   # This file
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite:///./acrs.db` | Database connection string |
| `JWT_SECRET_KEY` | Yes | - | Secret for JWT tokens |
| `SECRET_KEY` | Yes | - | App secret key |
| `GEMINI_API_KEY` | No | - | Google Gemini API key |
| `SMTP_USER` | No | - | Gmail address for sending emails |
| `SMTP_PASSWORD` | No | - | Gmail app password |

See `.env.example` for full list.

---

## 🚢 Deployment

### Hugging Face Spaces (Free)
1. Create new Space at [huggingface.co/new-space](https://huggingface.co/new-space)
2. Choose "Gradio" SDK
3. Push code:
```bash
git remote add hf https://huggingface.co/spaces/<username>/<space-name>
git push hf main
```
4. Add secrets in Space settings (DATABASE_URL, JWT_SECRET_KEY, etc.)

**Note:** Hugging Face Spaces has limitations:
- No persistent storage (use external PostgreSQL)
- Limited compute resources
- Public by default

### Production (Recommended)
- **Frontend:** AWS EC2 / Render / Railway
- **Database:** AWS RDS / Supabase / Neon
- **Storage:** AWS S3 (for PDFs)
- **Monitoring:** Sentry

See `PROJECT.md` for detailed deployment guide.

---

## 🤝 Contributing

This is a proprietary project. For access or collaboration inquiries, contact the maintainer.

---

## 📞 Support

- **Documentation:** See `PROJECT.md` for technical details
- **Issues:** Check existing issues or create new one
- **Email:** [Your contact email]

---

## 📝 License

Proprietary — All rights reserved

---

## 🗺️ Roadmap

### Phase 1: Foundation (Current)
- [x] Database setup
- [x] User authentication
- [x] Multi-client management
- [x] Data persistence
- [ ] Historical comparison UI

### Phase 2: API Integrations (Week 3-4)
- [ ] Google Ads API
- [ ] Meta Ads API
- [ ] Real-time alerts
- [ ] Enhanced predictions

### Phase 3: AI Chatbot (Week 5-6) 🆕
- [ ] **Conversational AI Assistant** - Ask questions in natural language
- [ ] **Vector Database** - ChromaDB for semantic search
- [ ] **Free Embeddings** - HuggingFace sentence-transformers
- [ ] **Text-to-SQL** - Generate database queries from questions
- [ ] **Context Management** - Multi-turn conversations with memory
- [ ] **Session Storage** - Temporary vector embeddings per session
- See `CHATBOT_FEATURE.md` for full specification

### Phase 4: Polish (Week 7-8)
- [ ] White-label branding
- [ ] Scheduled reports
- [ ] Collaboration features
- [ ] Mobile app

See `PROJECT.md` for complete roadmap.

---

## 🎯 Success Metrics

- **Page load:** <2 seconds
- **Report generation:** <5 seconds
- **Uptime:** >99.5%
- **User retention:** >80% MoM

---

**Built with ❤️ for marketing agencies**

*Version 0.2.0-alpha — Last updated: 2024-01-XX*
