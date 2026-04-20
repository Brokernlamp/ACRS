# Week 2 Day 2 - Action Plan

**Date:** January 2025  
**Focus:** Historical Comparison + Client Dashboard  
**Status:** In Progress

---

## Today's Goals

### 1. Historical Comparison UI (Priority 1)
**Time:** 2-3 hours  
**Status:** Starting now

**Tasks:**
- [ ] Add date range selector to UI
- [ ] Load data from database by date range
- [ ] Calculate week-over-week changes
- [ ] Calculate month-over-month changes
- [ ] Add comparison toggle
- [ ] Show trend arrows (↑↓) in KPI cards
- [ ] Display % change indicators

### 2. Client Dashboard (Priority 2)
**Time:** 2-3 hours  
**Status:** After historical comparison

**Tasks:**
- [ ] Create "Clients" tab in UI
- [ ] Show list of all clients
- [ ] Display quick stats per client
- [ ] Add client creation form
- [ ] Add client edit functionality
- [ ] Show last data upload date
- [ ] Add client filtering/search

### 3. Load Data from Database (Priority 3)
**Time:** 1-2 hours  
**Status:** After client dashboard

**Tasks:**
- [ ] Query database for selected client
- [ ] Load campaign data by date range
- [ ] Replace in-memory _state with DB queries
- [ ] Add data caching for performance
- [ ] Handle empty data gracefully

---

## Implementation Order

### Step 1: Historical Comparison (Starting Now)
```python
# Add to app.py
1. Date range selector UI components
2. Database query function with date filtering
3. Comparison calculation function
4. Update KPI cards with trends
5. Add comparison toggle
```

### Step 2: Client Dashboard
```python
# Add to app.py
1. New "Clients" tab
2. Client list display
3. Client stats aggregation
4. Add/Edit forms
5. Client selection integration
```

### Step 3: Database Loading
```python
# Refactor app.py
1. Load data from DB instead of CSV only
2. Cache loaded data in session
3. Refresh on client switch
4. Handle date range changes
```

---

## Files to Modify

1. **app.py** - Main changes
   - Add date range components
   - Add Clients tab
   - Add DB loading functions
   - Update process_upload to use dates

2. **database/crud.py** - Already has functions
   - `get_campaign_data(db, campaign_id, start_date, end_date)`
   - `get_client_data_summary(db, client_id, start_date, end_date)`
   - No changes needed!

3. **data_processor.py** - Add comparison functions
   - `calculate_period_comparison(current_data, previous_data)`
   - `get_trend_direction(current, previous)`
   - `format_change_percentage(change)`

---

## Quick Wins While You Gather APIs

Since you're gathering APIs, I'll implement features that work independently:

### ✅ Can Do Now (No API needed)
1. Historical comparison with existing data
2. Client dashboard with database
3. Date range filtering
4. Week/month comparisons
5. Trend indicators
6. Client management UI

### ⏳ Need APIs Later (Week 3-4)
1. Google Ads integration
2. Meta Ads integration
3. Real-time data sync
4. Automated data refresh

---

## Starting Implementation

I'll begin with:
1. **Historical Comparison** - Most requested feature
2. **Date Range Selector** - Foundation for comparisons
3. **Trend Indicators** - Visual improvements

Let's go! 🚀
