import time
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pytz
import urllib.request
from config import TARGET_TIMEZONE, SUPABASE_URL, SUPABASE_KEY
import os

# Set the timezone to UTC for consistent scraping
os.environ['TZ'] = 'UTC'
time.tzset()

ALLOWED_ELEMENT_TYPES = {
    "calendar__date": "date",
    "calendar__time": "time",
    "calendar__impact": "impact",
    "calendar__event": "event",
    "calendar__detail": "link"
}

SCRAPER_TIMEZONE = None

# --------------------- مرورگر ---------------------
def init_driver(headless=True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("window-size=1920x1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def scroll_to_end(driver):
    prev_pos = None
    while True:
        current_pos = driver.execute_script("return window.pageYOffset;")
        driver.execute_script("window.scrollTo(0, window.pageYOffset + 500);")
        time.sleep(1)
        if current_pos == prev_pos:
            break
        prev_pos = current_pos

# --------------------- زمان ---------------------
def convert_time_zone(date_str, time_str, from_zone_str, to_zone_str):
    if not date_str or not time_str:
        return time_str
    if time_str.lower() in ["all day", "tentative"]:
        return time_str
    try:
        from_zone = pytz.timezone(from_zone_str)
        to_zone = pytz.timezone(to_zone_str)
        naive_dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %I:%M%p")
        localized_dt = from_zone.localize(naive_dt)
        converted_dt = localized_dt.astimezone(to_zone)
        return converted_dt.strftime("%H:%M")
    except:
        return time_str

# --------------------- Supabase ---------------------
def insert_to_supabase(data):
    if not data:
        print("[WARNING] No data to insert into Supabase.")
        return
    for row in data:
        if row.get("date"):
            try:
                dt = datetime.strptime(row["date"], "%d/%m/%Y")
                row["date"] = dt.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"[WARNING] Failed to parse date '{row.get('date')}': {e}")
        for key in ["day", "time", "impact", "event", "link", "additional_details"]:
            if key not in row:
                row[key] = ""

    table_name = "forex_calendar"
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=json_data, method='POST')
    for key, value in headers.items():
        req.add_header(key, value)

    try:
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 201]:
                print(f"[INFO] {len(data)} rows successfully inserted in Supabase.")
                print("[INFO] Sample data inserted:", data[0])
            else:
                print(f"[ERROR] Unexpected response status: {response.status}")
    except Exception as e:
        print(f"[ERROR] Failed to insert into Supabase: {e}")
        print("[DEBUG] Data attempted to insert:", json.dumps(data, indent=2))

def update_to_supabase(table_id, update_data):
    if not update_data:
        print("[WARNING] No data to update in Supabase.")
        return

    table_name = "forex_calendar"
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?id=eq.{table_id}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    json_data = json.dumps(update_data).encode('utf-8')
    req = urllib.request.Request(url, data=json_data, method='PATCH')
    for key, value in headers.items():
        req.add_header(key, value)

    try:
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 204]:
                print(f"[INFO] Row with id {table_id} successfully updated in Supabase.")
            else:
                print(f"[ERROR] Unexpected response status: {response.status}")
    except Exception as e:
        print(f"[ERROR] Failed to update Supabase: {e}")
        print("[DEBUG] Data attempted to update:", json.dumps(update_data, indent=2))

def fetch_today_schedule():
    table_name = "forex_calendar"
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?date=eq.{today}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    req = urllib.request.Request(url, method="GET")
    for k,v in headers.items():
        req.add_header(k,v)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            schedule = []
            now_time = datetime.now()
            for row in data:
                time_str = row.get("time")
                if time_str and time_str.lower() not in ["all day", "tentative"]:
                    dt = datetime.strptime(f"{row['date']} {time_str}", "%Y-%m-%d %H:%M")
                    if dt > now_time:
                        schedule.append({"id": row.get("id"), "time": dt, "link": row.get("link")})
            return schedule
    except Exception as e:
        print(f"[ERROR] Failed to fetch schedule: {e}")
        return []

