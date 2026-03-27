import os
import sys
import subprocess
import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from db_init import init_db
from telegram_notify import send_telegram

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s: %(message)s',
    handlers=[
        logging.FileHandler('/logs/automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Accounts: each subdirectory in /accounts
ACCOUNTS = [d for d in os.listdir('/accounts') if os.path.isdir(os.path.join('/accounts', d))]

# Paths to bot scripts (mounted from /bots)
BOT_SCRIPTS = {
    'video': '/bots/video_bot.py',
    'streak': '/bots/streak_bot.py',
    'comment': '/bots/comment_bot.py',
    'growth': '/bots/growth_bot.py',
    'target_scraper': '/bots/target_scraper.py'   # optional
}

def run_bot(script, account, *args):
    """Run a bot script with the given account and extra arguments."""
    cmd = [sys.executable, script, account] + list(args)
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Bot {script} for {account} succeeded: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Bot {script} for {account} failed: {e.stderr}")
        return False

def run_video_bot(account):
    return run_bot(BOT_SCRIPTS['video'], account, '--mode', 'once')

def run_streak_bot(account):
    return run_bot(BOT_SCRIPTS['streak'], account)

def run_comment_bot(account):
    return run_bot(BOT_SCRIPTS['comment'], account)

def run_growth_bot(account):
    return run_bot(BOT_SCRIPTS['growth'], account)

def run_target_scraper(account):
    return run_bot(BOT_SCRIPTS['target_scraper'], account)

def full_automation():
    send_telegram("🚀 Starting daily TikTok automation for all accounts.")
    logger.info("=== Starting full automation sequence ===")

    for account in ACCOUNTS:
        logger.info(f"Processing account: {account}")
        send_telegram(f"🤖 Processing account <b>{account}</b>")

        # 1. Video bot (generate and upload)
        video_ok = run_video_bot(account)
        if not video_ok:
            logger.warning(f"Skipping comment bot for {account} because video failed.")
        else:
            # 2. Comment bot (only if video succeeded)
            run_comment_bot(account)

        # 3. Streak bot (always)
        run_streak_bot(account)

        # 4. Target scraper (collect new users to follow)
        run_target_scraper(account)

        # 5. Growth bot (follow collected users)
        run_growth_bot(account)

    send_telegram("✅ Daily automation completed for all accounts.")
    logger.info("=== Full automation sequence complete ===\n")

if __name__ == "__main__":
    # Initialize database tables
    init_db()

    # Setup scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(full_automation, CronTrigger(hour=9, minute=0), id='daily_automation')
    scheduler.start()
    logger.info("Scheduler started. Waiting for jobs...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
