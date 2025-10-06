from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime, timedelta

# --- 1. Set up Selenium ---
options = Options()
options.add_argument("--headless")   # run without opening a window
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# --- 2. Go to the events page ---
driver.get("https://www.bccenter.org/events")
driver.implicitly_wait(5)  # wait for JS to load

# --- 3. Grab event containers (adjust selector as needed) ---
events = driver.find_elements(By.CSS_SELECTOR, ".event-listing")

data = []
for event in events:
    try:
        title = event.find_element(By.CSS_SELECTOR, ".event-title").text
    except:
        title = None
    
    try:
        date_text = event.find_element(By.CSS_SELECTOR, ".event-date").text
    except:
        date_text = None
    
    data.append({"title": title, "date_text": date_text})

driver.quit()

# --- 4. Put into dataframe ---
df = pd.DataFrame(data)

# --- 5. Parse dates (adjust parsing depending on format seen) ---
def parse_dates(date_str):
    # Example: "January 10-12, 2024" → expand into full list of days
    if date_str is None:
        return []
    date_str = date_str.replace(",", "")
    parts = date_str.split()
    try:
        month = parts[0]
        days = parts[1]
        year = parts[-1]
        
        if "-" in days:
            start_day, end_day = days.split("-")
            start = datetime.strptime(f"{month} {start_day} {year}", "%B %d %Y")
            end = datetime.strptime(f"{month} {end_day} {year}", "%B %d %Y")
            return [start + timedelta(days=i) for i in range((end-start).days + 1)]
        else:
            return [datetime.strptime(f"{month} {days} {year}", "%B %d %Y")]
    except:
        return []

# Expand event dates
all_dates = []
for _, row in df.iterrows():
    for d in parse_dates(row["date_text"]):
        all_dates.append(d.date())

# --- 6. Build 2024 calendar ---
calendar_2024 = pd.DataFrame({
    "date": pd.date_range("2024-01-01", "2024-12-31", freq="D")
})
calendar_2024["Baltimore Convention Center"] = calendar_2024["date"].apply(
    lambda d: 1 if d in all_dates else 0
)

print(calendar_2024.head(20))
