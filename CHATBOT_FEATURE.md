# 🤖 AI Chatbot Feature Specification

**Feature:** Conversational AI Assistant for Campaign Analytics  
**Priority:** High  
**Estimated Week:** Week 5-6 (After API Integrations)  
**Status:** Planned

---

## 📋 Overview

Add an intelligent chatbot that can answer questions about campaign performance by querying the database and using vector embeddings for semantic search. The chatbot will have access to real-time campaign data from Meta Ads, Google Ads, and historical data.

---

## 🎯 Use Cases

### For Marketing Agencies
- "Which campaigns are underperforming this month?"
- "Show me the best performing ad creative for Client X"
- "What's the average CPL across all clients?"
- "Compare this week's performance to last week"
- "Which client has the highest ROI?"

### For Campaign Analysis
- "Why is Campaign A's CTR dropping?"
- "What budget changes would improve my leads?"
- "Show me trends for the last 30 days"
- "Which keywords are driving the most conversions?"
- "Predict next week's performance"

### For Reporting
- "Generate a summary for my client meeting"
- "What insights should I share with Client Y?"
- "Create a list of action items based on current data"

---

## 🏗️ Architecture

### Data Flow
```
1. API Integration (Meta/Google Ads)
   ↓
2. Store in PostgreSQL (structured data)
   ↓
3. Generate Embeddings (campaign descriptions, insights, metrics)
   ↓
4. Store in Vector DB (temporary session storage)
   ↓
5. User asks question via Chatbot
   ↓
6. Semantic search in Vector DB + SQL queries
   ↓
7. LLM generates natural language response
   ↓
8. Display to user with citations/sources
```

### Components

#### 1. Vector Database (Temporary Session Storage)
**Purpose:** Store embeddings for semantic search during user session

**Options:**
- **ChromaDB** (Recommended) - Free, lightweight, in-memory
- **Qdrant** - Free tier, fast, good for production
- **Weaviate** - Free cloud tier available
- **FAISS** - Facebook's library, completely free, local

**What to Store:**
- Campaign descriptions + metadata
- Historical insights and recommendations
- Client notes and context
- Performance summaries
- Anomaly detection results

#### 2. Embedding API (Free Options)

**Option A: OpenAI Embeddings** (Recommended)
- Model: `text-embedding-3-small`
- Cost: $0.02 per 1M tokens (~$0.0001 per query)
- Dimensions: 1536
- Quality: Excellent
- Free tier: No, but very cheap

**Option B: Cohere Embeddings** (Free Tier)
- Model: `embed-english-v3.0`
- Free tier: 100 API calls/month
- Dimensions: 1024
- Quality: Very good
- Upgrade: $1/1000 calls

**Option C: HuggingFace (Completely Free)**
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Cost: FREE (self-hosted)
- Dimensions: 384
- Quality: Good for most use cases
- No API limits

**Option D: Google Vertex AI Embeddings** (Free Tier)
- Model: `textembedding-gecko`
- Free tier: 1000 requests/month
- Dimensions: 768
- Quality: Excellent

**Recommendation:** Start with HuggingFace (free), upgrade to OpenAI if needed.

#### 3. LLM for Chat (Already Integrated)
- **Google Gemini** (Already in project)
- Model: `gemini-pro`
- Free tier: 60 requests/min
- Perfect for conversational AI

---

## 🛠️ Implementation Plan

### Phase 1: Basic Chatbot (Week 5)
**Duration:** 3-4 days

**Tasks:**
1. Add chatbot UI tab in Gradio
2. Integrate Google Gemini for responses
3. Create SQL query generator (text-to-SQL)
4. Basic Q&A without vector search
5. Context management (last 5 messages)

**Example:**
```python
# Simple chatbot without vector DB
def chat(message, history):
    # Get relevant data from PostgreSQL
    context = get_campaign_context(user_id, client_id)
    
    # Generate response with Gemini
    prompt = f"Context: {context}\n\nUser: {message}\n\nAssistant:"
    response = gemini.generate(prompt)
    
    return response
```

### Phase 2: Vector Search Integration (Week 6)
**Duration:** 3-4 days

**Tasks:**
1. Install ChromaDB or FAISS
2. Generate embeddings for campaign data
3. Implement semantic search
4. Combine SQL + vector search results
5. Add citation/source tracking
6. Session-based vector storage (clear on logout)

**Example:**
```python
# With vector search
def chat_with_vectors(message, history, session_id):
    # 1. Semantic search in vector DB
    similar_docs = vector_db.search(message, top_k=5)
    
    # 2. SQL query for structured data
    sql_results = execute_smart_query(message)
    
    # 3. Combine context
    context = {
        "similar_campaigns": similar_docs,
        "current_metrics": sql_results,
        "chat_history": history[-5:]
    }
    
    # 4. Generate response
    response = gemini.generate_with_context(message, context)
    
    return response
```

