You are building a multi-platform advertising analytics dashboard (ACRS) that consolidates 
campaign data from Google Ads, Meta Ads, and potentially other platforms into a unified interface.

## CURRENT STATE
- Dashboard exists with single-platform CSV upload capability
- Backend: FastAPI + Python, Frontend: Next.js + TypeScript
- Database: SQLAlchemy ORM with SQLite (dev) / PostgreSQL (prod)
- Analytics engine exists: performance scoring, budget optimization, predictions, waste detection

## GAPS TO FILL

### 1. DEMO/TEST DATA WITHOUT REAL ACCOUNTS
Create a mock API layer that simulates Google Ads and Meta Ads responses without requiring 
real advertising accounts or credentials. This allows:
- Local development and testing
- Live demos to potential customers
- QA environments
- Sandbox-safe experimentation

Requirements:
- Create realistic mock campaign data structures matching actual Google Ads API and Meta Ads API response formats
- Mock data should include: campaign_id, campaign_name, impressions, clicks, spend, conversions/leads, ctr, conversion_rate, cpl
- Add a `/api/demo/multi-platform-sync` endpoint that returns merged Google + Meta mock data
- Include at least 2-3 mock clients with multiple campaigns per platform (e.g., "Ajay", "TechStartup", "EcommerceBrand")
- Data should be realistic (e.g., CPL $20-$80, CTR 0.5%-3%, conversion rates 2%-15%)

### 2. MULTI-PLATFORM CLIENT MAPPING & DEDUPLICATION LOGIC
The same client name may exist on multiple platforms with different IDs. Example:
- Google Ads: Client "Ajay" (customer_id: 1234567890)
- Meta Ads: Client "Ajay" (account_id: act_123456789)
These must be recognized as the SAME client and merged intelligently.

Requirements:
- Implement fuzzy string matching (using fuzzywuzzy or similar) to suggest client merges across platforms
- Store platform-specific IDs (google_ads_customer_id, meta_ads_account_id) on the Client model
- Require explicit user confirmation before merging (prevent accidental duplicates)
- Create a mapping/linking workflow: "/api/clients/{client_id}/link-platforms" endpoint
- Ensure campaigns are deduplicated by (platform + platform_campaign_id) tuple, not just name
- Track sync metadata: last_google_sync, last_meta_sync timestamps

### 3. DATABASE SCHEMA UPDATES
Current models don't support multi-platform linking. Update:

**Client Model:**
- Add: google_ads_customer_id (String, nullable)
- Add: meta_ads_account_id (String, nullable)
- Add: linkedin_account_id (String, nullable) [for future]
- Add: last_google_sync (DateTime, nullable)
- Add: last_meta_sync (DateTime, nullable)

**Campaign Model:**
- Add: platform (String) — values: "google_ads", "meta_ads", "linkedin", "manual"
- Add: platform_campaign_id (String) — external platform ID
- Add: platform_account_id (String) — links back to platform-level account
- Add: is_auto_synced (Boolean, default=False)
- Add: synced_at (DateTime, nullable)
- Ensure unique constraint: (client_id, platform, platform_campaign_id)

**Create Migration:**
- Write a database migration (Alembic) to add these new columns to existing tables
- Provide a rollback plan

### 4. API ENDPOINTS FOR PLATFORM LINKING & SYNCING

Create these endpoints:

**POST /api/clients/{client_id}/link-platforms**
- Request: { google_account_id?: string, meta_account_id?: string }
- Response: { client_id, google_linked: bool, meta_linked: bool }
- Function: Store platform IDs on the Client record

**POST /api/clients/{client_id}/sync-platforms**
- Request: {} (no body)
- Response: { status: "synced", campaigns_added: int, aggregated: {...} }
- Function: Fetch latest campaigns from all linked platforms, merge them, save to DB
- Should call platform-specific fetcher functions

**GET /api/clients/{client_id}/platform-mapping-suggestions**
- Request: { platform_clients_a: [...], platform_clients_b: [...] }
- Response: [ { google_client, meta_client, confidence: 0-100, recommendation: "MERGE" | "REVIEW" } ]
- Function: Use fuzzy matching to suggest which clients from Google should merge with Meta clients
- Threshold: 85% similarity = "REVIEW", 90%+ = "MERGE"

