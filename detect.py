import cv2
import numpy as np
import os
import tensorflow as tf
from datetime import datetime
import sqlite3
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()
import os


model = tf.keras.models.load_model('model.h5')
VIOLENCE_THRESHOLD = 0.85

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")

def send_email_alert(confidence, frame_path, timestamp):
    msg = EmailMessage()
    msg['Subject'] = f'Violence Alert - Confidence {confidence:.2f}'
    msg['From'] = EMAIL
    msg['To'] = EMAIL
    msg.set_content(f'Violence detected at {timestamp} with confidence {confidence:.2f}. See attached frame.')

    with open(frame_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='image', subtype='jpeg', filename=os.path.basename(frame_path))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL, PASSWORD)
        smtp.send_message(msg)


def log_alert(video, frame_path, confidence, timestamp):
    conn = sqlite3.connect('violence_log.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO alerts (video, frame_path, confidence, timestamp) VALUES (?, ?, ?, ?)",
                   (video, frame_path, float(confidence), timestamp))
    conn.commit()
    conn.close()

def log_video(filename, status):
    conn = sqlite3.connect('video_logs.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (filename, status, timestamp) VALUES (?, ?, ?)",
                   (filename, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def save_detection_frame(frame, label):
    if not os.path.exists('captures'):
        os.makedirs('captures')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"captures/{label}_{timestamp}.jpg"
    cv2.imwrite(filename, frame)
    return filename

def detect_violence_clip(path):
    cap = cv2.VideoCapture(path)
    frame_buffer = []
    violence_detected = False
    max_confidence = 0
    frame_path = None
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        resized = cv2.resize(frame, (64, 64))
        frame_buffer.append(resized)
        frame_count += 1

        if len(frame_buffer) == 10:
            input_array = np.array([frame_buffer]) / 255.0
            prediction = model.predict(input_array)[0][0]

            start_frame = frame_count - 9
            end_frame = frame_count
            print(f"Frames {start_frame}-{end_frame} | Confidence: {prediction:.2f}")

            if prediction > VIOLENCE_THRESHOLD:
                frame_path = save_detection_frame(frame_buffer[-1], "violence")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                send_email_alert(prediction, frame_path, timestamp)
                log_alert(os.path.basename(path), frame_path, prediction, timestamp)
                log_video(os.path.basename(path), "violent")
                violence_detected = True
                max_confidence = prediction
                break

            frame_buffer.pop(0)

    if not violence_detected:
        log_video(os.path.basename(path), "non-violent")

    cap.release()
    return float(max_confidence), "Violence Detected" if max_confidence > 0.5 else "No Violence"
