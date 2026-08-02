from __future__ import annotations

import asyncio
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Iterable, Optional

from collections import defaultdict

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from telethon.errors import FloodWaitError
from telethon import TelegramClient
from telethon.sessions import StringSession


BASE_DIR = Path(__file__).resolve().parent
SESSION_DIR = BASE_DIR / "tg_sessions"
SESSION_PATH = SESSION_DIR / "geo_scraper"
SERVICE_ACCOUNT_PATH = BASE_DIR / "khemra_account.json"


def get_deployment_setting(name: str, default: str = "") -> str:
    """Read a setting from environment variables or Streamlit Secrets."""
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(name, default))
    except Exception:
        return default


def get_google_service_account_credentials(scope: list[str]) -> ServiceAccountCredentials:
    """Use a local credential file in development or Streamlit Secrets in hosting."""
    if SERVICE_ACCOUNT_PATH.exists():
        return ServiceAccountCredentials.from_json_keyfile_name(str(SERVICE_ACCOUNT_PATH), scope)

    try:
        import streamlit as st

        service_account = st.secrets.get("gcp_service_account")
        if service_account:
            return ServiceAccountCredentials.from_json_keyfile_dict(dict(service_account), scope)
    except Exception:
        pass

    raise FileNotFoundError(
        "Google service-account credentials are missing. Add khemra_account.json locally "
        "or gcp_service_account to Streamlit Secrets when hosting."
    )


API_ID = int(get_deployment_setting("TELEGRAM_API_ID", "22365302"))
API_HASH = get_deployment_setting("TELEGRAM_API_HASH", "df22eea81948788953b28b8112ab926a")
PHONE_NUMBER = get_deployment_setting("TELEGRAM_PHONE_NUMBER", "+855885478958")
TELEGRAM_SESSION_STRING = get_deployment_setting("TELEGRAM_SESSION_STRING")
SHEET_ID = get_deployment_setting("GOOGLE_SHEET_ID", "1wM7DTHizhg_A3h0qV3EhX4os4hk46uolW-ESQSJkgZs")
WORKSHEET_NAME = get_deployment_setting("GOOGLE_WORKSHEET_NAME", "Retail_update")
TELEGRAM_FLOOD_SLEEP_THRESHOLD = 180

TARGET_CHANNELS = [
    "https://t.me/+1MbLNmcPsZw5YWJl", #TLK
    "https://t.me/+-tr90ltW_zk4MTFl", #ASN
    "https://t.me/+yNETl07vtcM0MTRl", #BSL
    "https://t.me/+nq35Oy2dDssxODNl", #NRD
    "https://t.me/+ouwmdyThw7I2N2Nl", #271M
    "https://t.me/+Cl85yiAxl5xmZDM1", #598M
    "https://t.me/+JeQdy_3JC20wYTY1", #PDT
    "https://t.me/+97WK8wVcRmgxYjY9", #MTT
    "https://t.me/+mCpwZ7Z-KBsxY2Rl", #CMT
    "https://t.me/+j743FvFEECYyNTc1", #SRP
    "https://t.me/+SlZXNVyWbH4zNTg1", #SSP
    "https://t.me/+VaLceESv1jIzMDNl", #BTI
    "https://t.me/+UCjId_iRVsIwOTll", #PST
    "https://t.me/+sIb5nVhnn9xlZjk9", #SSM
    "https://t.me/+vkpxR1yV275hNGI1", #RSK
    "https://t.me/+YniwokcKqwdmOTY1", #BTK
    "https://t.me/+wlUNfNvUwv41YzQ1", #MMT
    "https://t.me/+xFopoqWlbmkwNjM1", #CHA
    "https://t.me/+esfcpSjuQ4w3ODE1", #BTB
    "https://t.me/+a8ciV6h5a4liMTk9", #VSR
    "https://t.me/+BJ9hdNyKJHc3Njc1", #STG
    "https://t.me/+DauAFdF-yCI1ZTNl", #KTE
    "https://t.me/+ELy9Fes6wC83YWU1", #KPC
    "https://t.me/+DfvdkDoi42liMTU1", #SNG
    "https://t.me/+bcBVZO-ZFQBjYjk1", #STS
    "https://t.me/+vfUy-D95bj44ZTNl", #PMR
    "https://t.me/+GC7KD-xBJfoyYzE1", #PVH
    "https://t.me/+gLQYhzJStoo5OTk1", #TKM
    "https://t.me/+mZqvOiubQuZkY2Jl", #KPT
    "https://t.me/+orPDzcb7YJs4OTY1", #NRM
    "https://t.me/+hUZklAeUAag0ZTk1", #KCG
    "https://t.me/+6onxVVeadwc0MThl", #BLG
    "https://t.me/+dU936kyELnJhZmE1", #DKO
    "https://t.me/asdcce1" #SRG
]

