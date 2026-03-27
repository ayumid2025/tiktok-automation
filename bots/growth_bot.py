#!/usr/bin/env python3
import os
import sys
import time
import random
import psycopg2
from datetime import datetime, timedelta
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

DAILY_FOLLOW_LIMIT = 20
UNFOLLOW_AFTER_DAYS = 3
DELAY_BETWEEN_ACTIONS = (30, 90)

def get_db_conn():
    return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)

def get_targets_to_follow(account, limit):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT target_username FROM target_users
        WHERE account = %s AND followed = FALSE
        ORDER BY found_at ASC
        LIMIT %s
    """, (account, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows]

def mark_followed(account, target_username):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE target_users
        SET followed = TRUE, followed_at = %s
        WHERE account = %s AND target_username = %s
    """, (datetime.now(), account, target_username))
    conn.commit()
    cur.close()
    conn.close()

def log_follow(account, target_username, action='follow'):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO follows (account, target_user, action, performed_at)
        VALUES (%s, %s, %s, %s)
    """, (account, target_username, action, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def get_users_to_unfollow(account):
    """Find users followed more than UNFOLLOW_AFTER_DAYS ago."""
    cutoff = datetime.now() - timedelta(days=UNFOLLOW_AFTER_DAYS)
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT target_user FROM follows
        WHERE account = %s AND action = 'follow'
          AND performed_at < %s
          AND NOT EXISTS (
            SELECT 1 FROM follows f2
            WHERE f2.account = follows.account
              AND f2.target_user = follows.target_user
              AND f2.action = 'unfollow'
          )
    """, (account, cutoff))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows]

def follow_user(driver, username):
    driver.get(f"https://www.tiktok.com/@{username}")
    time.sleep(2)
    try:
        follow_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Follow')]"))
        )
        follow_btn.click()
        time.sleep(random.uniform(1, 2))
        return True
    except Exception as e:
        print(f"Could not follow {username}: {e}")
        return False

def unfollow_user(driver, username):
    driver.get(f"https://www.tiktok.com/@{username}")
    time.sleep(2)
    try:
        following_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Following')]"))
        )
        following_btn.click()
        time.sleep(1)
        confirm_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Unfollow')]"))
        )
        confirm_btn.click()
        time.sleep(random.uniform(1, 2))
        return True
    except Exception as e:
        print(f"Could not unfollow {username}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python growth_bot.py <account>")
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

    # 1. Unfollow old users
    to_unfollow = get_users_to_unfollow(account)
    for user in to_unfollow:
        if unfollow_user(driver, user):
            log_follow(account, user, 'unfollow')
            print(f"Unfollowed {user}")
        time.sleep(random.uniform(*DELAY_BETWEEN_ACTIONS))

    # 2. Follow new targets
    targets = get_targets_to_follow(account, DAILY_FOLLOW_LIMIT)
    for user in targets:
        if follow_user(driver, user):
            mark_followed(account, user)
            log_follow(account, user, 'follow')
            print(f"Followed {user}")
        time.sleep(random.uniform(*DELAY_BETWEEN_ACTIONS))

    driver.quit()

if __name__ == "__main__":
    main()
