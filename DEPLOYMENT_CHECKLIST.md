# Pre-Deployment Checklist

Complete this checklist before deploying to Streamlit Community Cloud.

## Credential Verification

### Google Cloud Setup
- [ ] Google service account created in Google Cloud Console
- [ ] Google Sheets API enabled
- [ ] Google Drive API enabled
- [ ] Service account JSON key downloaded locally
- [ ] Target Google Sheet **shared** with service account email
- [ ] Sheet ID copied (`GOOGLE_SHEET_ID`)
- [ ] Worksheet name confirmed (`GOOGLE_WORKSHEET_NAME`)

### Telegram Setup
- [ ] Telegram API credentials obtained from https://my.telegram.org/auth
- [ ] `TELEGRAM_API_ID` copied
- [ ] `TELEGRAM_API_HASH` copied
- [ ] Phone number recorded (`TELEGRAM_PHONE_NUMBER`)
- [ ] (Optional) Session string generated for persistent access

## Code Cleanup

### Sensitive Files Check
- [ ] `khemra_account.json` exists ONLY locally (not in git)
- [ ] `tg_sessions/` folder exists ONLY locally (not in git)
- [ ] `.streamlit/secrets.toml` exists ONLY locally (not in git)
- [ ] `.gitignore` includes all sensitive files
- [ ] Run `git status` and verify no sensitive files are staged

### Code Review
- [ ] `Script.ipynb` cleared of outputs (if sharing)
- [ ] `Script.ipynb` has no hardcoded credentials (if sharing)
- [ ] `app.py` loads secrets via `st.secrets` or env vars
- [ ] `scraper_backend.py` uses `get_deployment_setting()` for all credentials
- [ ] No API keys/tokens hardcoded in any `.py` files
- [ ] `requirements.txt` updated with all dependencies
- [ ] All test/debug code removed

## GitHub Setup

- [ ] Repository created (private recommended)
- [ ] Code pushed to main branch
- [ ] .gitignore is working (verified with `git status`)
- [ ] No sensitive files appear in GitHub web interface

## Streamlit Cloud Readiness

- [ ] Have your secrets values ready:
  - [ ] `GOOGLE_SHEET_ID`
  - [ ] `GOOGLE_WORKSHEET_NAME`
  - [ ] Complete `gcp_service_account` JSON (from service account key file)
  - [ ] `TELEGRAM_API_ID`
  - [ ] `TELEGRAM_API_HASH`
  - [ ] `TELEGRAM_PHONE_NUMBER`
  - [ ] `TELEGRAM_SESSION_STRING` (optional, for scraping feature)

- [ ] Streamlit Community Cloud account created
- [ ] GitHub account linked to Streamlit Cloud
- [ ] Repository is accessible from Streamlit Cloud

## Deployment Execution

### Step 1: Deploy App
- [ ] Deploy to Streamlit Cloud via https://share.streamlit.io
- [ ] Select correct repository
- [ ] Set main file to `app.py`
- [ ] App shows error about missing secrets (expected)

### Step 2: Add Secrets
- [ ] Open app → Hamburger menu → Settings → Secrets
- [ ] Paste all secrets from above
- [ ] Verify multi-line strings (like private_key) use triple quotes
- [ ] Save secrets and wait for app to restart

### Step 3: Verify Functionality
- [ ] Dashboard page loads without errors
- [ ] Customer Records page displays data
- [ ] Data Export page works
- [ ] Analytics visualizations render
- [ ] No errors in Streamlit Cloud logs

## Post-Deployment

- [ ] Share app URL with team: `https://share.streamlit.io/USERNAME/repo-name`
- [ ] Monitor app in first 24 hours for errors
- [ ] Set reminder to check logs weekly
- [ ] Document app usage for team

## Security Reminders

- [ ] Keep GitHub repository **private**
- [ ] Never share or post your secrets
- [ ] Rotate credentials every 90 days
- [ ] If credentials leaked: immediately delete key in Google Cloud & regenerate Telegram session
- [ ] Monitor app activity in logs

---

## Completion

**Date Completed:** _______________

**Deployed By:** _______________

**App URL:** https://share.streamlit.io/_______________

**Notes:**
```
[Add any additional notes or issues encountered]




```

