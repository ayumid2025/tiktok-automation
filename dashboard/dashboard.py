import os
import psycopg2
from flask import Flask, render_template, jsonify

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'tiktok')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'securepassword')
DB_NAME = os.getenv('DB_NAME', 'tiktok_automation')

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    conn = get_db_connection()
    cur = conn.cursor()

    # Last 7 days: video uploads per day
    cur.execute("""
        SELECT DATE(uploaded_at) as day, COUNT(*)
        FROM videos
        WHERE uploaded_at > NOW() - INTERVAL '7 days'
        GROUP BY day
        ORDER BY day
    """)
    video_data = cur.fetchall()

    # Last 7 days: follows per day
    cur.execute("""
        SELECT DATE(performed_at) as day, COUNT(*)
        FROM follows
        WHERE action = 'follow' AND performed_at > NOW() - INTERVAL '7 days'
        GROUP BY day
        ORDER BY day
    """)
    follow_data = cur.fetchall()

    # Last 7 days: streaks sent per day
    cur.execute("""
        SELECT DATE(sent_at) as day, COUNT(*)
        FROM streak_messages
        WHERE sent_at > NOW() - INTERVAL '7 days'
        GROUP BY day
        ORDER BY day
    """)
    streak_data = cur.fetchall()

    cur.close()
    conn.close()

    def format_chart_data(data):
        labels = [str(row[0]) for row in data]
        values = [row[1] for row in data]
        return {'labels': labels, 'values': values}

    return jsonify({
        'videos': format_chart_data(video_data),
        'follows': format_chart_data(follow_data),
        'streaks': format_chart_data(streak_data)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
