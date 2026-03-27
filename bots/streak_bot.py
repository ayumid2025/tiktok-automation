#!/usr/bin/env python3
import os
import sys
import json
import time
import random
import psycopg2
from datetime import datetime
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

def log_streak(account, target_user):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO streak_messages (account, target_user, sent_at) VALUES (%s, %s, %s)",
                (account, target_user, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def send_dm(driver, username, message):
    """Send a DM to a user. Assumes we are already logged in."""
    driver.get(f"https://www.tiktok.com/@{username}")
    time.sleep(2)

    # Click message button (if present)
    try:
        msg_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Message')]"))
        )
        msg_btn.click()
        time.sleep(1)

        # In the chat window, type and send
        textarea = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='chat-input']"))
        )
        textarea.send_keys(message)
        send_btn = driver.find_element(By.CSS_SELECTOR, "[data-e2e='chat-send']")
        send_btn.click()
        time.sleep(random.uniform(1, 3))
        return True
    except Exception as e:
        print(f"Could not send DM to {username}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python streak_bot.py <account>")
        sys.exit(1)
    account = sys.argv[1]
    config_path = f"/accounts/{account}/config.json"
    if not os.path.exists(config_path):
        print(f"Config file not found for {account}")
        sys.exit(1)
    with open(config_path) as f:
        config = json.load(f)

    # Setup headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    # Load cookies
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

    message = config.get("MESSAGE_TO_SEND", ".")
    for target in config.get("TARGET_USERS", []):
        print(f"Sending streak to {target}")
        success = send_dm(driver, target, message)
        if success:
            log_streak(account, target)
        time.sleep(random.uniform(30, 60))  # be gentle

    driver.quit()

if __name__ == "__main__":
    main()
