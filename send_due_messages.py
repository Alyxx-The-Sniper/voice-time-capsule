import argparse
import sqlite3
from datetime import date, datetime
from utils import db_utils, email_utils
import sys

def get_due_messages(today: str) -> list[dict]:
    from utils.db_utils import DB_PATH

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM messages WHERE delivery_date = ? AND delivered_at IS NULL", (today,))
        rows = c.fetchall()
        return [dict(row) for row in rows]

def run_scheduler(due_messages: list[dict], deliver: bool):
    today = date.today().isoformat()
    print(f"📬 {len(due_messages)} message(s) scheduled for {today}")

    if not deliver:
        print("❌ Delivery cancelled. No emails sent.")
        return

    with sqlite3.connect(db_utils.DB_PATH) as conn:
        c = conn.cursor()
        for msg in due_messages:
            token = msg["token"]
            email = msg["email"]
            email_utils.send_delivery_email(email, token)
            print(f"✅ Sent message to {email} (token: {token})")
            delivered_time = datetime.utcnow().isoformat()
            c.execute("UPDATE messages SET delivered_at = ? WHERE token = ?", (delivered_time, token))
        conn.commit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deliver scheduled messages.")
    parser.add_argument('-y', '--yes', action='store_true', help="Deliver messages without prompt.")
    parser.add_argument('-n', '--no', action='store_true', help="Do not deliver messages.")
    args = parser.parse_args()

    today = date.today().isoformat()
    due_messages = get_due_messages(today)
    print(f"📬 {len(due_messages)} message(s) scheduled for {today}")

    if len(due_messages) == 0:
        print("No messages to deliver today.")
        sys.exit(0)

    if args.yes:
        proceed = True
    elif args.no:
        proceed = False
    else:
        ans = input("Do you want to deliver scheduled messages? (y/n): ").strip().lower()
        proceed = (ans == 'y')

    run_scheduler(due_messages, proceed)
