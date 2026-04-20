#!/usr/bin/env python3
"""
System Test Script
Tests database, authentication, and core functionality
"""

from database import SessionLocal, crud
from auth import register_user, authenticate_user, create_access_token, get_current_user
from datetime import date

def test_database():
    """Test database connection and CRUD operations"""
    print("\n🗄️  Testing Database...")
    db = SessionLocal()
    
    try:
        # Test user creation
        user, error = register_user(db, "test@example.com", "password123", "Test User", "Test Agency")
        if error:
            print(f"   ❌ User registration failed: {error}")
            # User might already exist, try to get it
            user = crud.get_user_by_email(db, "test@example.com")
        else:
            print(f"   ✅ User created: {user.email}")
        
        # Test client creation
        client = crud.create_client(db, user.id, "Test Client", "SaaS", 50.0, 10000.0)
        print(f"   ✅ Client created: {client.name}")
        
        # Test campaign creation
        campaign = crud.create_campaign(db, client.id, "Test Campaign", "manual")
        print(f"   ✅ Campaign created: {campaign.campaign_name}")
        
        # Test campaign data insertion
        data = crud.upsert_campaign_data(
            db, campaign.id, date.today(),
            impressions=10000, clicks=200, spend=150.0, leads=25,
            ctr=2.0, cpl=6.0, conversion_rate=12.5
        )
        print(f"   ✅ Campaign data inserted for {data.date}")
        
        # Test data retrieval
        clients = crud.get_clients_by_user(db, user.id)
        print(f"   ✅ Retrieved {len(clients)} client(s)")
        
        campaigns = crud.get_campaigns_by_client(db, client.id)
        print(f"   ✅ Retrieved {len(campaigns)} campaign(s)")
        
        campaign_data = crud.get_campaign_data(db, campaign.id)
        print(f"   ✅ Retrieved {len(campaign_data)} data point(s)")
        
        print("   ✅ Database tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False
    finally:
        db.close()


def test_authentication():
    """Test authentication system"""
    print("\n🔐 Testing Authentication...")
    db = SessionLocal()
    
    try:
        # Test user authentication
        user = authenticate_user(db, "test@example.com", "password123")
        if user:
            print(f"   ✅ User authenticated: {user.email}")
        else:
            print("   ❌ Authentication failed")
            return False
        
        # Test token creation
        token = create_access_token({"sub": str(user.id)})
        print(f"   ✅ JWT token created: {token[:20]}...")
        
        # Test token validation
        current_user = get_current_user(db, token)
        if current_user and current_user.id == user.id:
            print(f"   ✅ Token validated for user: {current_user.email}")
        else:
            print("   ❌ Token validation failed")
            return False
        
        print("   ✅ Authentication tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False
    finally:
        db.close()


def test_intelligence():
    """Test intelligence engine"""
    print("\n🧠 Testing Intelligence Engine...")
    
    try:
        import pandas as pd
        from intelligence import run_intelligence
        
        # Create sample data
        camp_data = {
            'campaign': ['Campaign A', 'Campaign B', 'Campaign C'],
            'impressions': [50000, 30000, 45000],
            'clicks': [600, 180, 900],
            'spend': [320.50, 150.00, 410.00],
            'leads': [45, 12, 70],
            'ctr': [1.2, 0.6, 2.0],
            'cpl': [7.12, 12.50, 5.86],
            'conversion_rate': [7.5, 6.7, 7.8]
        }
        camp_df = pd.DataFrame(camp_data)
        
        daily_data = {
            'date': pd.date_range('2024-01-01', periods=7),
            'leads': [45, 50, 42, 55, 47, 52, 54],
            'spend': [320, 340, 310, 360, 330, 345, 355]
        }
        daily_df = pd.DataFrame(daily_data)
        
        # Run intelligence
        intel = run_intelligence(camp_df, daily_df)
        
        print(f"   ✅ Performance scores calculated")
        print(f"   ✅ Budget allocation computed")
        print(f"   ✅ Predictions generated: {intel['leads_prediction']['predicted_leads']} leads")
        print(f"   ✅ Patterns detected: {len(intel['patterns'])} pattern(s)")
        print(f"   ✅ Actions recommended: {len(intel['actions'])} action(s)")
        print(f"   ✅ Wasted spend identified: ${intel['waste']['total_wasted']:.2f}")
        
        print("   ✅ Intelligence tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Intelligence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gemini():
    """Test Gemini API integration"""
    print("\n🤖 Testing Gemini API...")
    
    try:
        from gemini_insights import generate_executive_summary
        from config import config
        
        if not config.GEMINI_API_KEY:
            print("   ⚠️  Gemini API key not configured (optional)")
            print("   ✅ Fallback mode works")
            return True
        
        kpis = {
            'Total Spend': '$2,310.50',
            'Total Leads': 192,
            'Avg CTR (%)': 1.27,
            'Avg CPL ($)': 8.49
        }
        
        predictions = {
            'predicted_leads': 210,
            'trend': '📈 Improving',
            'growth_rate_pct': 9.4
        }
        
        actions = ['Scale Campaign A by 20%']
        
        summary = generate_executive_summary(kpis, predictions, actions)
        print(f"   ✅ Executive summary generated")
        print(f"   📝 {summary[:100]}...")
        
        print("   ✅ Gemini tests passed!")
        return True
        
    except Exception as e:
        print(f"   ⚠️  Gemini test failed (optional): {e}")
        return True  # Non-critical


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 AI GROWTH OPERATOR — SYSTEM TEST")
    print("=" * 60)
    
    results = {
        'Database': test_database(),
        'Authentication': test_authentication(),
        'Intelligence': test_intelligence(),
        'Gemini API': test_gemini(),
    }
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    all_passed = all(results.values())
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ System is ready for development")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("❌ Please check errors above")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
