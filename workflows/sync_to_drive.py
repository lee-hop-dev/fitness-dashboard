name: Sync to Google Drive

on:
  workflow_dispatch:        # Allows manual trigger from GitHub
  schedule:                # Optional: run on a schedule (here every day at midnight)
    - cron: "0 0 * * *"

jobs:
  sync:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Sync to Google Drive
        env:
          GOOGLE_SERVICE_ACCOUNT_JSON: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON }}
          GOOGLE_DRIVE_FOLDER_ID: ${{ secrets.GOOGLE_DRIVE_FOLDER_ID }}
        run: |
          python workflows/sync_to_drive.py --all
