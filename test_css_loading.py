#!/usr/bin/env python3
"""
Test script to verify enterprise_ui.css is loading correctly
"""

import os

# Test 1: Check if CSS file exists
CSS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enterprise_ui.css")
print("=" * 70)
print("CSS LOADING TEST")
print("=" * 70)
print(f"\n1. CSS File Path: {CSS_FILE}")
print(f"   File exists: {'✓ YES' if os.path.exists(CSS_FILE) else '✗ NO'}")

if os.path.exists(CSS_FILE):
    # Test 2: Check file size
    file_size = os.path.getsize(CSS_FILE)
    print(f"\n2. File Size: {file_size:,} bytes")
    print(f"   Size OK: {'✓ YES' if file_size > 10000 else '✗ NO (too small)'}")
    
    # Test 3: Check content
    with open(CSS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n3. Content Length: {len(content):,} characters")
    
    # Test 4: Check for key CSS rules
    checks = [
        ("Color variables", "--gray-50" in content),
        ("Typography", "--font-sans" in content),
        ("KPI cards", ".kpi-card" in content),
        ("Buttons", "button {" in content or "button{" in content),
        ("Tables", ".alloc-table" in content),
        ("Visual indicator", "Enterprise UI Loaded" in content),
    ]
    
    print("\n4. CSS Content Checks:")
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    # Test 5: Check first few lines
    print("\n5. First 300 characters:")
    print("   " + content[:300].replace("\n", "\n   "))
    
    # Final result
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - CSS should load correctly")
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. Open: http://localhost:7860")
        print("3. Look for '✓ Enterprise UI Loaded' badge in bottom-right corner")
        print("4. If you don't see it, try:")
        print("   - Hard refresh browser (Cmd+Shift+R on Mac)")
        print("   - Clear browser cache")
        print("   - Try incognito/private window")
    else:
        print("✗ SOME TESTS FAILED - Check errors above")
    print("=" * 70)
else:
    print("\n✗ ERROR: CSS file not found!")
    print("   Make sure enterprise_ui.css is in the same directory as app.py")
