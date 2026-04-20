# 🚀 AI Growth Operator — Project Documentation

## 📋 Overview

**AI Growth Operator** is an intelligent digital marketing analytics platform that transforms campaign data into actionable growth strategies. Built for marketing agencies managing multiple clients, it provides predictive analytics, budget optimization, and automated reporting without requiring data science expertise.

---

## 🎯 Vision

Transform marketing agencies from "report generators" to "AI-powered growth partners" by providing:
- Predictive performance forecasting
- Automated budget optimization
- Real-time anomaly detection
- Client-ready strategic reports

---

## 🏗️ System Architecture

### Current Stack
```
Frontend:  Gradio (Python-based UI)
Backend:   Python 3.10+
Database:  [TO BE ADDED] PostgreSQL
Auth:      [TO BE ADDED] JWT-based
AI/ML:     Rule-based intelligence engine + Google Gemini API
Storage:   [TO BE ADDED] AWS S3 / Local filesystem
```

### Core Modules

```
project/
├── app.py                      # Gradio UI + routing
├── auth.py                     # [NEW] User authentication
├── database/
│   ├── models.py              # [NEW] SQLAlchemy models
│   ├── crud.py                # [NEW] Database operations
│   └── migrations/            # [NEW] Alembic migrations
├── api/
│   ├── google_ads.py          # [NEW] Google Ads API client
│   ├── meta_ads.py            # [NEW] Meta Ads API client
│   └── data_sync.py           # [NEW] Auto-sync scheduler
├── intelligence/
│   ├── intelligence.py        # Prediction engine (existing)
│   ├── gemini_insights.py     # [NEW] LLM-powered insights
│   └── anomaly_detector.py    # [NEW] Real-time alerts
├── processors/
│   ├── data_processor.py      # KPI calculations (existing)
│   └── multi_source.py        # [NEW] Multi-platform data merger
├── visualizer.py              # Chart generation (existing)
├── report_generator.py        # PDF generation (existing)
├── emailer.py                 # Email delivery (existing)
├── utils.py                   # Helpers (existing)
├── config.py                  # [NEW] Configuration management
├── requirements.txt
└── .env                       # [NEW] Environment variables
```

---

## 🗄️ Database Schema

### Users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    agency_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    subscription_tier VARCHAR(50) DEFAULT 'free'
);
```

### Clients
```sql
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    target_cpl DECIMAL(10,2),
    monthly_budget DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, name)
);
```

### Campaigns
```sql
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    campaign_name VARCHAR(255) NOT NULL,
    platform VARCHAR(50), -- 'google_ads', 'meta_ads', 'linkedin', 'manual'
    platform_campaign_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

### Campaign Data (Time Series)
```sql
CREATE TABLE campaign_data (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,
    leads INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue DECIMAL(10,2) DEFAULT 0,
    ctr DECIMAL(5,2),
    cpl DECIMAL(10,2),
    conversion_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(campaign_id, date)
);
```

### API Connections
```sql
CREATE TABLE api_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    account_id VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, platform)
);
```

### Alerts
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE SET NULL,
    alert_type VARCHAR(50), -- 'cpl_spike', 'ctr_drop', 'budget_pacing', 'zero_conversions'
    severity VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    message TEXT,
    metric_value DECIMAL(10,2),
    threshold_value DECIMAL(10,2),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Reports
```sql
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    report_type VARCHAR(50), -- 'standard', 'growth_strategy'
    date_range_start DATE,
    date_range_end DATE,
    pdf_path VARCHAR(500),
    generated_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP
);
```

---

## 🔄 Development Roadmap

### ✅ Phase 0: MVP (COMPLETED)
- [x] CSV upload & validation
- [x] KPI calculations (CTR, CPL, Conversion Rate)
- [x] Campaign summary & daily trends
- [x] Rule-based predictions (leads, CPL, CTR)
- [x] Performance scoring algorithm
- [x] Budget optimization formulas
- [x] Pattern detection (day-of-week, anomalies)
- [x] Scenario simulator
- [x] Plotly visualizations (6 charts)
- [x] PDF report generation (standard + growth strategy)
- [x] Email delivery (SMTP)
- [x] Premium UI design with CSS