**GET /api/clients/{client_id}/campaigns**
- Update existing endpoint to return campaigns with platform info
- Response: [ { id, name, platform, group_id, platform_campaign_id } ]

### 5. IMPLEMENTATION UTILITIES

**File: backend/mock_ads_api.py**
- Function: get_mock_google_ads_campaigns(account_id: str) -> dict
  - Returns list of campaign dicts with realistic data
- Function: get_mock_meta_ads_campaigns(account_id: str) -> dict
  - Returns list of campaign dicts with realistic data

**File: backend/platform_merger.py**
- Function: merge_platform_campaigns(client_name: str, campaigns_list: list) -> dict
  - Input: List of campaigns from multiple platforms
  - Output: {
      "client": "Ajay",
      "campaigns": [...],  # deduplicated list
      "aggregated": {
        "total_spend": ...,
        "total_leads": ...,
        "total_impressions": ...,
        "blended_cpl": ...,
        "sources": ["google_ads", "meta_ads"]
      }
    }
- Function: fuzzy_match_clients(platform_clients_a: list, platform_clients_b: list, threshold=85) -> list
  - Uses fuzzywuzzy.token_sort_ratio() for matching
  - Returns matches with confidence scores

**File: backend/platform_integrations.py**
- Function: fetch_google_ads_campaigns(customer_id: str) -> dict
  - When demo mode: call get_mock_google_ads_campaigns()
  - When real mode: call actual Google Ads API
  - Returns normalized campaign list
- Function: fetch_meta_ads_campaigns(account_id: str) -> dict
  - When demo mode: call get_mock_meta_ads_campaigns()
  - When real mode: call actual Meta Marketing API
  - Returns normalized campaign list

### 6. FRONTEND INTEGRATION (UI HINTS)

Show user a "Link Platforms" workflow:
- Step 1: "Enter your Google Ads Customer ID" (text input with help link)
- Step 2: "Enter your Meta Ads Account ID" (text input with help link)
- Step 3: "Review automatic client merges" (show fuzzy-match suggestions, allow user to confirm/override)
- Step 4: "Sync Campaigns" (button triggers POST /api/clients/{id}/sync-platforms)
- Step 5: Dashboard shows merged data with platform badges ("🔵 Google + 🔴 Meta")

### 7. TESTING STRATEGY

Provide:
- Unit tests for fuzzy_match_clients() with edge cases (case differences, typos, partial matches)
- Integration test for merge_platform_campaigns() with mock data
- End-to-end test: Upload mock Google data → Upload mock Meta data → Verify merged result
- Postman collection or curl examples for all new endpoints

### 8. DOCUMENTATION

Provide:
- README section: "How to test without real ad accounts" (explain demo mode)
- README section: "How to link your Google Ads and Meta Ads accounts" (with screenshots or flow diagram)
- Code comments explaining the platform_campaign_id deduplication logic
- Example request/response JSON for each new endpoint

## DELIVERABLES CHECKLIST

- [ ] Mock API layer (mock_ads_api.py) with realistic test data
- [ ] Fuzzy matching + merge logic (platform_merger.py)
- [ ] Platform fetchers (platform_integrations.py) supporting demo + real mode
- [ ] Database models updated with new columns
- [ ] Alembic migration to apply schema changes
- [ ] Five new API endpoints (link, sync, suggestions, updated campaigns, demo sync)
- [ ] Backend tests (unit + integration)
- [ ] Frontend UI flow for platform linking (or detailed specification)
- [ ] Documentation with examples

## CONSTRAINTS & NOTES

- Maintain backward compatibility: existing CSV uploads should still work
- Demo mode should be default behavior (no credentials required)
- Use environment variable `DEMO_MODE=true` to toggle between mock and real API calls
- Platform IDs must be treated as immutable once linked (prevent accidental remapping)
- All campaigns must have a unique (client_id, platform, platform_campaign_id) tuple
- Fuzzy matching threshold tunable; default 85%
- Handle edge cases: missing conversions data, zero spend, renamed campaigns on platforms

## NEXT STEPS AFTER COMPLETION

Once this is done, you'll be ready to:
1. Integrate real Google Ads API credentials (OAuth flow)
2. Integrate real Meta Marketing API credentials (OAuth flow)
3. Build automatic daily sync jobs (scheduled tasks)
4. Add platform-specific features (budget rules, audience insights, etc.)