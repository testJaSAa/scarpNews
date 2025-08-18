
SUPABASE_URL = "https://fmvxnojvyvurdgbkrkqy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZtdnhub2p2eXZ1cmRnYmtya3F5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTUwMDkzMiwiZXhwIjoyMDcxMDc2OTMyfQ.FaJ91LxX537_OvbjJzhesRtFvtCjA1lFrT5YrqStbDA"

# ----------------- Timezones -----------------
TARGET_TIMEZONE = "UTC"
SCRAPER_TIMEZONE = None


ALLOWED_ELEMENT_TYPES = {
    "calendar__date": "date",
    "calendar__time": "time",
    "calendar__impact": "impact",
    "calendar__event": "event",
    "calendar__detail": "link",
}


ICON_COLOR_MAP = {
    "calendar__impact--high": "high",
    "calendar__impact--medium": "medium",
    "calendar__impact--low": "low",
}
