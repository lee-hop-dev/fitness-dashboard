# Fitness Dashboard

Automated fitness tracking dashboard pulling data from multiple sources (Intervals.icu, Concept2, Strava, Zwift) and displaying on GitHub Pages.

## Project Status

**Phase 1: Core Infrastructure** ✅ (In Progress)
- [x] Project structure
- [x] Configuration templates
- [x] Data schema
- [x] Intervals.icu connector
- [x] Concept2 connector
- [ ] Google Drive integration
- [ ] Data aggregation pipeline
- [ ] GitHub Actions workflow

**Phase 2: Enhanced Features** (Upcoming)
- [ ] Strava segments connector
- [ ] ZwiftRacing.app connector
- [ ] Dashboard pages (HTML/CSS/JS)

**Phase 3: Nice-to-Have** (Future)
- [ ] YouTube integration
- [ ] Race video gallery

## Architecture

```
Data Sources → Google Drive (Raw Storage) → GitHub Actions (Daily)
                                                ↓
                                           Process Data
                                                ↓
                                    GitHub Pages (Static Dashboard)
```

### Data Flow
1. **Daily sync** (6 AM UTC via GitHub Actions):
   - Pull new activities from Intervals.icu
   - Pull rowing workouts from Concept2
   - Fetch Strava segments (Phase 2)
   - Fetch Zwift race results (Phase 2)
   
2. **Data processing**:
   - Standardize to common schema
   - Aggregate metrics
   - Generate JSON for dashboard
   
3. **Deploy**:
   - Update static HTML/JS pages
   - Push to GitHub Pages

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- GitHub account
- Google Drive account
- API keys for:
  - Intervals.icu
  - Concept2 Logbook
  - Strava (Phase 2)
  - YouTube Data API (Phase 3)

### 2. Local Development Setup

```bash
# Clone repository
git clone https://github.com/lee-hop-dev/fitness-dashboard.git
cd fitness-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy config template
cp config/config.yaml.template config/config.yaml
cp .env.template .env

# Edit config files with your API keys
# config/config.yaml - main configuration
# .env - sensitive credentials
```

### 3. API Setup

#### Intervals.icu
1. Go to https://intervals.icu/settings
2. Find your API key under "Developer Settings"
3. Your athlete ID is in the URL: `intervals.icu/athletes/YOUR_ID`
4. Add to `.env`:
   ```
   INTERVALS_API_KEY=your_key_here
   ```

#### Concept2 Logbook
1. Use your existing Concept2 account credentials
2. Add to `.env`:
   ```
   CONCEPT2_USERNAME=LH_Hoppy
   CONCEPT2_PASSWORD=your_password_here
   ```

#### Google Drive (for data storage)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Google Drive API
4. Create credentials (OAuth 2.0 or Service Account)
5. Download `credentials.json` and save to `config/`
6. Create folder structure in Google Drive:
   ```
   /FitnessData/
     /raw/
     /processed/
     /cache/
   ```
7. Get folder ID from URL and add to `.env`:
   ```
   GOOGLE_DRIVE_FOLDER_ID=your_folder_id
   ```

### 4. Test Connectors

```bash
# Test Intervals.icu connection
python connectors/intervals_icu.py

# Test Concept2 connection
python connectors/concept2.py
```

### 5. GitHub Setup

#### Repository Secrets
Add these secrets in GitHub repo settings (Settings → Secrets and variables → Actions):

```
INTERVALS_API_KEY
CONCEPT2_USERNAME
CONCEPT2_PASSWORD
GOOGLE_DRIVE_FOLDER_ID
GOOGLE_CREDENTIALS_JSON (base64 encoded)
```

#### GitHub Pages
1. Go to repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: `gh-pages` (will be created by Actions)

### 6. Manual Data Collection (Testing)

```bash
# Run full data collection
python workflows/collect_data.py

# Sync to Google Drive
python workflows/sync_to_drive.py
```

## Project Structure

```
fitness-dashboard/
├── .github/
│   └── workflows/
│       └── daily-sync.yml      # GitHub Actions workflow
├── config/
│   ├── config.yaml.template    # Configuration template
│   ├── data_schema.json        # Standardized data schema
│   └── google_credentials.json # Google API credentials (gitignored)
├── connectors/
│   ├── intervals_icu.py        # Intervals.icu API
│   ├── concept2.py             # Concept2 Logbook API
│   ├── strava.py               # Strava API (Phase 2)
│   └── zwift_racing.py         # ZwiftRacing.app API (Phase 2)
├── workflows/
│   ├── collect_data.py         # Main data collection script
│   ├── sync_to_drive.py        # Google Drive sync
│   └── generate_pages.py       # HTML page generation
├── docs/
│   ├── index.html              # Overview dashboard
│   ├── cycling.html            # Cycling page
│   ├── running.html            # Running page
│   ├── rowing.html             # Rowing page
│   └── assets/                 # CSS, JS, images
├── data/                       # Local cache (gitignored)
├── requirements.txt            # Python dependencies
├── .env.template               # Environment variables template
├── .gitignore
└── README.md
```

## Configuration

### Activity Types
Configured in `config/config.yaml`:
- **Primary**: Ride, VirtualRide, Run, VirtualRun, Rowing
- **Secondary**: Walk, Swim, Workout, WeightTraining

### Wellness Metrics
- Sleep time and quality
- HRV (Heart Rate Variability)
- Resting heart rate
- Weight
- Fatigue, mood, soreness levels

### Display Settings
- Distance units: km or miles
- Date/time formats
- Chart colors per activity type
- Dashboard metric selection

## Dashboard Pages

### Overview
- Total activities, distance, time
- Weekly activity trends
- Current fitness (CTL) and form (TSB)
- Recent activities feed
- Wellness trends (HRV, sleep, weight)

### Cycling
- Combined outdoor + Zwift rides
- Activity trends and totals
- Strava segments and PRs
- Zwift race results
- Embedded race videos

### Running
- Activity trends
- Pace analysis
- Personal records

### Rowing
- Concept2-specific metrics
- Stroke rate, split times
- Rankings and goals

### Other
- Walking, swimming, general workouts

## Contributing

This is a personal project, but suggestions are welcome! Open an issue or PR.

## License

MIT License - See LICENSE file

## Troubleshooting

### Common Issues

**"Authentication failed" for Intervals.icu**
- Verify API key is correct
- Check athlete ID matches your profile

**"Rate limit exceeded"**
- Connectors have built-in rate limiting
- For manual runs, add delays between calls

**Google Drive upload fails**
- Verify credentials.json is valid
- Check folder permissions
- Ensure folder ID is correct

**GitHub Actions workflow fails**
- Check all repository secrets are set
- Verify secret names match workflow file
- Review Actions logs for specific errors

## Roadmap

- [x] Phase 1: Core infrastructure (Intervals + Concept2)
- [ ] Phase 2: Strava segments + Zwift racing
- [ ] Phase 3: YouTube integration
- [ ] Mobile-responsive design
- [ ] Dark mode
- [ ] Activity comparison tools
- [ ] Goal tracking
- [ ] Training plan integration

## Contact

Questions? Open an issue on GitHub.

---

**Current User**: Athlete ID 5718022  
**Last Updated**: 2025-02-11