### 🚧 Phase 1: Foundation (CURRENT — Week 1-2)
**Goal: Make it usable for real agencies**

#### Week 1
- [ ] Database setup (PostgreSQL + SQLAlchemy)
- [ ] User authentication system
  - [ ] Registration
  - [ ] Login/logout
  - [ ] Password reset
  - [ ] JWT tokens
- [ ] Multi-client management
  - [ ] Create/edit/delete clients
  - [ ] Client switcher dropdown
  - [ ] Per-client settings
- [ ] Data persistence layer
  - [ ] Save uploaded CSV data to DB
  - [ ] Historical data storage
  - [ ] Query optimization

#### Week 2
- [ ] Client dashboard redesign
  - [ ] Client list view
  - [ ] Quick stats per client
  - [ ] Last sync timestamp
- [ ] Historical comparison
  - [ ] Week-over-week metrics
  - [ ] Month-over-month trends
  - [ ] Custom date range selector
- [ ] Data export
  - [ ] Export to CSV
  - [ ] Export to Excel
  - [ ] API endpoint for data access

### 🎯 Phase 2: Intelligence (Week 3-4)
**Goal: Make it valuable**

#### Week 3
- [ ] Google Ads API integration
  - [ ] OAuth flow
  - [ ] Account selection
  - [ ] Campaign import
  - [ ] Daily auto-sync
- [ ] Meta Ads API integration
  - [ ] OAuth flow
  - [ ] Ad account selection
  - [ ] Campaign import
  - [ ] Daily auto-sync
- [ ] Multi-source data merger
  - [ ] Combine Google + Meta + Manual CSV
  - [ ] Deduplication logic
  - [ ] Platform attribution

#### Week 4
- [ ] Real-time anomaly detection
  - [ ] CPL spike detector (>30% increase)
  - [ ] CTR drop detector (>20% decrease)
  - [ ] Zero conversion alerts
  - [ ] Budget pacing alerts
- [ ] Alert system
  - [ ] Email notifications
  - [ ] In-app notification center
  - [ ] Alert preferences per client
  - [ ] Slack webhook integration
- [ ] Enhanced predictions
  - [ ] Confidence intervals
  - [ ] Seasonality detection
  - [ ] Budget pacing forecasts

### 🤖 Phase 3: AI Enhancement (Week 5-6)
**Goal: Make it intelligent**

#### Week 5
- [ ] Google Gemini integration
  - [ ] Executive summary generation
  - [ ] Natural language insights
  - [ ] Recommendation explanations
  - [ ] Client-friendly narratives
- [ ] Creative-level tracking
  - [ ] Ad creative breakdown
  - [ ] Creative fatigue detection
  - [ ] A/B test winner detection
- [ ] Audience insights
  - [ ] Demographic breakdown
  - [ ] Device performance
  - [ ] Time-of-day heatmaps

#### Week 6
- [ ] Advanced analytics
  - [ ] Funnel analysis
  - [ ] Attribution modeling
  - [ ] Cohort analysis
  - [ ] LTV integration
- [ ] Industry benchmarks
  - [ ] Vertical-specific norms
  - [ ] Percentile rankings
  - [ ] Competitive positioning

### 🎨 Phase 4: Polish (Week 7-8)
**Goal: Make it sellable**

#### Week 7
- [ ] White-label system
  - [ ] Custom branding upload
  - [ ] Color scheme customization
  - [ ] Logo in reports
  - [ ] Agency name replacement
- [ ] Enhanced PDF reports
  - [ ] Executive summary page
  - [ ] Client logo integration
  - [ ] Narrative flow
  - [ ] Comparison callouts

#### Week 8
- [ ] Scheduled reports
  - [ ] Weekly auto-generation
  - [ ] Auto-email to clients
  - [ ] Custom schedules per client
