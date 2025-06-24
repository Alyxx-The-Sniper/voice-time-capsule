import os
import uuid
from dotenv import load_dotenv

# 1. Load environment variables early! 
load_dotenv()

from flask import Flask, request, render_template, Response
from utils import gpt_utils, tts_utils, db_utils, cost_tracker, email_utils, whisper_utils
from email_validator import validate_email, EmailNotValidError
from datetime import date
from sqlalchemy import create_engine
import pandas as pd
from markupsafe import Markup
from utils.s3_utils import upload_audio_to_s3
import tempfile
from functools import wraps



# 2. Database Config (WORKS for SQLite & PostgreSQL)
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
engine = create_engine(DATABASE_URL)


# 3. Init DB Tables
with app.app_context():
    db_utils.init_db()

# ---- 4. Your Routes ----
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    print("==== /submit route hit ====")
    # --- 1. Validate email ---
    raw_email = request.form.get("email", "")
    try:
        v = validate_email(raw_email, check_deliverability=True)
        email = v.email
    except EmailNotValidError as e:
        return f"❌ Invalid email address: {str(e)}", 400

    # --- 2. Rate limit by IP ---
    ip = request.remote_addr
    today = date.today().isoformat()
    if db_utils.count_submissions_by_ip(ip, today) >= 7:
        return "❌ You’ve reached the maximun submissions today. Please try again tomorrow", 429

    # --- 3. Get delivery date and audio file ---
    delivery_date = request.form.get("deliveryDate")
    audio_file = request.files.get("audio")
    if not email or not delivery_date or not audio_file:
        return "Missing form fields", 400

    token = uuid.uuid4().hex[:8]
    filename = f"{token}.webm"

    # --- 4. Save user audio to a temp file first ---
    temp_audio_path = None
    temp_tts_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
            audio_file.save(temp_audio_path)

        # --- 5. Transcribe from local temp file ---
        transcript, duration_sec = whisper_utils.transcribe(temp_audio_path)

        # --- 6. Upload the original user audio to S3 ---
        with open(temp_audio_path, "rb") as f:
            audio_url = upload_audio_to_s3(f, f"audio/{filename}")

        # --- 7. Continue with LLM and TTS pipeline ---
        reply = gpt_utils.respond_as_future_self(transcript)
        voice_id = tts_utils.upload_user_voice(name=email, audio_path=temp_audio_path)

        # --- 8. Synthesize AI voice, save to temp file ---
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tempf:
            temp_tts_path = tempf.name

        tts_utils.synthesize(reply, temp_tts_path, voice_id)

        # --- 9. Upload synthesized AI voice to S3 ---
        ai_voice_filename = f"audio/{token}_ai.mp3"
        with open(temp_tts_path, "rb") as f:
            ai_audio_url = upload_audio_to_s3(f, ai_voice_filename)

        # --- 10. Save everything to DB ---
        db_utils.insert_message(
            token=token,
            email=email,
            ip=ip,
            created_at=today,
            delivery_date=delivery_date,
            original_audio=audio_url,
            ai_audio=ai_audio_url,
            transcript=transcript,
            enhanced_text=reply,
            voice_id=voice_id
        )

        cost_tracker.log_cost(
            token=token,
            duration_sec=duration_sec,
            gpt_input=0,
            gpt_output=0,
            tts_chars=len(reply)
        )

        email_utils.send_confirmation_email(email, token, delivery_date)
        return f"✅ Your time capsule is sealed! You’ll receive it on {delivery_date}."

    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        if temp_tts_path and os.path.exists(temp_tts_path):
            os.remove(temp_tts_path)

@app.route("/view/<token>")
def view_message(token):
    message = db_utils.get_message_by_token(token)
    if not message:
        return "❌ Message not found", 404
    return render_template("view.html", **message)

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def authenticate():
    return Response(
        "Could not verify your access level for that URL.\n"
        "You have to login with proper credentials", 401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route("/admin")
@requires_auth
def admin():
    df1 = pd.read_sql_query("SELECT * FROM messages", engine)
    df2 = pd.read_sql_query("SELECT * FROM cost_log", engine)
    html = "<h2>Messages</h2>" + df1.to_html(classes="table-auto") \
         + "<h2>Cost Log</h2>" + df2.to_html(classes="table-auto")
    return Markup(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

