import os
import sys
import json
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def log_streak(account, target_user):
    conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO streak_messages (account, target_user) VALUES (%s, %s)", (account, target_user))
    conn.commit()
    cur.close()
    conn.close()

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
    # (Insert actual streak sending logic here)
    # For each target in config['TARGET_USERS']:
    #   ... send message ...

    # Log each sent DM
    for user in config.get("TARGET_USERS", []):
        log_streak(account, user)

    driver.quit()

if __name__ == "__main__":
    main()
