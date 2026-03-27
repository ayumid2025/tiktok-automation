#!/usr/bin/env python3
import os
import sys
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
import openai

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'tiktok')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'securepassword')
DB_NAME = os.getenv('DB_NAME', 'tiktok_automation')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

def get_db_conn():
    return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)

def log_comment_reply(account, video_id, comment_text, reply_text):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO comments (account, video_id, comment_text, reply_text, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (account, video_id, comment_text, reply_text, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def generate_reply(comment_text):
    if not OPENAI_API_KEY:
        return "Thanks for watching! 🚀"
    prompt = f"Reply to this TikTok comment in a short, friendly, and engaging way (max 100 characters): {comment_text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Thanks for watching! 🚀"

def get_latest_video_id(driver, account):
    """Navigate to profile and get the latest video's ID."""
    driver.get(f"https://www.tiktok.com/@{account}")
    time.sleep(3)
    first_video = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/video/']"))
    )
    video_url = first_video.get_attribute("href")
    video_id = video_url.split("/video/")[-1].split("?")[0]
    return video_id

def main():
    if len(sys.argv) < 2:
        print("Usage: python comment_bot.py <account>")
        sys.exit(1)
    account = sys.argv[1]

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

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

    video_id = get_latest_video_id(driver, account)
    driver.get(f"https://www.tiktok.com/@{account}/video/{video_id}")
    time.sleep(4)

    # Scroll to load comments
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # Find all comment items (adjust selector as needed)
    comments = driver.find_elements(By.CSS_SELECTOR, "[data-e2e='comment-item']")
    for comment in comments:
        try:
            # Check if already replied (look for reply button)
            reply_btn = comment.find_element(By.CSS_SELECTOR, "[data-e2e='comment-reply']")
            # Get comment text
            comment_text_elem = comment.find_element(By.CSS_SELECTOR, "[data-e2e='comment-text']")
            comment_text = comment_text_elem.text

            reply_text = generate_reply(comment_text)
            print(f"Replying to '{comment_text}' with: {reply_text}")

            reply_btn.click()
            time.sleep(1)
            textarea = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder='Add a reply...']"))
            )
            textarea.send_keys(reply_text)
            send_btn = driver.find_element(By.CSS_SELECTOR, "[data-e2e='reply-send']")
            send_btn.click()
            time.sleep(random.uniform(2, 4))

            # Log to DB
            log_comment_reply(account, video_id, comment_text, reply_text)

        except Exception as e:
            # Probably already replied or no reply button
            continue

    driver.quit()

if __name__ == "__main__":
    main()
