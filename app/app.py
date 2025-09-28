from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import datetime
import os

app = Flask(__name__)

DB_FILE = "clipboard.db"
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS texts (
        id INTEGER PRIMARY KEY,
        content TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY,
        filename TEXT,
        size INTEGER,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET"])
def index():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT content, timestamp FROM texts ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    latest_text = row[0] if row else ""
    latest_time = row[1] if row else ""
    c.execute("SELECT id, filename, size, timestamp FROM files ORDER BY id DESC")
    files = c.fetchall()
    conn.close()
    return render_template("index.html", latest_text=latest_text, latest_time=latest_time, files=files)

@app.route("/save_text", methods=["POST"])
def save_text():
    data = request.get_json()
    if data and "content" in data:
        content = data["content"]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM texts")
        c.execute("INSERT INTO texts (content, timestamp) VALUES (?, ?)", (content, timestamp))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "timestamp": timestamp})
    return jsonify({"success": False}), 400

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "msg": "没有文件"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "msg": "文件名为空"}), 400
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)
    size = os.path.getsize(save_path)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO files (filename, size, timestamp) VALUES (?, ?, ?)", (file.filename, size, timestamp))
    file_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"success": True, "file": {"id": file_id, "filename": file.filename, "size": size, "timestamp": timestamp}})

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)

@app.route("/delete/<int:file_id>", methods=["POST"])
def delete_file(file_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT filename FROM files WHERE id=?", (file_id,))
    row = c.fetchone()
    if row:
        filename = row[0]
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        c.execute("DELETE FROM files WHERE id=?", (file_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "file_id": file_id})
    conn.close()
    return jsonify({"success": False}), 404

if __name__ == "__main__":
    app.run(debug=True)
