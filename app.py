from flask import Flask, render_template, request, redirect, url_for, jsonify
from detect import detect_violence_clip
from werkzeug.utils import secure_filename
import os
import sqlite3

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join("static", "uploads")
VIDEO_FOLDER = os.path.join("static", "videos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

uploaded_video_path = ""

@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@app.route('/alerts')
def alerts():
    conn = sqlite3.connect("violence_log.db")
    cursor = conn.cursor()
    cursor.execute("SELECT video, frame_path, confidence, timestamp FROM alerts")
    alerts_data = cursor.fetchall()
    conn.close()
    return render_template("alerts.html", alerts=alerts_data)

@app.route('/videologs')
def videologs():
    conn = sqlite3.connect("video_logs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT filename, status, timestamp FROM logs")
    video_logs = cursor.fetchall()
    conn.close()
    return render_template("videologs.html", logs=video_logs)

@app.route('/detect_video/<label>')
def detect_video(label):
    path = os.path.join("static", "videos", f"{label}.mp4")
    confidence, status = detect_violence_clip(path)
    return jsonify({
        "confidence": float(confidence),
        "status": status
    })

@app.route("/upload", methods=["POST"])
def upload():
    global uploaded_video_path
    if 'video' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    filename = secure_filename(file.filename)
    uploaded_video_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(uploaded_video_path)
    confidence, status = detect_violence_clip(uploaded_video_path)
    return jsonify({
        'filename': filename,
        'confidence': float(confidence),
        'status': status,
        'video_url': url_for('static', filename=f'uploads/{filename}')
    })

@app.route("/detect_uploaded")
def detect_uploaded():
    global uploaded_video_path
    confidence, status = detect_violence_clip(uploaded_video_path)
    return jsonify({
        "confidence": float(confidence),
        "status": status
    })

@app.route('/clear_alerts', methods=['POST'])
def clear_alerts():
    conn = sqlite3.connect("violence_log.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()
    return redirect(url_for('alerts'))

@app.route('/clear_videologs', methods=['POST'])
def clear_videologs():
    conn = sqlite3.connect("video_logs.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM logs")
    conn.commit()
    conn.close()
    return redirect(url_for('videologs'))

if __name__ == "__main__":
    app.run(debug=True)
