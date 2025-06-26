import os
import uuid
from flask import Flask, request, render_template, jsonify, redirect, url_for, Response, flash, session
from datetime import date
import tempfile

# If you use dotenv
from dotenv import load_dotenv
load_dotenv()

from utils import gpt_utils, tts_utils, db_utils, cost_tracker, email_utils, whisper_utils
from utils.s3_utils import upload_audio_to_s3

from sqlalchemy import create_engine
import pandas as pd
from markupsafe import Markup
from functools import wraps

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
engine = create_engine(DATABASE_URL)

with app.app_context():
    db_utils.init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    ip = request.remote_addr
    today = date.today().isoformat()
    if db_utils.count_submissions_by_ip(ip, today) >= 100:
        return jsonify({'error': "Rate limit reached"}), 429

    name = request.form.get("name", "")
    delivery_date = request.form.get("deliveryDate")
    audio_file = request.files.get("audio")
    if not name or not delivery_date or not audio_file:
        return jsonify({'error': "Missing form fields"}), 400

    token = uuid.uuid4().hex[:8]
    filename = f"{token}.webm"

    temp_audio_path = None
    temp_tts_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
            audio_file.save(temp_audio_path)

        transcript, duration_sec = whisper_utils.transcribe(temp_audio_path)

        with open(temp_audio_path, "rb") as f:
            audio_url = upload_audio_to_s3(f, f"audio/{filename}")

        reply = gpt_utils.respond_as_future_self(transcript)
        voice_id = tts_utils.upload_user_voice(name=name, audio_path=temp_audio_path)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tempf:
            temp_tts_path = tempf.name

        tts_utils.synthesize(reply, temp_tts_path, voice_id)

        ai_voice_filename = f"audio/{token}_ai.mp3"
        with open(temp_tts_path, "rb") as f:
            ai_audio_url = upload_audio_to_s3(f, ai_voice_filename)

        db_utils.insert_message(
            token=token,
            name=name,
            email=None,
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

        # Respond with redirect URL
        return jsonify({'redirect_url': url_for('view_message', token=token)})

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
    # Grab feedback from query param if present
    sent = request.args.get("sent")
    email_status = None
    if sent == "1":
        email_status = "✅ Email sent! Check your inbox."
    elif sent == "0":
        email_status = "❌ There was a problem sending the email."
    return render_template("view.html", email_status=email_status, **message)




# Email sending from view page is handled via another route (POST from the form on view.html)
@app.route("/send_audio", methods=["POST"])
def send_audio():
    email = request.form.get("email", "").strip()
    token = request.form.get("token", "").strip()
    if not email or not token:
        # Ideally flash an error or handle
        return redirect(url_for('view_message', token=token, sent=0))

    # Find audio_file by token in DB
    message = db_utils.get_message_by_token(token)
    if not message:
        return "❌ Message not found", 404

    audio_url = message['ai_audio']  

    # Update the database with the new email!
    db_utils.update_message_email(token, email)


    # Send the audio via email (implement email_utils.send_audio_email)
    try:
        email_utils.send_audio_email(email, audio_url)
        # Pass success info to the template
        return redirect(url_for('view_message', token=token, sent=1))
    except Exception as e:
        print("Email send error:", e)
        return redirect(url_for('view_message', token=token, sent=0))

# Admin panel code (unchanged)
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
