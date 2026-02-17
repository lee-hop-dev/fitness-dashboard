# 🚀 Ready to Test! - Next Steps Guide

## ✅ What's Now Complete

You have:
- ✅ Intervals.icu connector (working!)
- ✅ Concept2 connector (optional - can skip)
- ✅ Google Drive credentials in place
- ✅ Configuration files set up
- ✅ Data collection pipeline
- ✅ Google Drive sync
- ✅ GitHub Actions workflow

## 🎯 Test Locally First

### Step 1: Install Google API packages

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib google-auth
```

### Step 2: Run the complete pipeline

```bash
python run_pipeline.py
```

**What will happen:**
1. Opens browser for Google Drive authorization (first time only)
2. Collects last 7 days of data from Intervals.icu
3. Processes and aggregates data
4. Uploads to Google Drive
5. Shows summary statistics

**Expected output:**
```
================================================================
FITNESS DASHBOARD - LOCAL TEST RUN
================================================================

STEP 1: Collecting data from APIs...
----------------------------------------------------------------------
Retrieved X activities
Retrieved X wellness entries
Retrieved X fitness data points

STEP 2: Syncing to Google Drive...
----------------------------------------------------------------------
✅ Uploaded X raw data files
✅ Uploaded X processed data files

================================================================
SUCCESS! Pipeline completed
================================================================

Summary:
  📊 Total activities: X
  📏 Total distance: X km
  ⏱️  Total duration: X hours
```

### Step 3: Verify in Google Drive

Check your Google Drive folder:
```
FitnessData/
├── raw/
│   └── intervals_icu_2025-02-11.json
└── processed/
    └── aggregated_2025-02-11.json
```

### If First-Time Google Auth Fails:

If you see authentication errors:

1. **Check credentials file:**
   ```bash
   dir config\google_credentials.json
   ```

2. **Delete old token if exists:**
   ```bash
   del config\token.json
   ```

3. **Run again:**
   ```bash
   python run_pipeline.py
   ```

4. **Browser will open** - Click "Allow" for Google Drive access

---

## 📤 Push to GitHub

Once local testing works:

### Step 1: Initialize git (if not done)

```bash
git init
git add .
git commit -m "Initial commit - Phase 1 complete"
```

### Step 2: Create GitHub repository

1. Go to https://github.com/new
2. Repository name: `fitness-dashboard`
3. **Private** (recommended - contains API keys in Actions)
4. Don't initialize with README (you already have one)

### Step 3: Push to GitHub

```bash
git remote add origin https://github.com/lee-hop-dev/fitness-dashboard.git
git branch -M main
git push -u origin main
```

---

## 🔐 Setup GitHub Secrets

**CRITICAL:** Add these secrets before running Actions

Go to: Repository Settings → Secrets and variables → Actions → New repository secret

### Required Secrets:

1. **INTERVALS_API_KEY**
   - Value: Your Intervals.icu API key

2. **CONCEPT2_USERNAME**
   - Value: `LH_Hoppy`

3. **CONCEPT2_PASSWORD**
   - Value: Your Concept2 password

4. **GOOGLE_DRIVE_FOLDER_ID**
   - Value: `1VgiX477IQmVqq7-X5JRyC3OTxDmFWPEW`

5. **GOOGLE_CREDENTIALS_JSON** (Most important!)
   - Encode the file as base64:
   
   **Windows:**
   ```powershell
   certutil -encode config\google_credentials.json temp.txt
   ```
   Then open `temp.txt`, copy everything EXCEPT the first and last lines
   
   **Or use Python:**
   ```bash
   python -c "import base64; print(base64.b64encode(open('config/google_credentials.json', 'rb').read()).decode())"
   ```
   
   Copy the output and paste as the secret value

---

## ⚙️ Test GitHub Actions

### Step 1: Enable Actions

Go to: Repository → Actions tab → Enable Actions

### Step 2: Manual test run

1. Click on "Daily Data Sync" workflow
2. Click "Run workflow"
3. Leave defaults (7 days)
4. Click "Run workflow"

### Step 3: Monitor

Watch the workflow run:
- Should complete in 2-3 minutes
- Check logs for any errors
- Verify files appear in Google Drive

### If GitHub Actions Fails:

**Common issues:**

1. **Secrets not set:**
   - Double-check all 5 secrets are added
   - Names must match exactly (case-sensitive)

2. **Google credentials error:**
   - Verify base64 encoding is correct
   - No extra spaces or newlines

3. **Rate limiting:**
   - Wait a few minutes and try again

---

## 📊 What's in the Data Files?

### aggregated_YYYY-MM-DD.json structure:

```json
{
  "last_updated": "2025-02-11T10:30:00",
  "date_range": {
    "start": "2025-02-04",
    "end": "2025-02-11"
  },
  "activities": [
    {
      "id": "123",
      "type": "Ride",
      "start_time": "2025-02-11T08:00:00",
      "duration": 3600,
      "distance": 25000,
      "metrics": {
        "avg_power": 200,
        "avg_heart_rate": 145
      }
    }
  ],
  "wellness": [...],
  "training_load": [...],
  "summary": {
    "total_activities": 5,
    "total_distance_km": 125.5,
    "total_duration_hours": 6.5,
    "by_activity_type": {...},
    "latest_wellness": {...},
    "latest_fitness": {
      "ctl": 45.2,
      "atl": 38.5,
      "tsb": 6.7
    }
  }
}
```

---

## 🎨 Next: Build Dashboard (Phase 2)

Once data collection works:

1. **Create HTML pages** (Overview, Cycling, Running, etc.)
2. **Add Chart.js** for visualizations
3. **Deploy to GitHub Pages**
4. **Add Strava segments connector**
5. **Add ZwiftRacing.app connector**

---

## 📝 Useful Commands

### Collect last 7 days (default)
```bash
python workflows/collect_data.py
```

### Collect full history (365 days)
```bash
python workflows/collect_data.py --full
```

### Collect custom range
```bash
python workflows/collect_data.py --days 30
```

### Sync to Google Drive only
```bash
python workflows/sync_to_drive.py --all
```

### Run full pipeline
```bash
python run_pipeline.py
```

### Verify setup
```bash
python verify_setup.py
```

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Google auth browser won't open
```bash
# Delete token and try again
del config\token.json
python run_pipeline.py
```

### Intervals.icu rate limiting
Wait 60 seconds, the connector handles it automatically

### Data files not in Google Drive
Check `data/processed/` folder exists locally first

---

## ✅ Success Checklist

- [ ] `python run_pipeline.py` completes successfully
- [ ] Files appear in Google Drive (FitnessData/processed/)
- [ ] Code pushed to GitHub
- [ ] All 5 secrets added to GitHub
- [ ] GitHub Actions workflow runs successfully
- [ ] Data appears in Google Drive from Actions run

Once all checked, you're ready for Phase 2! 🎉

---

## 📞 Need Help?

Common issues and solutions:

1. **Google auth fails locally:**
   - Make sure you're logged into Google in your browser
   - Check credentials.json is valid
   - Try incognito window

2. **GitHub Actions fails authentication:**
   - Re-check base64 encoding of google_credentials.json
   - Verify all secret names exactly match

3. **No data collected:**
   - Verify API key in .env
   - Check Intervals.icu has activities in date range
   - Review logs for specific errors

4. **Files not syncing:**
   - Verify GOOGLE_DRIVE_FOLDER_ID is correct
   - Check folder permissions in Google Drive
   - Ensure subfolders (raw/processed/cache) exist