### Phase 3: Advanced Features (Week 7)
**Duration:** 2-3 days

**Tasks:**
1. Multi-turn conversations with memory
2. Follow-up question handling
3. Chart generation from chat
4. Export chat insights to PDF
5. Voice input (optional)

---

## 💾 Vector Database Schema

### Collection: `campaign_embeddings`
```python
{
    "id": "campaign_123_2024-01-15",
    "embedding": [0.123, 0.456, ...],  # 384 or 1536 dimensions
    "metadata": {
        "campaign_id": 123,
        "campaign_name": "Summer Sale 2024",
        "client_id": 5,
        "client_name": "Acme Corp",
        "date": "2024-01-15",
        "metrics": {
            "impressions": 50000,
            "clicks": 600,
            "spend": 320.50,
            "leads": 45,
            "cpl": 7.12,
            "ctr": 1.2
        },
        "insights": "Campaign performing above target CPL...",
        "type": "campaign_summary"
    },
    "text": "Summer Sale 2024 campaign for Acme Corp generated 45 leads..."
}
```

### Collection: `insights_embeddings`
```python
{
    "id": "insight_456",
    "embedding": [...],
    "metadata": {
        "client_id": 5,
        "date": "2024-01-15",
        "type": "anomaly",
        "severity": "high"
    },
    "text": "CTR dropped 30% in the last 3 days, indicating ad fatigue..."
}
```

---

## 🔧 Technical Stack

### Required Libraries
```bash
# Vector DB
pip install chromadb  # or faiss-cpu

# Embeddings
pip install sentence-transformers  # HuggingFace (free)
# OR
pip install openai  # OpenAI embeddings (paid but cheap)
# OR
pip install cohere  # Cohere (free tier)

# Already have
# google-generativeai  # Gemini (already installed)
```

### Code Structure
```
ACRS/
├── chatbot/
│   ├── __init__.py
│   ├── chat_engine.py       # Main chatbot logic
│   ├── embeddings.py        # Embedding generation
│   ├── vector_store.py      # Vector DB operations
│   ├── query_generator.py   # Text-to-SQL
│   └── context_builder.py   # Context management
├── app.py                    # Add chatbot tab
└── requirements.txt          # Add new dependencies
```

---

## 🎨 UI Design

### Chatbot Tab
```
┌─────────────────────────────────────────────────┐
│  🤖 AI Campaign Assistant                       │
├─────────────────────────────────────────────────┤
│                                                 │
│  💬 Chat History                                │
│  ┌───────────────────────────────────────────┐ │
│  │ User: Which campaigns need attention?     │ │
│  │                                           │ │
│  │ AI: Based on your data, 3 campaigns      │ │
│  │     are underperforming:                 │ │
│  │     1. Campaign A - CPL $15 (target $10) │ │
│  │     2. Campaign B - CTR 0.5% (avg 1.2%)  │ │
│  │     3. Campaign C - Spend up 40%         │ │
│  │                                           │ │
│  │     [View Details] [Generate Report]     │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  💬 Ask a question...                           │
│  ┌───────────────────────────────────────────┐ │
│  │ Type your question here...                │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  [Send] [Clear Chat] [Export Conversation]     │
└─────────────────────────────────────────────────┘
```

---

## 📊 Example Queries & Responses

### Query 1: Performance Analysis
**User:** "Show me campaigns with CPL above $10"

**AI Response:**
```
I found 5 campaigns with CPL above $10:

1. **Campaign A** (Client: Acme Corp)
   - CPL: $12.50 (+25% vs target)
   - Spend: $2,500
   - Leads: 200
   - Recommendation: Reduce budget by 20%

2. **Campaign B** (Client: TechStart)
   - CPL: $15.00 (+50% vs target)
   - Spend: $3,000
   - Leads: 200
   - Recommendation: Pause and review targeting

[View Full Report] [Optimize Budgets]
```

### Query 2: Trend Analysis
**User:** "What's trending up this week?"

**AI Response:**
```
📈 Positive Trends (Last 7 Days):

✅ **Leads:** +15% (450 → 517)
✅ **CTR:** +0.3% (1.2% → 1.5%)
✅ **Conversion Rate:** +2% (3% → 5%)

📉 Areas of Concern:

⚠️ **CPL:** +$2.50 ($8 → $10.50)
⚠️ **Spend:** +30% ($5,000 → $6,500)

💡 Insight: Higher spend is driving more leads, but efficiency is declining.
```

### Query 3: Recommendations
**User:** "What should I do to improve ROI?"

