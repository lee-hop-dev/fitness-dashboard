# Quick Start Guide

Get your fitness dashboard up and running in 15 minutes.

## 🚀 Fast Track Setup

### 1. Initial Setup (5 minutes)

```bash
# Clone and install
git clone <your-repo>
cd fitness-dashboard
pip install -r requirements.txt
```

### 2. Get API Keys (5 minutes)

**Intervals.icu:**
- Login → Settings → Developer → Generate API Key
- Copy your Athlete ID from URL: `intervals.icu/athletes/YOUR_ID`

**Concept2:**
- Just your login credentials from log.concept2.com

**Google Drive:**
- See `docs/GOOGLE_DRIVE_SETUP.md` (takes 5 min)
- Download credentials.json to `config/`

### 3. Configure (2 minutes)

```bash
# Create config from template
cp config/config.yaml.template config/config.yaml

# Edit with your API keys
nano config/config.yaml  # or use your favorite editor
```

Fill in these sections:
```yaml
intervals_icu:
  api_key: "your_api_key_here"
  athlete_id: "i123456"

concept2:
  username: "your_username"
  password: "your_password"

google_drive:
  credentials_file: "config/credentials.json"
  raw_folder: "Github/Fitness/Raw"
  processed_folder: "Github/Fitness/Processed"
```

### 4. Test Everything (2 minutes)

```bash
# Run comprehensive tests
python scripts/test_setup.py
```

You should see all green checkmarks ✓

### 5. First Sync (1 minute)

```bash
# Sync last 7 days
python scripts/sync_data.py --days 7

# Or do full historical sync
python scripts/sync_data.py --full-sync
```

Check your Google Drive → `Github/Fitness/Raw/` for JSON files!

## 🔄 Enable Daily Automation

### Push to GitHub and Setup Secrets

```bash
# Push your code (credentials.json is gitignored)
git add .
git commit -m "Initial setup"
git push origin main
```

### Add GitHub Secrets

Go to: Settings → Secrets and variables → Actions

Add these secrets (from your config.yaml):
- `INTERVALS_API_KEY`
- `INTERVALS_ATHLETE_ID`
- `CONCEPT2_USERNAME`
- `CONCEPT2_PASSWORD`
- `GOOGLE_DRIVE_CREDENTIALS` (entire JSON from credentials.json)

### Enable Actions

1. Go to Actions tab
2. Enable workflows
3. Done! Syncs daily at 6 AM UTC

## 📊 What You Get

After first sync, check Google Drive:

```
Github/Fitness/Raw/
├── activities_2024-02-04_to_2024-02-11.json  # All workouts
├── wellness_2024-02-04_to_2024-02-11.json    # Sleep, HRV, etc.
└── fitness_2024-02-04_to_2024-02-11.json     # CTL, ATL, TSB trends
```

Each file contains:
- ✅ Standardized data format
- ✅ All activities from multiple sources
- ✅ No duplicates
- ✅ Timestamped and organized

## 🎯 Next Steps

### Phase 2: Add More Data Sources
- [ ] Strava segments (coming soon)
- [ ] Zwift race results (coming soon)

### Phase 3: Build Dashboard
- [ ] Overview page with charts
- [ ] Sport-specific pages
- [ ] YouTube race videos

### Manual Operations

```bash
# Sync specific date range
python scripts/sync_data.py --days 30

# Full historical sync
python scripts/sync_data.py --full-sync

# Test configuration
python scripts/test_setup.py

# Test individual connectors
python connectors/intervals_icu.py
python connectors/concept2.py
python connectors/google_drive.py
```

## ❓ Troubleshooting

### "Config file not found"
→ Copy `config.yaml.template` to `config.yaml`

### "Credentials file not found"
→ See `docs/GOOGLE_DRIVE_SETUP.md`

### "Authentication failed"
→ Check API keys in config.yaml
→ Verify they're not expired
→ Test individual connectors

### "Permission denied" (Google Drive)
→ Share Drive folder with service account email
→ Use "Editor" permission

### GitHub Actions failing
→ Check all secrets are set correctly
→ Verify JSON format in GOOGLE_DRIVE_CREDENTIALS
→ Check Actions logs for specific error

## 📚 Full Documentation

- `README.md` - Complete project documentation
- `docs/GOOGLE_DRIVE_SETUP.md` - Detailed Drive setup
- `docs/SETUP_CHECKLIST.md` - Step-by-step checklist

## 🎉 Success!

When everything works, you'll have:

✅ Automated daily data sync
✅ All fitness data in one place
✅ Standardized format for analysis
✅ Secure cloud storage
✅ No manual work required

Your fitness data is now on autopilot! 🚀

---

**Need help?** Open an issue on GitHub or check the docs folder.
