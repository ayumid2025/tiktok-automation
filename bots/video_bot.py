import os
import sys
import subprocess
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def log_video(account, video_url):
    conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO videos (account, video_url) VALUES (%s, %s)", (account, video_url))
    conn.commit()
    cur.close()
    conn.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python video_bot.py <account> [--mode mode]")
        sys.exit(1)
    account = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'once'

    # 1. Run the AI video generation (Benoitvrm) – adapt to your actual script.
    # For demonstration, we simulate a video being generated.
    # Replace with actual call to your existing video generation script.
    video_path = f"/accounts/{account}/output_videos/video_1.mp4"
    # (Assume generation happens here)

    # 2. Upload the video using Selenium (or API) and get video URL.
    video_url = f"https://www.tiktok.com/@{account}/video/123456789"

    # 3. Log to database
    log_video(account, video_url)
    print(f"Video uploaded for {account}: {video_url}")

if __name__ == "__main__":
    main()
