# Deployment Guide: Telegram Customer Data Scraper

This guide covers deploying the Streamlit dashboard to **Streamlit Community Cloud**.

## Prerequisites

- ✅ GitHub account
- ✅ Streamlit Community Cloud account (free at https://streamlit.io/cloud)
- ✅ Google Cloud service account with Sheets API enabled
- ✅ Telegram API credentials
- ✅ Access to target Telegram channels
- ✅ Access to your Google Sheet (to share with service account)

---

## Phase 1: Pre-Deployment Checklist

### 1.1 Verify Sensitive Files Are Excluded

Your `.gitignore` is already configured. **Verify these files are NOT in your repo:**

- ❌ `khemra_account.json` (Google service account key)
- ❌ `tg_sessions/geo_scraper.session` (Telegram session file)
- ❌ `.streamlit/secrets.toml` (local secrets)
- ❌ `.env` files
- ❌ `Script.ipynb` (if it contains hardcoded credentials)

**Check before pushing:**
```powershell
git status
# Ensure the above files don't appear
```

### 1.2 Clean Up Local Secrets

Before committing, ensure your repository is clean:

```powershell
# Remove any accidentally added credentials
git rm --cached khemra_account.json
git rm --cached .streamlit/secrets.toml
git rm --cached -r tg_sessions/

# Verify
git status
```

### 1.3 Update Script.ipynb (If Sharing)

If `Script.ipynb` contains hardcoded values:
1. Open the notebook
2. Replace hardcoded Telegram API IDs, sheet IDs, and phone numbers with placeholders
3. **Clear all output cells** before committing: Cell → All Output → Clear

---

## Phase 2: GitHub Setup

### 2.1 Create a Private GitHub Repository

1. Go to https://github.com/new
2. Create a **private** repository
3. Name it: `telegram-scraper-dashboard` (or your preference)
4. Do NOT initialize with README, .gitignore, or license (we have these)

### 2.2 Push Your Code

```powershell
cd "path\to\Tele_scrap"

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: Telegram scraper dashboard"

# Add remote (replace YOUR_USERNAME and repo-name)
git remote add origin https://github.com/YOUR_USERNAME/repo-name.git
git branch -M main
git push -u origin main
```

**Verify on GitHub:** The sensitive files should NOT appear in your repo.

---

## Phase 3: Prepare Google Cloud Credentials

### 3.1 Create a Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the **Google Sheets API** and **Google Drive API**
4. Go to **Service Accounts** (under IAM & Admin)
5. Create a new service account with name: `telegram-scraper`
6. Grant it **Viewer** role (for sheets access)
7. Create a **JSON key** and download it

### 3.2 Share Your Google Sheet

1. Open your target Google Sheet
2. In the sheet, click **Share**
3. Share with the `client_email` from the service account JSON
4. Grant **Editor** permission

---

## Phase 4: Obtain Telegram Credentials

### 4.1 Get Telegram API Credentials

1. Go to https://my.telegram.org/auth
2. Log in with your Telegram account
3. Go to **API development tools**
4. Create a new application if you don't have one
5. Copy:
   - `api_id`
   - `api_hash`

### 4.2 Generate Session String (for Deployment)

**For local development:** The app uses `tg_sessions/geo_scraper.session`

**For Streamlit Cloud:** You need a `TELEGRAM_SESSION_STRING`. To generate this locally:

```powershell
# Option 1: Use the app's Scrape Data page to test and generate a session string
# Option 2: Run a session string generator (see below)

# Save your phone number for later
$phone = "+855885478958"  # Replace with your actual phone number
```

To generate a persistent session string, you can use this Python snippet locally:

```python
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

async def create_session_string():
    api_id = 22365302  # Replace with your API ID
    api_hash = "df22eea81948788953b28b8112ab926a"  # Replace with your API hash
    phone_number = "+855885478958"  # Replace with your phone
    
    client = TelegramClient(StringSession(), api_id, api_hash)
    
    async with client:
        await client.start(phone=phone_number)
        session_string = client.session.save()
        print(f"Session String:\n{session_string}")

asyncio.run(create_session_string())
```

**Important:** Save this session string securely—you'll need it for Streamlit Secrets.

---

## Phase 5: Deploy to Streamlit Community Cloud

### 5.1 Connect GitHub to Streamlit

1. Go to https://share.streamlit.io
2. Click **Create app**
3. Link your GitHub account (authorize Streamlit)
4. Select your repository: `telegram-scraper-dashboard`
5. Select branch: `main`
6. Set main file path: `app.py`
7. Click **Deploy**

The app will deploy and attempt to run. You'll see an error about missing secrets—**this is expected**.

### 5.2 Add Secrets to Streamlit Cloud

1. Once deployed, click the **hamburger menu** (☰) in the top-right
2. Select **Settings** → **Secrets**
3. Copy the contents from `.streamlit/secrets.toml.example`
4. Paste into the Secrets text area and fill in all values:

```toml
GOOGLE_SHEET_ID = "your-actual-sheet-id"
GOOGLE_WORKSHEET_NAME = "testing"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
[paste entire private key from the JSON file]
-----END PRIVATE KEY-----
"""
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"

# Required only for the "Scrape Data" page
TELEGRAM_API_ID = "your-telegram-api-id"
TELEGRAM_API_HASH = "your-telegram-api-hash"
TELEGRAM_PHONE_NUMBER = "your-telegram-phone-number"
TELEGRAM_SESSION_STRING = "your-persistent-session-string"
```

4. Click **Save** and wait for the app to restart

### 5.3 Verify Deployment

Once secrets are saved:
- The **Dashboard** page should load and display data from your Google Sheet
- The **Data Export** page should work for exporting customer records
- The **Scrape Data** page requires the Telegram session string

---

## Phase 6: Post-Deployment Verification

### 6.1 Test Core Features

- [ ] Dashboard loads and displays data
- [ ] Customer Records page shows data from Google Sheet
- [ ] Data Export downloads CSV/Excel files
- [ ] Analytics page generates charts
- [ ] Telegram Channels list appears

### 6.2 Test Scraping (if credentials provided)

- [ ] Scrape Data page is accessible
- [ ] Can initiate scrape jobs (if session string is valid)
- [ ] Scraping History updates after job completion

### 6.3 Monitor Logs

Click the **hamburger menu** → **Manage app** → **View logs** to check for:
- Missing dependencies
- Secret configuration errors
- API connection issues

---

## Phase 7: Troubleshooting

### Issue: "Missing gcp_service_account"

**Solution:** Ensure your `[gcp_service_account]` table is properly formatted in Secrets. Multi-line strings must use triple quotes.

### Issue: Google Sheets connection fails

**Solution:**
1. Verify the sheet is shared with the service account's `client_email`
2. Check that `GOOGLE_SHEET_ID` matches your actual sheet URL
3. Confirm the worksheet name (default: `testing`) exists in the sheet

### Issue: Telegram features not working

**Solution:**
1. If using local session: Feature won't work on Streamlit Cloud
2. If using session string: Ensure `TELEGRAM_SESSION_STRING` is set in Secrets
3. Verify Telegram API credentials are correct

### Issue: Session expired

**Solution:** Telegram sessions expire after some time. You may need to periodically regenerate the session string and update Secrets.

---

## Phase 8: Maintenance & Updates

### Update Deployment

```powershell
# Make changes locally
git add .
git commit -m "Update feature/fix bug"
git push origin main

# Streamlit Cloud will auto-detect and redeploy
# Monitor deployment in the "Manage app" view
```

### Rotate Credentials Periodically

- [ ] Rotate Google service account key every 90 days
- [ ] Regenerate Telegram session string if it expires
- [ ] Keep your GitHub repository private

### Monitor Usage

- View Streamlit Cloud dashboard for app usage, errors, and resource consumption
- Check logs regularly for warnings or failures

---

## Security Best Practices

1. **Never commit credentials** to GitHub
2. **Use Streamlit Secrets** for all sensitive data (not environment variables in code)
3. **Keep your GitHub repo private**
4. **Share Sheets with service account only**, not with personal Google accounts
5. **Rotate credentials** if they're ever accidentally exposed
6. **Monitor Telegram session** health—regenerate if compromised

---

## Summary

Your deployment workflow:
1. ✅ Ensure `.gitignore` is correct
2. ✅ Push code to private GitHub repo
3. ✅ Create Google service account & Telegram API credentials
4. ✅ Deploy to Streamlit Cloud
5. ✅ Add secrets via Streamlit Cloud dashboard
6. ✅ Test and monitor

Your app is now **live and ready to use**! 🚀

---

## Quick Reference: URLs

- **Streamlit Cloud**: https://share.streamlit.io
- **Google Cloud Console**: https://console.cloud.google.com
- **Telegram API**: https://my.telegram.org/auth
- **Your App**: `https://share.streamlit.io/YOUR_USERNAME/repo-name`

---

## Support

For issues with:
- **Streamlit**: https://discuss.streamlit.io
- **Google Sheets API**: https://developers.google.com/sheets/api/guides
- **Telethon**: https://docs.telethon.dev/

