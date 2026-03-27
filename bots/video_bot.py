#!/usr/bin/env python3
import os
import sys
import time
import random
import subprocess
import psycopg2
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Database connection
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'tiktok')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'securepassword')
DB_NAME = os.getenv('DB_NAME', 'tiktok_automation')

def get_db_conn():
    return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)

def log_video(account, video_url):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO videos (account, video_url, uploaded_at) VALUES (%s, %s, %s)",
                (account, video_url, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def generate_video(account):
    """Run the Benoitvrm AI video generator."""
    # Assume Benoitvrm is installed at /app/Benoitvrm (mounted from host)
    script_path = "/bots/video_generation/main.py"  # adjust to your actual path
    output_dir = f"/accounts/{account}/output_videos"
    os.makedirs(output_dir, exist_ok=True)
    cmd = [sys.executable, script_path, "--mode", "once", "--output", output_dir]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Find the generated video file (usually video_1.mp4)
        video_file = os.path.join(output_dir, "video_1.mp4")
        if os.path.exists(video_file):
            return video_file
        else:
            raise Exception("Video not generated")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Video generation failed: {e.stderr}")

def upload_video(driver, video_path, account):
    """Upload video using Selenium."""
    driver.get("https://www.tiktok.com/upload")
    time.sleep(3)

    # Wait for file input
    file_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
    )
    file_input.send_keys(video_path)
    time.sleep(5)  # wait for upload to start

    # Wait for upload to finish (progress bar disappears)
    WebDriverWait(driver, 60).until(
        EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-e2e='upload-progress']"))
    )

    # Optionally add a caption (you can generate one)
    caption_input = driver.find_element(By.CSS_SELECTOR, "[data-e2e='caption-textarea']")
    caption_input.send_keys(f"Check out this AI-generated video! #fyp #ai")

    # Click post
    post_btn = driver.find_element(By.CSS_SELECTOR, "[data-e2e='post-button']")
    post_btn.click()
    time.sleep(5)

    # Get video URL from the resulting page
    video_url = driver.current_url
    return video_url

def main():
    if len(sys.argv) < 2:
        print("Usage: python video_bot.py <account>")
        sys.exit(1)
    account = sys.argv[1]

    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1080,1920")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    # Load cookies
    cookies_path = f"/accounts/{account}/cookies.txt"
    if not os.path.exists(cookies_path):
        print("Cookies file not found")
        sys.exit(1)
    driver.get("https://www.tiktok.com")
    with open(cookies_path, "r") as f:
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

    # Generate video
    video_path = generate_video(account)
    print(f"Video generated: {video_path}")

    # Upload
    video_url = upload_video(driver, video_path, account)
    print(f"Uploaded: {video_url}")

    # Log to database
    log_video(account, video_url)

    driver.quit()

if __name__ == "__main__":
    main()
