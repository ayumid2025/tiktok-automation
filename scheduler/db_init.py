import psycopg2
import os

def init_db():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'tiktok'),
        password=os.getenv('DB_PASSWORD', 'securepassword'),
        dbname=os.getenv('DB_NAME', 'tiktok_automation')
    )
    cur = conn.cursor()

    # Videos table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id SERIAL PRIMARY KEY,
            account VARCHAR(50) NOT NULL,
            video_url TEXT,
            views INTEGER,
            likes INTEGER,
            comments INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Comments table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            account VARCHAR(50) NOT NULL,
            video_id INTEGER REFERENCES videos(id),
            comment_text TEXT,
            reply_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Streak DMs table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS streak_messages (
            id SERIAL PRIMARY KEY,
            account VARCHAR(50) NOT NULL,
            target_user VARCHAR(50) NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Follows/Unfollows table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS follows (
            id SERIAL PRIMARY KEY,
            account VARCHAR(50) NOT NULL,
            target_user VARCHAR(50) NOT NULL,
            action VARCHAR(10) NOT NULL,
            performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Competitors table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id SERIAL PRIMARY KEY,
            account VARCHAR(50) NOT NULL,
            competitor_username VARCHAR(50) NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Target users from competitors
    cur.execute("""
        CREATE TABLE IF NOT EXISTS target_users (
            id SERIAL PRIMARY KEY,
            account VARCHAR(50) NOT NULL,
            competitor_username VARCHAR(50) NOT NULL,
            target_username VARCHAR(50) NOT NULL,
            engagement_type VARCHAR(10),
            followed BOOLEAN DEFAULT FALSE,
            found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            followed_at TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()