STRUCTURED_FIELD_PATTERN = re.compile(r"\b(Name|Tel|Telephone|Business|Purpose|Bank|Amount|Interest|Loan Type|Tenure|Maturity|Status|Potential|Potential Product|Remark)\b", re.IGNORECASE)

OUTPUT_COLUMNS = [
    "Source_Channel",
    "Sender_ID",
    "Sender_Name",
    "Name",
    "Tel",
    "Business",
    "Purpose",
    "Bank",
    "Amount",
    "Interest",
    "Loan_Type",
    "Tenure",
    "Maturity",
    "Status",
    "Potential_Level",
    "Potential_Product",
    "Remark",
    "Message_Date",
    "Latitude",
    "Longitude",
    "Raw_Text",
    "Has_Image",
    "Has_Location",
]

FIELD_PATTERNS = {
    "Name": re.compile(r"^\s*Name\s*:\s*(.*)$", re.IGNORECASE),
    "Tel": re.compile(r"^\s*Tel\s*:\s*(.*)$", re.IGNORECASE),
    "Business": re.compile(r"^\s*Business\s*:\s*(.*)$", re.IGNORECASE),
    "Purpose": re.compile(r"^\s*Purpose\s*:\s*(.*)$", re.IGNORECASE),
    "Bank": re.compile(r"^\s*Bank\s*:\s*(.*)$", re.IGNORECASE),
    "Amount": re.compile(r"^\s*Amount\s*:\s*(.*)$", re.IGNORECASE),
    "Interest": re.compile(r"^\s*Interest\s*:\s*(.*)$", re.IGNORECASE),
    "Loan_Type": re.compile(r"^\s*Loan\s*Type\s*:\s*(.*)$", re.IGNORECASE),
    "Tenure": re.compile(r"^\s*Tenure\s*:\s*(.*)$", re.IGNORECASE),
    "Maturity": re.compile(r"^\s*Maturity\s*:\s*(.*)$", re.IGNORECASE),
    "Status": re.compile(r"^\s*Status\s*:\s*(.*)$", re.IGNORECASE),
    "Potential_Level": re.compile(r"^\s*Potential\s*H/M/L\s*:\s*(.*)$", re.IGNORECASE),
    "Potential_Product": re.compile(r"^\s*Potential\s*Product\s*:\s*(.*)$", re.IGNORECASE),
    "Remark": re.compile(r"^\s*Remark\s*:\s*(.*)$", re.IGNORECASE),
}

FIELD_ALIASES = {
    "telephone": "Tel",
    "loan type": "Loan_Type",
    "loan_type": "Loan_Type",
    "potential h/m/l": "Potential_Level",
    "potential level": "Potential_Level",
    "potential_product": "Potential_Product",
    "potential product": "Potential_Product",
}


def format_duration(start_time: float) -> str:
    elapsed = max(int(time.time() - start_time), 0)
    minutes, seconds = divmod(elapsed, 60)
    return f"{minutes}m {seconds:02d}s"


