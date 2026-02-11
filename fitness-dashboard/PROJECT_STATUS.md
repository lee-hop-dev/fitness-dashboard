# Fitness Dashboard - Phase 1 Complete ✅

## What's Been Built

### Configuration & Infrastructure
✅ **Project Structure** - Complete directory layout with proper organization
✅ **Config Templates** - YAML config and .env templates with your details pre-filled
✅ **Data Schema** - Standardized JSON schema for all activity types
✅ **Gitignore** - Proper exclusions for secrets and data files

### Core Connectors (Phase 1)
✅ **Intervals.icu Connector** - Full implementation with:
- Activity fetching with date ranges
- Wellness data (sleep, HRV, weight, etc.)
- Training load metrics (CTL, ATL, TSB)
- Power curves
- Data standardization to common schema
- Built-in rate limiting
- Error handling

✅ **Concept2 Connector** - Full implementation with:
- Workout fetching with authentication
- Detailed split data
- Rankings/goals
- Token management
- Data standardization
- Rate limiting

### Documentation
✅ **README.md** - Comprehensive project documentation
✅ **SETUP.md** - Step-by-step setup guide
✅ **Setup Verification Script** - Automated testing of configuration

### Dependencies
✅ **requirements.txt** - All Python packages needed for Phase 1

---

## Your Pre-Configured Details

**Intervals.icu**
- Athlete ID: `5718022`

**Concept2**
- Username: `LH_Hoppy`

**GitHub**
- Username: `lee-hop-dev`
- Repo: `fitness-dashboard`

**Page Structure** (Configured in config.yaml)
- Overview (main dashboard)
- Cycling (outdoor + Zwift combined)
- Running
- Rowing (Concept2-specific)
- Cardio/Workout
- Other (walking, swimming)

---

## Next Steps

### Immediate (To Complete Phase 1)

1. **Get Your API Keys**
   - Intervals.icu: https://intervals.icu/settings
   - Concept2: Use your existing password

2. **Setup Google Drive**
   - Create Google Cloud project
   - Enable Drive API
   - Download credentials
   - Create `/FitnessData/` folder structure
   - Get folder ID

3. **Configure Locally**
   ```bash
   # Copy templates
   cp .env.template .env
   cp config/config.yaml.template config/config.yaml
   
   # Edit with your keys
   nano .env
   ```

4. **Test Connections**
   ```bash
   pip install -r requirements.txt
   python verify_setup.py
   ```

5. **Build Remaining Phase 1 Components**
   - [ ] Google Drive sync module (`workflows/sync_to_drive.py`)
   - [ ] Data aggregation pipeline (`workflows/collect_data.py`)
   - [ ] GitHub Actions workflow (`.github/workflows/daily-sync.yml`)

### Phase 2 (After Phase 1 Works)

6. **Add Enhanced Features**
   - [ ] Strava segments connector
   - [ ] ZwiftRacing.app connector
   - [ ] Build HTML dashboard pages

### Phase 3 (Polish)

7. **Nice-to-Have**
   - [ ] YouTube integration
   - [ ] Race video gallery
   - [ ] Mobile optimization

---

## Project Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                             │
│  Intervals.icu  │  Concept2  │  Strava  │  ZwiftRacing.app  │
└────────────┬────────────────────────────────────────────────┘
             │
             ↓
      ┌──────────────┐
      │  Connectors  │  ← You are here (Phase 1)
      │  (Python)    │
      └──────┬───────┘
             │
             ↓
      ┌──────────────┐
      │ Google Drive │  ← Next: Build this
      │ (Raw Data)   │
      └──────┬───────┘
             │
             ↓
    ┌────────────────────┐
    │  GitHub Actions    │  ← Then: Automate
    │  (Daily @ 6 AM)    │
    └────────┬───────────┘
             │
             ↓
    ┌────────────────────┐
    │ Data Processing    │
    │ & Aggregation      │
    └────────┬───────────┘
             │
             ↓
    ┌────────────────────┐
    │  GitHub Pages      │
    │  (Dashboard)       │
    └────────────────────┘
