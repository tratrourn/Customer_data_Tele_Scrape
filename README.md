# Customer data scraping dashboard

Streamlit dashboard for viewing Telegram customer data stored in Google Sheets.

## Run locally

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

For local Google Sheets access, keep `khemra_account.json` beside `app.py`. It is ignored by Git.

## Deploy to Streamlit Community Cloud

1. Create a private GitHub repository using the contents of this folder as the repository root.
2. Do not commit `khemra_account.json`, `.env`, Telegram session files, or `.streamlit/secrets.toml`.
3. In Streamlit Community Cloud, choose the repository and deploy `app.py`.
4. Copy the values from `.streamlit/secrets.toml.example` into the app's **Advanced settings > Secrets** panel, replacing every placeholder with your own values.

The Google service account needs access to the target Google Sheet. Share the sheet with the `client_email` from the service-account credentials.

The dashboard and exports require only the Google Sheets secrets. The hosted Scrape Data page additionally requires a persistent `TELEGRAM_SESSION_STRING`; local Telegram session files are not persistent in Community Cloud.
