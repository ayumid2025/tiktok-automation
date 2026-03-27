#!/usr/bin/env python3
import os
import sys
import time
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'tiktok')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'securepassword')
DB_NAME = os.getenv('DB_NAME', 'tiktok_automation')

def get_db_conn():
    return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)

def get_competitors(account):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT competitor_username FROM competitors WHERE account = %s", (account,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows]

def store_target(account, competitor, target_username, engagement_type):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO target_users (account, competitor_username, target_username, engagement_type)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (account, target_username) DO NOTHING
    """, (account, competitor, target_username, engagement_type))
    conn.commit()
    cur.close()
    conn.close()

def scrape_competitor(driver, account, competitor):
    driver.get(f"https://www.tiktok.com/@{competitor}")
    time.sleep(3)
    # Click on the first video
    try:
        first_video = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='/video/']"))
        )
        first_video.click()
        time.sleep(3)
    except:
        return

    # Scroll to load comments
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # Get comment usernames
    comment_usernames = driver.find_elements(By.CSS_SELECTOR, "[data-e2e='comment-username']")
    for username_elem in comment_usernames:
        username = username_elem.text.strip()
        if username:
            store_target(account, competitor, username, 'comment')
            print(f"Added {username} from {competitor}")

    # Optionally, you could also scrape likers by clicking the like button and scrolling
    # but that's more complex.

    driver.back()
    time.sleep(2)

def main():
    if len(sys.argv) < 2:
        print("Usage: python target_scraper.py <account>")
        sys.exit(1)
    account = sys.argv[1]

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    # Load cookies (required to access TikTok without being blocked)
    cookies_path = f"/accounts/{account}/cookies.txt"
    driver.get("https://www.tiktok.com")
    with open(cookies_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split("\t")
                if len(parts) == 7:
                    driver.add_cookie({
                        "domain": parts[0],
                        "name": parts[5],
                        "value": parts[6],
                        "path": parts[2],
                        "secure": parts[3] == "TRUE",
                        "httpOnly": parts[4] == "TRUE"
                    })
    driver.refresh()
    time.sleep(3)

    competitors = get_competitors(account)
    for competitor in competitors:
        scrape_competitor(driver, account, competitor)

    driver.quit()

if __name__ == "__main__":
    main()
