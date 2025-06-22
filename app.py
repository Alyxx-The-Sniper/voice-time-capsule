import os
import uuid
from dotenv import load_dotenv
from flask import Flask, request, render_template
from utils import whisper_utils, gpt_utils, tts_utils, db_utils, cost_tracker, email_utils
from utils.db_utils import DB_PATH, count_submissions_by_ip
from email_validator import validate_email, EmailNotValidError
from datetime import date


load_dotenv()
db_utils.init_db()

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join("static", "audio")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    # 1) Parse inputs

    # 1.1 simple email handler for valid or invalid email
    raw_email = request.form.get("email", "")
    try:
        # Throws EmailNotValidError if invalid
        v = validate_email(raw_email, check_deliverability=True)
        email = v.email  # normalized form
    except EmailNotValidError as e:
        return f"❌ Invalid email address: {str(e)}", 400

    # 1.2 limit submission per IP (this rule refresh 24 hours)
    ip = request.remote_addr
    today = date.today().isoformat()
    # rate-limit by IP
    if count_submissions_by_ip(ip, today) >= 4:
        return "❌ You’ve reached the maximun submissions today. Please try again tomorrow", 429
    

    # delviery date and audio
    delivery_date = request.form.get("deliveryDate")
    audio_file = request.files.get("audio")
    if not email or not delivery_date or not audio_file:
        return "Missing form fields", 400


    token = uuid.uuid4().hex[:8]

    # 2) Save uploaded audio to "audio/" (flat structure, not per-user)
    audio_path = os.path.join(UPLOAD_FOLDER, f"{token}.webm")
    audio_file.save(audio_path)

    # 3) Transcribe & duration
    transcript, duration_sec = whisper_utils.transcribe(audio_path)

    # 4) AI rewrite (free HF model)
    reply = gpt_utils.respond_as_future_self(transcript)


    ### Debuging phase 
    # print("===Speech to Text===")
    # print(transcript)
    # print("=======")
    # print("=== AI Reply ===")
    # print(reply)
    # # For debugging, return the reply to the user and halt further steps:
    # # check if the transcribe is readable
    # return f"AI reply:\n{reply}", 200
    # End debuging Phase



    # 5) Clone voice & synthesize TTS
    voice_id = tts_utils.upload_user_voice(name=email, audio_path=audio_path)
    ai_voice_path = os.path.join(UPLOAD_FOLDER, f"{token}_ai.mp3")
    tts_utils.synthesize(reply, ai_voice_path, voice_id)



    # 6) Save to database

    # mesagges table
    db_utils.insert_message(
        token=token,
        email=email,
        ip=ip,
        created_at=today,
        delivery_date=delivery_date,
        original_audio=audio_path,
        ai_audio=ai_voice_path,
        transcript=transcript,
        enhanced_text=reply,
        voice_id=voice_id
    )

    # 7) Cost tracking table
    cost_tracker.log_cost(
        token=token,
        duration_sec=duration_sec,
        gpt_input=0,
        gpt_output=0,
        tts_chars=len(reply)
    )

    # 8) Send confirmation email
    email_utils.send_confirmation_email(email, token, delivery_date)

    return f"✅ Your time capsule is sealed! You’ll receive it on {delivery_date}."

@app.route("/view/<token>")
def view_message(token):
    message = db_utils.get_message_by_token(token)
    if not message:
        return "❌ Message not found", 404
    return render_template("view.html", **message)



import pandas as pd
import sqlite3
from markupsafe import Markup

@app.route("/admin")
def admin():
    conn = sqlite3.connect(DB_PATH)
    df1 = pd.read_sql_query("SELECT * FROM messages", conn)
    df2 = pd.read_sql_query("SELECT * FROM cost_log", conn)
    html = "<h2>Messages</h2>" + df1.to_html(classes="table-auto") \
         + "<h2>Cost Log</h2>" + df2.to_html(classes="table-auto")
    return Markup(html)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

