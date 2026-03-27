import os
import sys
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import openai

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

def log_comment_reply(account, video_id, comment_text, reply_text):
    conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO comments (account, video_id, comment_text, reply_text)
        VALUES (%s, %s, %s, %s)
    """, (account, video_id, comment_text, reply_text))
    conn.commit()
    cur.close()
    conn.close()

def generate_ai_reply(comment):
    if not OPENAI_API_KEY:
        return "Thanks for watching! 🚀"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Reply to this TikTok comment in a friendly, short way: {comment}"}],
            max_tokens=60,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except:
        return "Thanks for watching! 🚀"

def main():
    if len(sys.argv) < 2:
        print("Usage: python comment_bot.py <account>")
        sys.exit(1)
    account = sys.argv[1]

    # Setup browser and cookies (same as streak_bot)
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

    # 1. Go to latest video (or specified URL)
    # 2. Find unreplied comments
    # 3. For each, generate reply and send
    # 4. Log in database

    driver.quit()

if __name__ == "__main__":
    main()
