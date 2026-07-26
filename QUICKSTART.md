# 🚀 Quick Start: Deploy to Streamlit Cloud

**Estimated time:** 30-45 minutes (first time setup)

This is a **TL;DR** guide. For detailed steps, see the linked documents.

---

## 5-Minute Overview

You have a Streamlit dashboard for Telegram customer data. To host it publicly:

1. **Push code to private GitHub repo** (with sensitive files excluded)
2. **Get credentials** from Google Cloud and Telegram
3. **Deploy to Streamlit Cloud** (free hosting)
4. **Add secrets** to Streamlit dashboard
5. **Done!** Your app is live

---

## Prerequisites

Before you start, have ready:

- [ ] GitHub account (free at https://github.com)
- [ ] Google Cloud account (free at https://console.cloud.google.com)
- [ ] Streamlit account (free at https://share.streamlit.io)
- [ ] Your Google Sheet ID
- [ ] Telegram API credentials (from https://my.telegram.org/auth)

---

## The Four Documents

| Document | Purpose | Time |
|----------|---------|------|
| [GITHUB_SETUP.md](GITHUB_SETUP.md) | Set up GitHub repo & push code | 10 min |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Detailed deployment walkthrough | 30 min |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Step-by-step verification | 20 min |
| [verify_deployment.py](verify_deployment.py) | Auto-verify setup (run this first!) | 2 min |

---

## Getting Started NOW

### Step 1️⃣: Verify Your Setup (2 minutes)

```powershell
cd "C:\Users\tra.troeurn\OneDrive - Chip Mong Group\Documents\Scrape_customer_data_tele\Telegram_srape Python Script\Tele_scrap"
python verify_deployment.py
```

**Expected:** ✓ All checks pass

If checks fail: Fix the issues shown and rerun.

### Step 2️⃣: Set Up GitHub (10 minutes)

Follow [GITHUB_SETUP.md](GITHUB_SETUP.md)

**Result:** Your code is on GitHub (privately)

### Step 3️⃣: Gather Credentials (15 minutes)

Collect these values (you'll need them in 30 minutes):

**From Google Cloud:**
- `GOOGLE_SHEET_ID` — Your sheet's ID from the URL
- `GOOGLE_WORKSHEET_NAME` — Worksheet name (default: `testing`)
- `gcp_service_account` — Entire JSON object from your service account key file

**From Telegram:**
- `TELEGRAM_API_ID` — from https://my.telegram.org/auth
- `TELEGRAM_API_HASH` — from https://my.telegram.org/auth
- `TELEGRAM_PHONE_NUMBER` — Your Telegram account phone
- `TELEGRAM_SESSION_STRING` — (optional, for scraping feature)

See [DEPLOYMENT_GUIDE.md Phases 3-4](DEPLOYMENT_GUIDE.md#phase-3-prepare-google-cloud-credentials) for detailed steps.

### Step 4️⃣: Deploy (5 minutes)

1. Go to https://share.streamlit.io
2. Click **Create app**
3. Connect your GitHub account
4. Select your repository: `telegram-scraper-dashboard`
5. Main file: `app.py`
6. Click **Deploy**

Wait 2-3 minutes for deployment. You'll see an error about missing secrets—**this is expected**.

### Step 5️⃣: Add Secrets (5 minutes)

1. Click **≡ (hamburger menu)** in top-right
2. Select **Settings** → **Secrets**
3. Paste this template and fill in your values:

```toml
GOOGLE_SHEET_ID = "your-sheet-id-here"
GOOGLE_WORKSHEET_NAME = "testing"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
your-private-key-content-here
-----END PRIVATE KEY-----
"""
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"

TELEGRAM_API_ID = "your-telegram-api-id"
TELEGRAM_API_HASH = "your-telegram-api-hash"
TELEGRAM_PHONE_NUMBER = "your-phone-number"
TELEGRAM_SESSION_STRING = "your-session-string-if-you-have-one"
```

4. Click **Save**
5. Wait 30 seconds for app to restart

### Step 6️⃣: Test Your App ✨

Visit: `https://share.streamlit.io/YOUR_USERNAME/telegram-scraper-dashboard`

You should see:
- ✅ Dashboard page loads with data
- ✅ Customer Records page works
- ✅ Data Export available
- ✅ No errors in logs

---

## Common Issues

### "AttributeError: None has no attribute 'get'"
**Solution:** Missing secrets in Streamlit Cloud. Go to Settings → Secrets and verify all values are entered.

### "Permission denied when accessing Google Sheet"
**Solution:** Share your Google Sheet with the `client_email` from your service account.

### "Telegram session expired"
**Solution:** Use `TELEGRAM_SESSION_STRING` instead of local session files.

---

## After Deployment

### Share Your App
```
https://share.streamlit.io/YOUR_USERNAME/telegram-scraper-dashboard
```

Send this link to your team!

### Monitor & Update
- Check **Manage app** → **Logs** weekly for errors
- Make local changes, commit, and push to GitHub—**Streamlit Cloud auto-redeploys**
- Rotate credentials every 90 days

### Keep It Secure
- ✅ Repository stays private
- ✅ Never share secrets
- ✅ If credentials leak: rotate immediately

---

## Need Help?

| Problem | Guide |
|---------|-------|
| GitHub setup fails | [GITHUB_SETUP.md](GITHUB_SETUP.md#troubleshooting) |
| Can't get Telegram credentials | [DEPLOYMENT_GUIDE.md Phase 4](DEPLOYMENT_GUIDE.md#phase-4-obtain-telegram-credentials) |
| Secrets configuration issues | [DEPLOYMENT_GUIDE.md Phase 5.2](DEPLOYMENT_GUIDE.md#52-add-secrets-to-streamlit-cloud) |
| General deployment flow | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| Pre-deployment checklist | [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) |

---

## What Happens Next?

```
Your Computer
    ↓
 GitHub (Private)
    ↓
 Streamlit Cloud
    ↓
 Public Internet
    ↓
 Your Team's Browsers
```

Your app will be **live on the internet**, accessible from anywhere!

---

## Summary

| Phase | Action | Time | Status |
|-------|--------|------|--------|
| 1 | Run verification script | 2 min | ⬜ TODO |
| 2 | Set up GitHub repo | 10 min | ⬜ TODO |
| 3 | Get credentials | 15 min | ⬜ TODO |
| 4 | Deploy to Streamlit Cloud | 5 min | ⬜ TODO |
| 5 | Add secrets | 5 min | ⬜ TODO |
| 6 | Test app | 5 min | ⬜ TODO |
| **Total** | | **42 min** | ⬜ TODO |

---

**Ready to begin? Start with [GITHUB_SETUP.md](GITHUB_SETUP.md)!** 🚀