def looks_like_customer_record(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return False
    return bool(STRUCTURED_FIELD_PATTERN.search(stripped))


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return ""
    return digits


def to_sheet_bool(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def extract_coordinates_from_text(text: str) -> tuple[str, str]:
    normalized_text = re.sub(r"\s+", " ", text or "").strip()

    labeled_patterns = [
        re.compile(r"(?:lat|latitude)\s*[:=]\s*(-?\d{1,3}(?:\.\d+)?)\s*(?:,|\s)+\s*(?:lng|lon|long|longitude)\s*[:=]\s*(-?\d{1,3}(?:\.\d+)?)", re.IGNORECASE),
        re.compile(r"(?:lng|lon|long|longitude)\s*[:=]\s*(-?\d{1,3}(?:\.\d+)?)\s*(?:,|\s)+\s*(?:lat|latitude)\s*[:=]\s*(-?\d{1,3}(?:\.\d+)?)", re.IGNORECASE),
    ]

    for pattern in labeled_patterns:
        match = pattern.search(normalized_text)
        if match:
            first, second = match.group(1), match.group(2)
            if "lat" in pattern.pattern.lower().split("\\s*[:=]\\s*")[0]:
                return first, second
            return second, first

    pair_match = re.search(r"(-?\d{1,2}\.\d+)\s*[,/ ]\s*(-?\d{1,3}\.\d+)", normalized_text)
    if pair_match:
        lat, lon = pair_match.group(1), pair_match.group(2)
        try:
            lat_val = float(lat)
            lon_val = float(lon)
            if -90 <= lat_val <= 90 and -180 <= lon_val <= 180:
                return lat, lon
        except ValueError:
            pass

    return "", ""


def extract_location_coordinates(msg) -> tuple[str, str]:
    """Pull latitude/longitude from any known Telethon location shape."""

    def walk(value) -> tuple[str, str]:
        if value is None:
            return "", ""

        if hasattr(value, "to_dict"):
            try:
                value = value.to_dict()
            except Exception:
                pass

        if isinstance(value, dict):
            lat_value = None
            lon_value = None
            for key in ("lat", "latitude"):
                if key in value and value[key] is not None:
                    lat_value = value[key]
                    break
            for key in ("long", "lng", "lon", "longitude"):
                if key in value and value[key] is not None:
                    lon_value = value[key]
                    break

            if lat_value is not None and lon_value is not None:
                return str(lat_value), str(lon_value)

            for nested_key in ("geo", "location", "point", "venue"):
                nested_value = value.get(nested_key)
                lat, lon = walk(nested_value)
                if lat and lon:
                    return lat, lon

            return "", ""

        else:
            lat_value = getattr(value, "lat", None)
            lon_value = getattr(value, "long", None)
            if lon_value is None:
                lon_value = getattr(value, "lng", None)
            if lon_value is None:
                lon_value = getattr(value, "longitude", None)
            if lat_value is None:
                lat_value = getattr(value, "latitude", None)

            if lat_value is not None and lon_value is not None:
                return str(lat_value), str(lon_value)

            for nested_attr in ("geo", "location", "point", "venue"):
                nested_value = getattr(value, nested_attr, None)
                lat, lon = walk(nested_value)
                if lat and lon:
                    return lat, lon

            return "", ""

        return "", ""

    candidates = [
        getattr(msg, "media", None),
        getattr(msg, "geo", None),
        getattr(msg, "location", None),
        getattr(getattr(msg, "media", None), "geo", None),
        getattr(getattr(msg, "media", None), "location", None),
        getattr(getattr(msg, "media", None), "venue", None),
        getattr(getattr(msg, "media", None), "vgeo", None),
    ]

    for candidate in candidates:
        lat, lon = walk(candidate)
        if lat and lon:
            return lat, lon

    return extract_coordinates_from_text(getattr(msg, "message", "") or "")


def extract_structured_fields(text: str) -> dict:
    result = {key: "" for key in FIELD_PATTERNS.keys()}
    normalized_text = re.sub(r"\r\n|\r", "\n", text or "")

    current_field = None
    current_value_lines = []

    def store_current_field() -> None:
        nonlocal current_field, current_value_lines
        if current_field is not None:
            value = "\n".join(current_value_lines).strip()
            result[current_field] = re.sub(r"\s+$", "", value)
        current_field = None
        current_value_lines = []

    for raw_line in normalized_text.splitlines():
        line = raw_line.strip()
        if not line:
            if current_field is not None:
                current_value_lines.append("")
            continue

        matched_field = None
        matched_value = None

        for field_name, pattern in FIELD_PATTERNS.items():
            match = pattern.match(line)
            if match:
                matched_field = field_name
                matched_value = (match.group(1) or "").strip()
                break

        if matched_field is not None:
            store_current_field()
            current_field = matched_field
            current_value_lines = [matched_value] if matched_value else []
            continue

        lowered = line.lower()
        alias_field = FIELD_ALIASES.get(lowered)
        if alias_field is not None:
            store_current_field()
            current_field = alias_field
            current_value_lines = []
            continue

        if current_field is not None:
            current_value_lines.append(line)

    store_current_field()

    result["Tel"] = normalize_phone(result.get("Tel", "").strip())
    return result


def build_output_record(channel_name: str, sender_id: int, sender_name: str, msg) -> dict:
    raw_text = (getattr(msg, "message", "") or "").strip()
    parsed = extract_structured_fields(raw_text)

    lat, lon = extract_location_coordinates(msg)

    has_location = bool(lat and lon)
    has_image = bool(getattr(msg, "photo", None) or (getattr(msg, "media", None) and not has_location))

    message_date = getattr(msg, "date", None)
    message_date_str = message_date.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S") if message_date else ""

    return {
        "Source_Channel": channel_name,
        "Sender_ID": str(sender_id or ""),
        "Sender_Name": sender_name or "",
        "Name": parsed.get("Name", ""),
        "Tel": parsed.get("Tel", ""),
        "Business": parsed.get("Business", ""),
        "Purpose": parsed.get("Purpose", ""),
        "Bank": parsed.get("Bank", ""),
        "Amount": parsed.get("Amount", ""),
        "Interest": parsed.get("Interest", ""),
        "Loan_Type": parsed.get("Loan_Type", ""),
        "Tenure": parsed.get("Tenure", ""),
        "Maturity": parsed.get("Maturity", ""),
        "Status": parsed.get("Status", ""),
        "Potential_Level": parsed.get("Potential_Level", ""),
        "Potential_Product": parsed.get("Potential_Product", ""),
        "Remark": parsed.get("Remark", ""),
        "Message_Date": message_date_str,
        "Latitude": lat,
        "Longitude": lon,
        "Raw_Text": raw_text,
        "Has_Image": to_sheet_bool(has_image),
        "Has_Location": to_sheet_bool(has_location),
    }


def is_auto_bot_sender(sender_name: str | None, sender_id: object | None = None) -> bool:
    """Return True when the message is from the auto bot sender that should be skipped."""
    normalized_sender = (sender_name or "").strip().casefold()
    if normalized_sender in {"bp_bot", "bp bot", "bp-bot"}:
        return True
    if sender_id is not None:
        return str(sender_id).strip().casefold() in {"bp_bot", "bp bot", "bp-bot"}
    return False


def record_key(record: dict) -> tuple:
    return (
        (record.get("Source_Channel") or "").strip(),
        normalize_phone(record.get("Tel") or "").strip(),
        (record.get("Name") or "").strip().lower(),
        (record.get("Message_Date") or "").strip(),
    )


def ensure_sheet_headers(worksheet) -> None:
    """Guarantee header row exists and matches the target output schema."""
    header = worksheet.row_values(1)
    if header != OUTPUT_COLUMNS:
        worksheet.update("A1", [OUTPUT_COLUMNS])


def sanitize_dataframe_for_sheets(df: pd.DataFrame) -> pd.DataFrame:
    """Remove NaN / NaT / inf before sending to Google Sheets."""
    df = df.copy()
    df = df.replace([float("inf"), float("-inf")], "")
    df = df.astype(object)
    df = df.where(pd.notnull(df), "")
    return df


def extract_geo_from_message(msg):
    """Telegram location is usually inside msg.media.geo, not msg.geo."""
    media = getattr(msg, "media", None)
    if not media:
        return None, None

    geo = getattr(media, "geo", None)
    if geo and hasattr(geo, "lat") and hasattr(geo, "long"):
        return geo.lat, geo.long

    return None, None


def pop_best_candidate(candidates, target_dt, max_gap_minutes):
    """Find nearest message in time within allowed window."""
    if not candidates:
        return None

    best_idx = None
    best_gap = None

    for idx, item in enumerate(candidates):
        gap = abs((item["date"] - target_dt).total_seconds())
        if gap <= max_gap_minutes * 60:
            if best_gap is None or gap < best_gap:
                best_gap = gap
                best_idx = idx

    if best_idx is None:
        return None

    return candidates.pop(best_idx)


async def scrape_channels(
    selected_channels: Optional[Iterable[str]] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    log_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Run the real Telegram scrape using the project's existing Telethon session.
    This keeps the Streamlit UI connected to the actual workflow in the folder
    without forcing any editor or notebook interactions.
    """
    start_time = time.time()
    from_date = from_date or (datetime.now() - timedelta(days=1))
    to_date = to_date or datetime.now()

    # Keep comparisons consistent with Telegram message timestamps.
    from_date = from_date.replace(tzinfo=None)
    to_date = to_date.replace(tzinfo=None)
    if from_date > to_date:
        from_date, to_date = to_date, from_date

    selected_channels = list(selected_channels or TARGET_CHANNELS)
    if not selected_channels:
        selected_channels = list(TARGET_CHANNELS)

    def emit_log(message: str) -> None:
        if log_callback:
            log_callback(message)

    async def resolve_channel_entity(
        client: TelegramClient,
        channel_url: str,
        progress_callback=None,
        progress_value: int = 0,
    ):
        """Resolve a channel, waiting and retrying if Telegram rate-limits invite checks."""
        while True:
            try:
                return await client.get_entity(channel_url)
            except FloodWaitError as exc:
                wait_seconds = max(int(getattr(exc, "seconds", 0)), 1)
                if progress_callback:
                    progress_callback(
                        progress_value,
                        f"⏳ Telegram rate-limited this channel. Waiting {wait_seconds}s before retrying...",
                    )
                await asyncio.sleep(wait_seconds + 1)

    session_name = StringSession(TELEGRAM_SESSION_STRING) if TELEGRAM_SESSION_STRING else str(SESSION_PATH)
    if not TELEGRAM_SESSION_STRING:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)

    # Check if session file exists locally or session string is provided
    session_file_exists = (SESSION_PATH.parent / f"{SESSION_PATH.name}.session").exists()
    if not TELEGRAM_SESSION_STRING and not session_file_exists:
        raise RuntimeError(
            "❌ Telegram authentication unavailable.\n\n"
            "For Streamlit Cloud deployment:\n"
            "1. Add 'TELEGRAM_SESSION_STRING' to your Streamlit Secrets\n"
            "2. Generate it locally by running: streamlit run app.py → Settings → Authenticate Telegram\n\n"
            "For local development:\n"
            "1. Use a .session file from tg_sessions/ folder"
        )

    emit_log("🧪 ===== TELEGRAM SCRAPER - MULTI-TARGET EXECUTION =====")
    emit_log(f"📋 Global Limits: 1000000 requests, 1000000 messages (TESTING=True)")
    emit_log(f"📅 Scrape window: {from_date:%Y-%m-%d %H:%M:%S}  ->  {to_date:%Y-%m-%d %H:%M:%S}")

    try:
        async with TelegramClient(
            session_name,
            API_ID,
            API_HASH,
            request_retries=2,
            flood_sleep_threshold=TELEGRAM_FLOOD_SLEEP_THRESHOLD,
        ) as client:
            # Use timeout for client start (30 seconds)
            try:
                await asyncio.wait_for(client.connect(), timeout=30.0)
            except asyncio.TimeoutError:
                raise RuntimeError("⏱️ Timeout connecting to Telegram. The server may be unreachable or rate-limited.")
            emit_log("🔗 Connected to Telegram. Starting channel loop.")
            
            # Only call start() if NOT using StringSession (StringSession doesn't need auth)
            if not TELEGRAM_SESSION_STRING:
                try:
                    await asyncio.wait_for(client.start(phone=PHONE_NUMBER), timeout=60.0)
                except asyncio.TimeoutError:
                    raise RuntimeError("⏱️ Timeout during Telegram authentication. Please try again later.")
            
            if not await client.is_user_authorized():
                raise RuntimeError(
                    "❌ Telegram session is not authorized.\n"
                    "Please add a valid TELEGRAM_SESSION_STRING to Streamlit Secrets."
                )

            channel_targets = list(selected_channels)

            messages_scanned = 0
            records_extracted = 0
            errors = 0
            new_records = 0
            duplicates = 0
            error_details = []
            extracted_records = []
            pending_text_records = defaultdict(list)
            pending_location_messages = defaultdict(list)

            MAX_MESSAGES_PER_CHANNEL = 1000000  # Limit messages to scan per channel
            MAX_RECORDS_PER_CHANNEL = 1000000    # Stop scanning if we get 100 good records

            for idx, channel_url in enumerate(channel_targets, start=1):
                channel_progress = int(((idx - 1) / max(len(channel_targets), 1)) * 45)
                if progress_callback:
                    progress_callback(channel_progress, f"Scanning channel {idx}/{len(channel_targets)}")

                try:
                    entity = await resolve_channel_entity(
                        client,
                        channel_url,
                        progress_callback=progress_callback,
                        progress_value=channel_progress,
                    )
                    batch_messages = 0
                    batch_records = 0
                    channel_name = getattr(entity, "title", None) or channel_url
                    emit_log("")
                    emit_log(f"🎯 Starting scrape for: {channel_name}")
                    emit_log(f"📅 Filter from {from_date:%Y-%m-%d %H:%M:%S} to {to_date:%Y-%m-%d %H:%M:%S}")

                    # Iterate from newest to oldest so we can stop once messages are older than from_date.
                    async for msg in client.iter_messages(entity, offset_date=to_date, reverse=False, limit=MAX_MESSAGES_PER_CHANNEL):
                        if not msg.date:
                            continue

                        msg_date = msg.date.replace(tzinfo=None)
                        if msg_date < from_date:
                            break
                        if msg_date > to_date:
                            continue

                        batch_messages += 1
                        messages_scanned += 1
                        raw_text = (getattr(msg, "message", "") or "").strip()
                        lat, lon = extract_location_coordinates(msg)
                        if not lat or not lon:
                            lat, lon = extract_geo_from_message(msg)
                        if not raw_text and not (lat and lon):
                            continue

                        if raw_text and not looks_like_customer_record(raw_text) and not (lat and lon):
                            continue

                        sender_name = ""
                        sender_id = getattr(msg, "sender_id", None)
                        message_date = msg.date.replace(tzinfo=None) if getattr(msg, "date", None) else None

                        if (lat and lon) and not raw_text and sender_id and message_date:
                            matched_text = pop_best_candidate(
                                pending_text_records.get(sender_id, []),
                                message_date,
                                15,
                            )
                            if matched_text is not None:
                                extracted_records[matched_text["record_index"]]["Latitude"] = str(lat)
                                extracted_records[matched_text["record_index"]]["Longitude"] = str(lon)
                                extracted_records[matched_text["record_index"]]["Has_Location"] = "TRUE"
                                continue
                            pending_location_messages[sender_id].append({"date": message_date, "lat": lat, "lon": lon})
                            continue

                        try:
                            sender = await msg.get_sender()
                            first = (getattr(sender, "first_name", "") or "").strip()
                            last = (getattr(sender, "last_name", "") or "").strip()
                            sender_name = f"{first} {last}".strip() or (getattr(sender, "username", "") or "")
                        except Exception:
                            sender_name = ""

                        if is_auto_bot_sender(sender_name, sender_id):
                            emit_log(f"⏭️ Skipping auto bot sender: {sender_name or sender_id}")
                            continue

                        extracted_records.append(
                            build_output_record(
                                channel_name=channel_name,
                                sender_id=sender_id,
                                sender_name=sender_name,
                                msg=msg,
                            )
                        )
                        if sender_id and message_date and not (lat and lon):
                            matched_location = pop_best_candidate(
                                pending_location_messages.get(sender_id, []),
                                message_date,
                                15,
                            )
                            if matched_location is not None:
                                extracted_records[-1]["Latitude"] = str(matched_location["lat"])
                                extracted_records[-1]["Longitude"] = str(matched_location["lon"])
                                extracted_records[-1]["Has_Location"] = "TRUE"
                            else:
                                pending_text_records[sender_id].append({"date": message_date, "record_index": len(extracted_records) - 1})
                        records_extracted += 1
                        batch_records += 1

                        # Stop if we've found enough records in this channel
                        if batch_records >= MAX_RECORDS_PER_CHANNEL:
                            break

                    if progress_callback:
                        progress_callback(int((idx / max(len(channel_targets), 1)) * 75), f"✓ {channel_name}: {batch_records} records")
                    emit_log(f"✅ Done: {batch_messages} messages → {batch_records} customer records")

                except Exception as exc:
                    errors += 1
                    error_details.append(f"{channel_url}: {type(exc).__name__}: {str(exc)[:100]}")
                    if progress_callback:
                        progress_callback(int((idx / max(len(channel_targets), 1)) * 75), f"⚠️ {type(exc).__name__}")
                    emit_log(f"⚠️ Channel error: {type(exc).__name__}: {str(exc)[:160]}")

            new_records = max(records_extracted - duplicates, 0)

            if progress_callback:
                progress_callback(100, "Finalizing results")

            emit_log("")
            emit_log("🚀 PUSHING DATA TO GOOGLE SHEETS....")

            return {
                "messages_scanned": messages_scanned,
                "records_extracted": records_extracted,
                "new_records": new_records,
                "duplicates": duplicates,
                "invalid_records": max(records_extracted - new_records, 0),
                "errors": errors,
                "error_details": error_details,
                "records": extracted_records,
                "processing_time": format_duration(start_time),
                "status": "Completed" if errors == 0 else "Completed with warnings",
            }
    except RuntimeError as e:
        # Re-raise RuntimeError (auth/timeout issues) so it's shown to user
        raise e
    except Exception as e:
        # Catch any other exceptions from the async context
        return {
            "messages_scanned": 0,
            "records_extracted": 0,
            "new_records": 0,
            "duplicates": 0,
            "invalid_records": 0,
            "errors": 1,
            "error_details": [f"Telegram connection error: {str(e)[:200]}"],
            "records": [],
            "processing_time": format_duration(start_time),
            "status": "Failed",
        }


def get_google_worksheet():
    """Connect to the configured Google Sheet/worksheet and return the worksheet handle."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = get_google_service_account_credentials(scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    return spreadsheet.worksheet(WORKSHEET_NAME)


def push_records_to_sheet(records: list[dict], log_callback: Optional[Callable[[str], None]] = None) -> dict:
    """
    Push scraped records to Google Sheets WITHOUT deleting existing data.

    Flow: read existing sheet -> build unique keys -> compare each new
    record -> skip duplicates, append only genuinely new records.
    """
    try:
        if not records:
            return {
                "success": True,
                "inserted_rows": 0,
                "duplicate_rows": 0,
                "total_existing_rows": 0,
                "total_rows_after": 0,
                "sheet_status": "updated",
                "worksheet_name": WORKSHEET_NAME,
                "message": "No records found to upload.",
            }

        warnings = []
        for row_index, record in enumerate(records, start=1):
            if not str(record.get("Loan_Type", "")).strip():
                warnings.append(f"⚠️ Validation warning row {row_index}: Loan Type is empty")

        if log_callback:
            for warning in warnings[:20]:
                log_callback(warning)
            if len(warnings) > 20:
                log_callback(f"⚠️ Validation warning output truncated: {len(warnings) - 20} more rows")

        if log_callback:
            log_callback("⚙️ Starting Google Sheets authentication...")

        df_new = pd.DataFrame(records)
        for col in OUTPUT_COLUMNS:
            if col not in df_new.columns:
                df_new[col] = ""
        df_new = df_new[OUTPUT_COLUMNS]
        df_new = sanitize_dataframe_for_sheets(df_new)

        worksheet = get_google_worksheet()
        ensure_sheet_headers(worksheet)

        existing_values = worksheet.get_all_values()
        if not existing_values or len(existing_values) == 1:
            existing_df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        else:
            headers = existing_values[0]
            data_rows = existing_values[1:]
            existing_df = pd.DataFrame(data_rows, columns=headers)
            for col in OUTPUT_COLUMNS:
                if col not in existing_df.columns:
                    existing_df[col] = ""
            existing_df = existing_df[OUTPUT_COLUMNS]

        existing_keys = set()
        for _, row in existing_df.iterrows():
            key = record_key(row.to_dict())
            if key:
                existing_keys.add(key)

        new_rows = []
        current_run_keys = set()
        duplicate_count = 0
        skipped_bot_rows = 0

        for _, row in df_new.iterrows():
            new_record = row.to_dict()
            sender_name = str(new_record.get("Sender_Name", "") or "").strip()
            if is_auto_bot_sender(sender_name, new_record.get("Sender_ID")):
                skipped_bot_rows += 1
                continue

            key = record_key(new_record)

            if key in existing_keys or key in current_run_keys:
                duplicate_count += 1
                continue

            new_rows.append([new_record.get(col, "") for col in OUTPUT_COLUMNS])
            current_run_keys.add(key)

        inserted_count = 0
        if new_rows:
            worksheet.append_rows(new_rows, value_input_option="RAW")
            inserted_count = len(new_rows)

        if log_callback:
            log_callback(f"✅ Pushed {inserted_count} rows to Google Sheets (Worksheet: {WORKSHEET_NAME}) at {datetime.now():%Y-%m-%d %H:%M:%S}")
            if skipped_bot_rows:
                log_callback(f"⏭️ Skipped {skipped_bot_rows} row(s) from BP_bot before upload")

        existing_count = len(existing_df)
        total_after = existing_count + inserted_count

        return {
            "success": True,
            "inserted_rows": inserted_count,
            "duplicate_rows": duplicate_count,
            "total_existing_rows": existing_count,
            "total_rows_after": total_after,
            "sheet_status": "updated",
            "worksheet_name": worksheet.title,
            "message": (
                f"Google Sheet updated successfully. "
                f"Added {inserted_count} new records. "
                f"Skipped {duplicate_count} duplicate records."
                f"{' and ' if skipped_bot_rows else ''}{skipped_bot_rows} bot records removed."
            ),
            "warnings": warnings,
        }

    except Exception as e:
        return {
            "success": False,
            "inserted_rows": 0,
            "duplicate_rows": 0,
            "total_existing_rows": 0,
            "total_rows_after": 0,
            "sheet_status": "not_connected",
            "worksheet_name": WORKSHEET_NAME,
            "message": f"Failed to update Google Sheets: {str(e)}",
        }


def normalize_live_sheet_for_dashboard(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Google Sheet columns into the dashboard-friendly field names used by analytics and filters."""
    if raw_df is None:
        return pd.DataFrame()

    normalized_df = raw_df.copy()
    if normalized_df.empty:
        return normalized_df

    def pick_column(*candidates: str):
        for candidate in candidates:
            if candidate in normalized_df.columns:
                return candidate
        return None

    def assign_text_column(target: str, *candidates: str) -> None:
        source_column = pick_column(*candidates)
        if source_column:
            normalized_df[target] = normalized_df[source_column].fillna("").astype(str).str.strip()
        else:
            normalized_df[target] = ""

    assign_text_column("Customer Name", "Customer Name", "Name", "Sender_Name", "Sender Name", "CustomerName")
    assign_text_column("Phone Number", "Phone Number", "Tel", "Telephone", "Phone", "Phone_Number")
    assign_text_column("Telegram Channel", "Telegram Channel", "Source_Channel", "Channel", "Source", "Source Channel")
    assign_text_column("Business Type", "Business Type", "Business", "BusinessType", "Business_Type")
    assign_text_column("Status", "Status", "Customer Status", "Status_", "Outcome")
    assign_text_column("Potential_Level", "Potential_Level", "Potential Level", "Potential H/M/L", "Potential_H_M_L", "Potential")
    assign_text_column("Potential_Product", "Potential_Product", "Potential Product", "PotentialProduct", "Product Type", "Product_Type")
    assign_text_column("Bank", "Bank", "Competitor Bank", "Competitor_Bank", "Bank_Name")

    message_date_column = pick_column("Message Date", "Message_Date", "Date", "Created At")
    if message_date_column:
        normalized_df["Message Date"] = pd.to_datetime(normalized_df[message_date_column], errors="coerce")
    else:
        normalized_df["Message Date"] = pd.Series([pd.NaT] * len(normalized_df))

    return normalized_df.replace({pd.NA: "", None: ""}).copy()


def get_live_google_sheet_records() -> pd.DataFrame:
    """Read the configured worksheet without renaming or dropping its columns."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = get_google_service_account_credentials(scope)
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
    return pd.DataFrame(worksheet.get_all_records()).replace({pd.NA: "", None: ""})


def get_live_customer_records() -> pd.DataFrame:
    """Read the live Google Sheet and normalize the fields used in dashboard summaries."""
    raw_df = get_live_google_sheet_records()
    if raw_df.empty:
        return pd.DataFrame(columns=["Customer Name", "Phone Number", "Telegram Channel", "Message Date", "Business Type", "Status"])

    normalized_df = normalize_live_sheet_for_dashboard(raw_df)
    return normalized_df[
        [
            "Customer Name",
            "Phone Number",
            "Telegram Channel",
            "Message Date",
            "Business Type",
            "Status",
            "Potential_Level",
            "Potential_Product",
            "Bank",
        ]
    ].copy().replace({pd.NA: "", None: ""})


def run_scrape_job(selected_channels, from_date, to_date, progress_callback=None, log_callback=None) -> dict:
    result = asyncio.run(
        scrape_channels(
            selected_channels=selected_channels,
            from_date=from_date,
            to_date=to_date,
            progress_callback=progress_callback,
            log_callback=log_callback,
        )
    )

    try:
        sheet_result = push_records_to_sheet(result.get("records", []), log_callback=log_callback)
        result["warnings"] = sheet_result.get("warnings", [])
        result["new_records"] = int(sheet_result.get("inserted_rows", 0))
        result["duplicates"] = int(sheet_result.get("duplicate_rows", 0))
        result["invalid_records"] = max(int(result.get("records_extracted", 0)) - int(result.get("new_records", 0)), 0)
        result["sheet_status"] = sheet_result.get("sheet_status", "updated")
        result["worksheet_name"] = sheet_result.get("worksheet_name", WORKSHEET_NAME)
    except Exception:
        result["sheet_status"] = "not_connected"

    result.pop("records", None)
    return result