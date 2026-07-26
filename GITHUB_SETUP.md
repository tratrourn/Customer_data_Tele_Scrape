# GitHub Setup Guide for Streamlit Deployment

This guide walks you through setting up a GitHub repository for deploying the Telegram Scraper Dashboard to Streamlit Cloud.

## Step 1: Prepare Your Local Repository

### 1.1 Verify Your Project Structure

Your project should be in this directory:
```
Tele_scrap/
├── app.py
├── scraper_backend.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example
├── DEPLOYMENT_GUIDE.md
├── DEPLOYMENT_CHECKLIST.md
├── verify_deployment.py
├── khemra_account.json          (LOCAL ONLY - not committed)
├── tg_sessions/
│   └── geo_scraper.session      (LOCAL ONLY - not committed)
└── Script.ipynb
```

### 1.2 Verify .gitignore is Correct

**Open `.gitignore` and verify it contains:**
```
khemra_account.json
.streamlit/secrets.toml
tg_sessions/
*.session
.venv/
venv/
__pycache__/
*.py[cod]
.env
*.pem
*.key
*.p12
*.pfx
```

If your `.gitignore` is missing these entries, update it now.

### 1.3 Run Verification Script

```powershell
cd "path\to\Tele_scrap"
python verify_deployment.py
```

**Expected output:** All checks should pass. Fix any issues marked "ERROR" before proceeding.

---

## Step 2: Create a GitHub Repository

### 2.1 Go to GitHub

1. Visit https://github.com/new
2. Sign in if needed

### 2.2 Create Repository

Fill in the form:

| Field | Value |
|-------|-------|
| **Repository name** | `telegram-scraper-dashboard` (or your preferred name) |
| **Description** | `Streamlit dashboard for Telegram customer data scraping` |
| **Visibility** | ✅ **PRIVATE** (Important for security!) |
| **Initialize with** | ❌ Leave empty (we have our own .gitignore and README) |

### 2.3 Click "Create repository"

GitHub will show setup instructions. **Keep this page open** for the next step.

---

## Step 3: Push Your Code to GitHub

### 3.1 Open Terminal in Your Project Directory

```powershell
# Navigate to your project
cd "C:\Users\tra.troeurn\OneDrive - Chip Mong Group\Documents\Scrape_customer_data_tele\Telegram_srape Python Script\Tele_scrap"
```

### 3.2 Check Git Status (Should be Clean)

```powershell
git status
```

**Expected output:**
```
On branch main
nothing to commit, working tree clean
```

If you see changes or uncommitted files, they may be sensitive. Use `git status` to review:
```powershell
git status
```

### 3.3 Initialize Git (if not already done)

```powershell
# Check if git is already initialized
git log --oneline -1

# If you see a commit, skip this step. If you get an error:
git init
git add .
git commit -m "Initial commit: Telegram scraper dashboard"
```

### 3.4 Add Remote Repository

Replace `YOUR_USERNAME` and `repo-name` with your GitHub username and repository name:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/telegram-scraper-dashboard.git
git branch -M main
git push -u origin main
```

**Example:**
```powershell
git remote add origin https://github.com/johndoe/telegram-scraper-dashboard.git
git branch -M main
git push -u origin main
```

### 3.5 When Prompted for Credentials

GitHub no longer accepts password authentication. You'll need to authenticate with one of these methods:

#### Option A: GitHub CLI (Recommended)
```powershell
# Install GitHub CLI first from https://cli.github.com
# Then authenticate:
gh auth login
```

#### Option B: Personal Access Token
1. Go to GitHub → Settings → Developer settings → **Personal access tokens** → **Tokens (classic)**
2. Click "Generate new token"
3. Name it: `streamlit-deployment`
4. Select scopes: ✅ `repo` (all)
5. Click "Generate token"
6. Copy the token (you won't see it again)
7. When prompted for password in terminal, **paste the token** (it won't show as you type)

#### Option C: SSH Key
```powershell
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Add to SSH agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519

# Add public key to GitHub:
# 1. Go to GitHub → Settings → SSH and GPG keys
# 2. Click "New SSH key"
# 3. Paste contents of C:\Users\YOUR_USERNAME\.ssh\id_ed25519.pub
# 4. Save

# Then use SSH remote instead:
git remote remove origin
git remote add origin git@github.com:YOUR_USERNAME/telegram-scraper-dashboard.git
git push -u origin main
```

### 3.6 Verify Push Succeeded

```powershell
git log --oneline -1 --remotes
```

You should see your commit listed under `origin/main`.

---

## Step 4: Verify on GitHub Web

1. Go to https://github.com/YOUR_USERNAME/telegram-scraper-dashboard
2. Verify you see your code
3. **Important:** Verify these files are NOT in the repository:
   - ❌ `khemra_account.json` should NOT appear
   - ❌ `secrets.toml` should NOT appear
   - ❌ `tg_sessions/` folder should NOT appear

If you see any sensitive files, **DELETE THE REPOSITORY** and start over:
1. GitHub → Your repo → Settings → scroll to "Danger Zone" → Delete this repository
2. Fix your `.gitignore`
3. Run `verify_deployment.py` again
4. Create a new repository and push again

---

## Step 5: Prepare for Streamlit Deployment

Before deploying to Streamlit Cloud, make sure you have:

- [ ] Private GitHub repository created
- [ ] Code successfully pushed
- [ ] No sensitive files visible on GitHub
- [ ] GitHub repository link ready

**Your repo URL will be:**
```
https://github.com/YOUR_USERNAME/telegram-scraper-dashboard
```

---

## Next Steps

Now proceed to:
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete Phase 3-5 (Credentials and Streamlit Cloud setup)
2. Or follow [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for a structured checklist

---

## Troubleshooting

### "fatal: not a git repository"
```powershell
git init
git add .
git commit -m "Initial commit"
```

### "rejected ... [remote rejected] main -> main (refusing to push)"
Check .gitignore is correct and sensitive files aren't staged:
```powershell
git status
git rm --cached khemra_account.json
git rm --cached -r tg_sessions/
git commit -m "Remove sensitive files"
git push
```

### "Permission denied (publickey)"
Your SSH key isn't set up. Use GitHub CLI or Personal Access Token instead.

### "remote already exists"
```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/repo-name.git
git push -u origin main
```

---

## Keeping Your Repository Updated

After deployment, when you make changes:

```powershell
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Description of changes"

# Push to GitHub
git push origin main

# Streamlit Cloud will automatically redeploy
```

---

## Security Reminders

✅ **Always:**
- Keep your GitHub repository **private**
- Never commit sensitive files
- Use `.gitignore` for credentials
- Verify no secrets before pushing

❌ **Never:**
- Make your repository public
- Share your credentials
- Commit `.env`, `secrets.toml`, or private keys
- Share access to your repository with untrusted users

