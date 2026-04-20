# CSS Not Showing? Troubleshooting Guide

## Quick Fix (Most Common Issue)

**The CSS is loading, but your browser is caching the old version.**

### Solution:

1. **Hard Refresh** (clears cache for current page):
   - **Mac:** `Cmd + Shift + R`
   - **Windows/Linux:** `Ctrl + Shift + R`

2. **Or use Incognito/Private Window:**
   - **Mac:** `Cmd + Shift + N` (Chrome) or `Cmd + Shift + P` (Firefox)
   - **Windows:** `Ctrl + Shift + N` (Chrome) or `Ctrl + Shift + P` (Firefox)

3. **Or clear browser cache completely:**
   - Chrome: Settings → Privacy → Clear browsing data → Cached images and files
   - Firefox: Settings → Privacy → Clear Data → Cached Web Content

---

## Visual Indicator

When the CSS loads correctly, you'll see:

```
✓ Enterprise UI Loaded
```

**Location:** Bottom-right corner of the page (green badge)

**If you see this badge:** CSS is loaded! The styling should be applied.

**If you don't see this badge:** CSS is not loading. Follow steps below.

---

## Step-by-Step Debugging

### Step 1: Verify CSS File Exists

```bash
cd /Users/swarjadhav/Projects/ACRS
ls -la enterprise_ui.css
```

**Expected:** File should exist and be ~21KB

### Step 2: Run Test Script

```bash
python3 test_css_loading.py
```

**Expected:** All tests should pass (✓)

### Step 3: Check Console Output

When you run `python app.py`, you should see:

```
[DEBUG] Looking for CSS at: /Users/swarjadhav/Projects/ACRS/enterprise_ui.css
[DEBUG] CSS file exists: True
[DEBUG] CSS loaded successfully: 18006 characters
```

**If you don't see this:** The CSS isn't being loaded by Python.

### Step 4: Check Browser Console

1. Open browser (http://localhost:7860)
2. Open Developer Tools:
   - **Mac:** `Cmd + Option + I`
   - **Windows:** `F12`
3. Go to "Console" tab
4. Look for any CSS errors

### Step 5: Inspect Element

1. Right-click on any element (like the header)
2. Select "Inspect" or "Inspect Element"
3. Look at the "Styles" panel
4. Check if CSS variables are defined:
   - Look for `--gray-50`, `--blue-500`, etc.
   - If you see them: CSS is loaded
   - If you don't: CSS is not applied

---

## Common Issues & Solutions

### Issue 1: "I restarted the backend but nothing changed"

**Cause:** Browser cache

**Solution:**
```bash
# 1. Stop the backend (Ctrl+C)
# 2. Clear browser cache (Cmd+Shift+R)
# 3. Restart backend
python app.py
# 4. Reload page in browser (Cmd+R)
```

### Issue 2: "I see the green badge but UI looks the same"

**Cause:** Gradio's default styles are overriding custom CSS

**Solution:** Add `!important` to critical styles (already done in enterprise_ui.css)

**Check:** Look at the header. It should be:
- White background (not black)
- No emoji in title (just "AI Growth Operator")
- Clean, minimal design

### Issue 3: "Console shows CSS loaded but styles not applied"

**Cause:** CSS specificity issue

**Solution:** Check browser DevTools:
1. Inspect an element
2. Look at "Computed" styles
3. See which CSS rules are being applied
4. If Gradio's styles are winning, we need higher specificity

### Issue 4: "Python says CSS file not found"

**Cause:** File path issue

**Solution:**
```bash
# Check current directory
pwd

# Should be: /Users/swarjadhav/Projects/ACRS

# Check if CSS is there
ls enterprise_ui.css

# If not found, you're in wrong directory
cd /Users/swarjadhav/Projects/ACRS
```

---

## What Should Change (Visual Checklist)

When CSS loads correctly, you should see:

### ✓ Header
- [ ] White background (not black)
- [ ] No rocket emoji (🚀)
- [ ] Clean typography
- [ ] Small blue dot before title

### ✓ KPI Cards
- [ ] White background (not colored)
- [ ] Uppercase labels (TOTAL SPEND)
- [ ] Compact height (~88px)
- [ ] Gray borders (subtle)

### ✓ Buttons
- [ ] Blue primary buttons
- [ ] 40px height
- [ ] Subtle rounded corners (6px)
- [ ] No emoji in button text (optional)

### ✓ Tables
- [ ] Horizontal borders only (no vertical)
- [ ] Gray header background
- [ ] Hover effect on rows
- [ ] Right-aligned numbers

### ✓ Overall
- [ ] Gray background (#F9FAFB)
- [ ] System fonts (not default)
- [ ] Professional, clean look
- [ ] Green badge in bottom-right corner

---

## Still Not Working?

### Nuclear Option: Force Reload Everything

```bash
# 1. Stop backend
# Ctrl+C

# 2. Clear Python cache
rm -rf __pycache__
find . -name "*.pyc" -delete

# 3. Restart backend
python app.py

# 4. Open in INCOGNITO window
# Cmd+Shift+N (Chrome) or Cmd+Shift+P (Firefox)

# 5. Navigate to http://localhost:7860
```

### Check Gradio Version

```bash
pip show gradio
```

**Required:** Gradio 3.x or 4.x

**If older:** Update with `pip install --upgrade gradio`

---

## Contact for Help

If none of the above works, provide:

1. **Console output** when running `python app.py`
2. **Browser console errors** (F12 → Console tab)
3. **Screenshot** of current UI
4. **Gradio version** (`pip show gradio`)
5. **Browser & version** (Chrome 120, Firefox 121, etc.)

---

## Quick Test: Is CSS Working?

Run this in your browser console (F12 → Console):

```javascript
// Check if CSS variables are defined
getComputedStyle(document.documentElement).getPropertyValue('--gray-50')
```

**Expected output:** `#F9FAFB` or `rgb(249, 250, 251)`

**If empty:** CSS is not loaded

---

## Success Indicators

You'll know it's working when:

1. ✓ Green badge appears (bottom-right)
2. ✓ Header is white (not black)
3. ✓ Background is light gray (#F9FAFB)
4. ✓ Typography looks clean and professional
5. ✓ Overall UI looks like Stripe Dashboard

**If you see all 5:** Success! CSS is working.

---

**Last Resort:** Share a screenshot and I'll help debug further.
