# Security notes before sharing this project

Do not include the following files in a ZIP that will be sent to another person:

- `khemra_account.json`
  - Contains a Google service-account private key.
  - Anyone with this file may be able to access Google Sheets/Drive resources granted to that service account.
  - Rotate/delete this key in Google Cloud if it was already shared.

- `tg_sessions/geo_scraper.session`
  - Contains a Telegram login session.
  - Anyone with this file may be able to reuse the logged-in Telegram session.
  - Delete the session file before sharing and log out/revoke sessions from Telegram if it was already shared.

- `Script.ipynb`
  - Contains hardcoded Telegram API values, a phone number, Google Sheets IDs, channel links, and local file paths.
  - Clean or replace those values with placeholders before sending the notebook.
  - The notebook output cells may also reveal scraped data and account/channel details; clear outputs before sharing.

Recommended safe sharing steps:

1. Remove `khemra_account.json` from the ZIP.
2. Remove the whole `tg_sessions/` folder from the ZIP.
3. Replace hardcoded credentials in `Script.ipynb` with placeholders or environment variables.
4. Clear notebook outputs before sharing.
5. Rotate any key/session that may already have been exposed.