- [ ] Collaboration features
  - [ ] Comments on campaigns
  - [ ] Task assignments
  - [ ] Team member invites
- [ ] Goal tracking
  - [ ] Monthly targets
  - [ ] Progress bars
  - [ ] Pacing alerts

---

## 🔐 Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/acrs

# Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key-here

# Google Ads API
GOOGLE_ADS_CLIENT_ID=your-client-id
GOOGLE_ADS_CLIENT_SECRET=your-client-secret
GOOGLE_ADS_DEVELOPER_TOKEN=your-developer-token

# Meta Ads API
META_APP_ID=your-app-id
META_APP_SECRET=your-app-secret

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# AWS S3 (for PDF storage)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=acrs-reports
AWS_REGION=us-east-1

# App Config
APP_ENV=development
DEBUG=True
SECRET_KEY=your-app-secret-key
```

---

## 🧪 Testing Strategy

### Unit Tests
- Database CRUD operations
- KPI calculation accuracy
- Prediction algorithm validation
- Alert trigger logic

### Integration Tests
- API connection flows
- Data sync pipelines
- Report generation end-to-end
- Email delivery

### Load Tests
- 100 concurrent users
- 1000 campaigns per user
- 90 days of historical data
- Report generation under 5 seconds

---

## 📊 Success Metrics

### Technical KPIs
- Page load time: <2 seconds
- API response time: <500ms
- Report generation: <5 seconds
- Uptime: >99.5%

### Business KPIs
- User retention: >80% month-over-month
- Daily active users: >60% of total users
- Reports generated per user: >10/month
- API sync success rate: >95%

---

## 🚀 Deployment

### Current: Hugging Face Spaces
- Free tier
- Gradio native support
- No database persistence (limitation)

### Target: Production Infrastructure
```
Frontend:  Gradio → Hosted on AWS EC2 / Render
Database:  PostgreSQL → AWS RDS / Supabase
Storage:   AWS S3 → PDF reports
Cache:     Redis → Session management
Queue:     Celery + Redis → Background jobs (data sync, report generation)
Monitor:   Sentry → Error tracking
Analytics: PostHog → User behavior
```

---

## 💰 Monetization Strategy

### Pricing Tiers

| Tier | Price | Clients | Features |
|------|-------|---------|----------|
| **Free** | $0 | 1 | Manual CSV only, basic reports |
| **Starter** | $49/mo | 5 | API integrations, alerts |
| **Agency** | $149/mo | 20 | White-label, scheduled reports |
| **Pro** | $297/mo | 50 | Advanced analytics, collaboration |
| **Enterprise** | $997/mo | Unlimited | Custom integrations, dedicated support |

---

## 🔒 Security Considerations

- [ ] Password hashing (bcrypt)
- [ ] JWT token expiration
- [ ] API rate limiting
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS protection
- [ ] CSRF tokens
- [ ] Encrypted API tokens in database
- [ ] HTTPS only in production
- [ ] Regular security audits

---

## 📚 Documentation TODO

- [ ] API documentation (Swagger/OpenAPI)
- [ ] User guide (how to connect Google Ads)
- [ ] Video tutorials
- [ ] Developer documentation
- [ ] Deployment guide
- [ ] Troubleshooting guide

---

## 🤝 Contributing

### Code Style
- PEP 8 compliance
- Type hints for all functions
- Docstrings for public APIs
- Maximum line length: 120 characters

### Git Workflow
- `main` branch: production-ready code
- `develop` branch: integration branch
- Feature branches: `feature/user-auth`, `feature/google-ads-api`
- Commit messages: Conventional Commits format

---

## 📞 Support

- Email: support@aigrowthoperator.com (TODO)
- Documentation: docs.aigrowthoperator.com (TODO)
- Community: Discord server (TODO)

---

## 📝 License

Proprietary — All rights reserved

---

**Last Updated:** 2024-01-XX  
**Version:** 0.2.0-alpha  
**Status:** Active Development
