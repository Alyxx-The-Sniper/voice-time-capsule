import argparse
from datetime import date
from utils import db_utils, email_utils
import sys

def get_due_messages(today: str) -> list[dict]:
    # Use the existing SQLAlchemy function you already have
    return db_utils.get_due_undelivered_messages(today)

def run_scheduler(due_messages: list[dict], deliver: bool):
    today = date.today().isoformat()
    print(f"📬 {len(due_messages)} message(s) scheduled for {today}")

    if not deliver:
        print("❌ Delivery cancelled. No emails sent.")
        return

    # Use the db_utils function to mark as delivered
    for msg in due_messages:
        token = msg["token"]
        email = msg["email"]
        email_utils.send_delivery_email(email, token)
        print(f"✅ Sent message to {email} (token: {token})")
        db_utils.mark_message_delivered(token)

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
        proceed = Fals