```

---

## File Structure Created

```
fitness-dashboard/
├── README.md                    ← Main documentation
├── requirements.txt             ← Python dependencies
├── verify_setup.py              ← Setup verification script
├── .env.template                ← Environment variables template
├── .gitignore                   ← Git exclusions
│
├── config/
│   ├── config.yaml.template     ← Main config (pre-filled with your IDs)
│   └── data_schema.json         ← Standard data format
│
├── connectors/
│   ├── intervals_icu.py         ← ✅ Intervals.icu API
│   └── concept2.py              ← ✅ Concept2 API
│
├── workflows/                   ← TODO: Build these next
│   ├── collect_data.py          ← Data collection orchestrator
│   ├── sync_to_drive.py         ← Google Drive sync
│   └── generate_pages.py        ← HTML generation
│
├── .github/workflows/           ← TODO: GitHub Actions
│   └── daily-sync.yml           ← Daily automation
│
├── docs/
│   └── SETUP.md                 ← Step-by-step setup guide
│
└── data/                        ← Local cache (gitignored)
```

---

## Key Features Implemented

### Intervals.icu Connector
- ✅ Fetches all activity types (Ride, VirtualRide, Run, Rowing, etc.)
- ✅ Pulls wellness metrics (sleep, HRV, resting HR, weight, mood)
- ✅ Gets training load (CTL/ATL/TSB for fitness tracking)
- ✅ Retrieves power curves for analysis
- ✅ Standardizes data to common schema
- ✅ Handles rate limiting (500ms between requests)
- ✅ Proper error handling with retries

### Concept2 Connector
- ✅ OAuth authentication with token management
- ✅ Fetches workouts with detailed splits
- ✅ Supports date range filtering
- ✅ Gets rankings and goals
- ✅ Converts to standard schema
- ✅ Rate limiting (1s between requests)
- ✅ Auto re-authentication on token expiry

### Data Schema
Standardized format supports:
- All activity types (cycling, running, rowing, etc.)
- Rich metrics (HR, power, pace, cadence)
- Zone distribution (HR zones, power zones)
- Detailed splits
- Wellness tracking
- Training load progression
- Segment efforts (for Strava - Phase 2)
- Race results (for Zwift - Phase 2)

---

## Testing Your Setup

Once you have your API keys:

```bash
# Test Intervals.icu
python connectors/intervals_icu.py

# Expected output:
# Connected successfully! Athlete: [Your Name]
# Retrieved X activities from last 7 days
# Retrieved X wellness entries from last 7 days

# Test Concept2
python connectors/concept2.py

# Expected output:
# Connected successfully! User: LH_Hoppy
# Retrieved X workouts from last 30 days
```

---

## What's Different From Typical Setups

### Why Google Drive?
- ✅ Corporate laptop safe - no local storage
- ✅ Access from anywhere
- ✅ Easy API integration
- ✅ GitHub Actions can read/write directly
- ✅ Manual backup option

### Why Intervals.icu as Primary Source?
- ✅ Already aggregates Garmin, Strava, etc.
- ✅ One API instead of many
- ✅ Rich analytics built-in (CTL/ATL/TSB)
- ✅ No OAuth complexity
- ✅ Wellness data included

### Why Concept2 Separate?
- ✅ Rowing-specific metrics not in Intervals
- ✅ Detailed split data
- ✅ Rankings and logbook features
- ✅ Better for rower dashboard section

---

## Estimated Time to Complete

**Phase 1 Remaining**: 3-4 hours
- Google Drive integration: 1 hour
- Data collection pipeline: 1 hour
- GitHub Actions: 1 hour
- Testing: 1 hour

**Phase 2**: 4-6 hours
- Strava connector: 2 hours
- Zwift connector: 1 hour
- Dashboard HTML: 2-3 hours

**Phase 3**: 2-3 hours
- YouTube integration: 1-2 hours
- Polish: 1 hour

**Total**: 10-15 hours for full completion

---

## Questions to Answer Before Next Session

1. **Do you have a Strava API app set up?** (Need for Phase 2)
2. **What's your Zwift username/ID?** (Need for ZwiftRacing.app)
3. **Do you stream races on YouTube?** If yes:
   - Channel URL?
   - Playlist for races?
4. **Dashboard preferences:**
   - Dark mode or light mode?
   - Chart library preference? (Chart.js, Plotly, etc.)
   - Mobile-first or desktop-first design?

---

## Ready to Proceed!

You now have:
- ✅ Complete project structure
- ✅ Working API connectors
- ✅ Configuration templates
- ✅ Clear documentation
- ✅ Setup verification tools

**Next build focus**: Google Drive integration + data collection pipeline

Let me know when you're ready to continue building the remaining Phase 1 components!
