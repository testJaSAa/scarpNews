
SUPABASE_URL = "https://jntrovvbeuscfjkfsqxo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpudHJvdnZiZXVzY2Zqa2ZzcXhvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTg1OTI4MiwiZXhwIjoyMDcxNDM1MjgyfQ.dCWOlORWdhuGpwlMRIMEM3qR0UVAxTipXwfPkhl6o_U"

# ----------------- Timezones -----------------
TARGET_TIMEZONE = "Asia/Tehran"
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