# --------------------- اسکرپ کل روز ---------------------
def scrape_full_day(day_param, year):
    month_str = day_param[:3]
    day_num = int(day_param[3:day_param.rfind('.')])
    year = int(day_param[day_param.rfind('.')+1:])
    month = datetime.strptime(month_str.capitalize(), "%b").month
    current_date = f"{day_num:02d}/{month:02d}/{year}"
    current_day = datetime(year, month, day_num).strftime("%a")

    url = f"https://www.forexfactory.com/calendar?day={day_param}"
    driver = init_driver()
    driver.get(url)
    time.sleep(3)
    global SCRAPER_TIMEZONE
    SCRAPER_TIMEZONE = driver.execute_script("return Intl.DateTimeFormat().resolvedOptions().timeZone")
    scroll_to_end(driver)

    try:
        table = driver.find_element(By.CLASS_NAME, "calendar__table")
        print("[DEBUG] Calendar table found.")
    except Exception as e:
        print(f"[ERROR] Failed to find calendar table: {e}")
        driver.quit()
        return []

    rows = table.find_elements(By.TAG_NAME, "tr")
    print(f"[DEBUG] Number of rows found: {len(rows)}")

    data = []
    current_time = ""
    temp_data = []

    for row in rows:
        row_data = {}
        event_id = row.get_attribute("data-event-id")
        for element in row.find_elements(By.TAG_NAME, "td"):
            class_name = element.get_attribute("class")
            class_list = class_name.split()
            key = None
            for cls in class_list:
                if cls in ALLOWED_ELEMENT_TYPES:
                    key = ALLOWED_ELEMENT_TYPES[cls]
                    break
            if key:
                if key == "impact":
                    impacts = element.find_elements(By.TAG_NAME, "span")
                    if impacts:
                        title = impacts[0].get_attribute("title")
                        row_data["impact"] = title if title else ""
                elif key == "link" and event_id:
                    row_data["link"] = f"https://www.forexfactory.com/calendar?day={day_param}#detail={event_id}"
                else:
                    row_data[key] = element.text.strip() if element.text else ""
        if "time" in row_data:
            current_time = row_data["time"]
        if row_data and "event" in row_data:
            row_data["day"] = current_day
            row_data["date"] = current_date
            if SCRAPER_TIMEZONE and TARGET_TIMEZONE:
                row_data["time"] = convert_time_zone(current_date, current_time, SCRAPER_TIMEZONE, TARGET_TIMEZONE)
            else:
                row_data["time"] = current_time
            print("[DEBUG] Collected row_data:", row_data)
            temp_data.append((row_data, event_id, row))

    for row_data, event_id, row_element in temp_data:
        if event_id:
            try:
                event_cell = row_element.find_element(By.CLASS_NAME, "calendar__event")
                driver.execute_script("arguments[0].click();", event_cell)
                time.sleep(2)
                expanded_row = driver.find_element(By.CSS_SELECTOR, "tr.calendar__row--expanded")
                row_data["additional_details"] = expanded_row.text
                driver.execute_script("arguments[0].click();", event_cell)
                time.sleep(1)
            except Exception as e:
                print(f"[WARNING] Failed to expand details for event {event_id}: {e}")
                row_data["additional_details"] = ""
        data.append(row_data)

    insert_to_supabase(data)
    driver.quit()
    return data

# --------------------- اسکرپ جزئیات خبر ---------------------
def scrape_news_details(news_link, table_id):
    driver = init_driver()
    driver.get(news_link)
    time.sleep(2)
    try:
        event_row = driver.find_element(By.CSS_SELECTOR, "tr.calendar__row--expanded")
        details = event_row.text
        print(f"[INFO] Scraped details for table id {table_id}")
        update_to_supabase(table_id, {"additional_details": details})
    except Exception as e:
        print(f"[WARNING] Failed to scrape news details: {e}")
    driver.quit()

# --------------------- Scheduler چند روز ---------------------
def scheduler_multi_days(days=3):
    print(f"[INFO] Scheduler for {days} days started...")
    for day_offset in range(days):
        target_date = datetime.now() + timedelta(days=day_offset)
        day_param = target_date.strftime("%b%d.%Y").lower()
        year = target_date.year
        print(f"[INFO] Scraping full day news for {day_param}...")
        scrape_full_day(day_param, year)

    print("[INFO] Starting live scheduler for today's upcoming news...")
    while True:
        schedule = fetch_today_schedule()
        now = datetime.now()
        for item in schedule:
            if abs((item["time"] - now).total_seconds()) < 60:
                print(f"[INFO] Scraping scheduled news: {item['link']}")
                scrape_news_details(item["link"], item["id"])
        time.sleep(30)

# --------------------- Main ---------------------
if __name__ == "__main__":
    scheduler_multi_days(days=3)