**AI Response:**
```
Based on your current performance, here are 3 actionable recommendations:

1. **Reallocate Budget** 🎯
   - Move $500 from Campaign C (CPL $15) to Campaign A (CPL $7)
   - Expected impact: +25 leads, -$200 wasted spend

2. **Refresh Ad Creative** 🎨
   - Campaign B shows 30% CTR drop (ad fatigue)
   - Test new creatives this week

3. **Optimize Targeting** 🔍
   - Campaign D has high impressions but low clicks
   - Narrow audience to improve relevance

[Apply Recommendations] [Run Simulation]
```

---

## 🔐 Security & Privacy

### Data Handling
- **Session-based storage:** Vector DB cleared after logout
- **No PII in embeddings:** Only aggregate metrics and insights
- **Client isolation:** Each user only sees their own data
- **API key security:** Store in environment variables

### Rate Limiting
- Max 100 messages per session
- Max 10 messages per minute
- Prevent abuse and API cost overruns

---

## 💰 Cost Estimation

### Free Tier (Recommended for MVP)
- **Embeddings:** HuggingFace (FREE)
- **Vector DB:** ChromaDB in-memory (FREE)
- **LLM:** Google Gemini free tier (60 req/min)
- **Total:** $0/month

### Paid Tier (For Scale)
- **Embeddings:** OpenAI ($0.02/1M tokens) ≈ $5/month
- **Vector DB:** Qdrant cloud ($25/month)
- **LLM:** Gemini Pro ($0.50/1M tokens) ≈ $10/month
- **Total:** $40/month for 10,000 queries

---

## 📈 Success Metrics

### User Engagement
- Average messages per session: >5
- User satisfaction: >80%
- Query resolution rate: >90%

### Technical Performance
- Response time: <2 seconds
- Accuracy: >85% (human evaluation)
- Uptime: >99%

---

## 🗓️ Timeline

### Week 5: Basic Chatbot
- Day 1-2: UI implementation
- Day 3-4: Gemini integration
- Day 5: Testing & refinement

### Week 6: Vector Search
- Day 1-2: Vector DB setup
- Day 3-4: Embedding generation
- Day 5: Integration & testing

### Week 7: Polish
- Day 1-2: Advanced features
- Day 3: Performance optimization
- Day 4-5: User testing & bug fixes

---

## 🚀 Future Enhancements

### Phase 4 (Week 8+)
- **Voice input/output:** Whisper API integration
- **Multi-language support:** Translate queries and responses
- **Proactive insights:** AI suggests questions to ask
- **Slack/Teams integration:** Chat in your workspace
- **Mobile app:** Native iOS/Android chatbot

### Advanced Features
- **Custom training:** Fine-tune on agency-specific data
- **Predictive Q&A:** "You might want to know..."
- **Automated reporting:** "Generate weekly summary"
- **Collaborative chat:** Multiple users in same conversation

---

## 📚 Resources

### Free Embedding APIs
1. **HuggingFace Inference API**
   - URL: https://huggingface.co/inference-api
   - Free tier: Unlimited (rate limited)
   - Models: 100+ embedding models

2. **Cohere Free Tier**
   - URL: https://cohere.com/pricing
   - Free: 100 calls/month
   - Model: embed-english-v3.0

3. **Google Vertex AI**
   - URL: https://cloud.google.com/vertex-ai/pricing
   - Free: 1000 requests/month
   - Model: textembedding-gecko

### Vector Databases
1. **ChromaDB** (Recommended for MVP)
   - Docs: https://docs.trychroma.com/
   - Free, open-source, in-memory

2. **FAISS** (Facebook)
   - Docs: https://github.com/facebookresearch/faiss
   - Free, fast, local

3. **Qdrant**
   - Docs: https://qdrant.tech/
   - Free tier: 1GB storage

### Tutorials
- Text-to-SQL: https://github.com/defog-ai/sqlcoder
- RAG with ChromaDB: https://docs.trychroma.com/guides
- Gemini Chat: https://ai.google.dev/tutorials/python_quickstart

---

## ✅ Checklist

### Before Starting
- [ ] Complete API integrations (Meta, Google Ads)
- [ ] Database has sufficient historical data
- [ ] Gemini API key configured and tested
- [ ] Choose embedding provider (HuggingFace recommended)
- [ ] Choose vector DB (ChromaDB recommended)

### Implementation
- [ ] Install required libraries
- [ ] Create chatbot UI tab
- [ ] Implement basic Q&A
- [ ] Add vector search
- [ ] Test with real queries
- [ ] Add error handling
- [ ] Optimize performance
- [ ] User testing

### Launch
- [ ] Documentation complete
- [ ] Rate limiting configured
- [ ] Monitoring setup
- [ ] User feedback mechanism
- [ ] Cost tracking

---

**Status:** Ready for implementation in Week 5-6  
**Dependencies:** API integrations (Week 3-4)  
**Estimated Effort:** 8-10 days  
**ROI:** High - Major differentiator for agencies

---

*Last updated: January 2025*
