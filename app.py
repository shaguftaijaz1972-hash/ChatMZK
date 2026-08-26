# ==========================================
# Imports
# ==========================================

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session
)

from dotenv import load_dotenv
from google import genai

import sqlite3
import os

from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from docx import Document


# ==========================================
# Load Environment
# ==========================================

load_dotenv()


# ==========================================
# Gemini AI
# ==========================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ==========================================
# Flask App
# ==========================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "chatmzk_secret_key"
)


# ==========================================
# Configuration
# ==========================================

DATABASE = "database.db"

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "docx"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ==========================================
# Global Variables
# ==========================================

current_chat_id = None
current_document = ""
# ==========================================
# Database Connection
# ==========================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================
# Initialize Database
# ==========================================

def init_db():

    conn = get_db()

    cursor = conn.cursor()

    # ==========================================
    # Users Table
    # ==========================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        profile_photo TEXT DEFAULT '',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)
  

    # ==========================================
    # Chats Table
    # ==========================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS chats(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        title TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id)
        REFERENCES users(id)

    )

    """)

    # ==========================================
    # Messages Table
    # ==========================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS messages(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        chat_id INTEGER,

        sender TEXT NOT NULL,

        message TEXT NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(chat_id)
        REFERENCES chats(id)

    )

    """)

    conn.commit()

    conn.close()
   # ==========================================
# Initialize Database
# ==========================================

init_db()

print("DATABASE INITIALIZED:", DATABASE)


    # ==========================================
# Home
# ==========================================

@app.route("/")
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("index.html")


# ==========================================
# Login
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM users
        WHERE email=? AND password=?
        """,
        (email, password)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return redirect(url_for("home"))

    return render_template(
        "login.html",
        error="Invalid email or password."
    )


# ==========================================
# Signup
# ==========================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "GET":
        return render_template("signup.html")

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE email=?",
        (email,)
    )

    if cursor.fetchone():

        conn.close()

        return render_template(
            "signup.html",
            error="Email already exists."
        )

    cursor.execute(
        """
        INSERT INTO users(username,email,password)
        VALUES(?,?,?)
        """,
        (username, email, password)
    )

    conn.commit()

    conn.close()

    return redirect(url_for("login"))


# ==========================================
# Logout
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))
    # ==========================================
# New Chat
# ==========================================

@app.route("/new_chat", methods=["POST"])
def new_chat():

    global current_chat_id

    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chats(user_id, title)
        VALUES(?, ?)
        """,
        (
            session["user_id"],
            "New Chat"
        )
    )

    conn.commit()

    current_chat_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "chat_id": current_chat_id
    })


# ==========================================
# Get Chats
# ==========================================

@app.route("/get_chats")
def get_chats():

    if "user_id" not in session:
        return jsonify([])

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, title
        FROM chats
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    )

    chats = cursor.fetchall()

    conn.close()

    return jsonify([
        dict(chat)
        for chat in chats
    ])


# ==========================================
# Get Messages
# ==========================================

@app.route("/get_messages/<int:chat_id>")
def get_messages(chat_id):

    global current_chat_id

    current_chat_id = chat_id

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT sender, message
        FROM messages
        WHERE chat_id=?
        ORDER BY id ASC
        """,
        (chat_id,)
    )

    messages = cursor.fetchall()

    conn.close()

    return jsonify([
        dict(message)
        for message in messages
    ])
    # ==========================================
# Chat
# ==========================================

@app.route("/chat", methods=["POST"])
def chat():

    global current_chat_id
    global current_document

    try:

        if "user_id" not in session:
            return jsonify({
                "reply": "Please login first."
            }), 401

        data = request.get_json()

        user_message = data.get(
            "message",
            ""
        ).strip()

        if not user_message:
            return jsonify({
                "reply": "Please enter a message."
            })

        conn = get_db()
        cursor = conn.cursor()

        # Create first chat automatically
        if current_chat_id is None:

            cursor.execute(
                """
                INSERT INTO chats(user_id,title)
                VALUES(?,?)
                """,
                (
                    session["user_id"],
                    "New Chat"
                )
            )

            conn.commit()

            current_chat_id = cursor.lastrowid

        # Save User Message
        cursor.execute(
            """
            INSERT INTO messages(chat_id,sender,message)
            VALUES(?,?,?)
            """,
            (
                current_chat_id,
                "user",
                user_message
            )
        )

        conn.commit()

        # Prompt
        if current_document.strip():

            prompt = f"""
You are ChatMZK AI.

Answer ONLY from the uploaded document.

Document:

{current_document}

Question:

{user_message}
"""

        else:

            prompt = user_message

        # Gemini Response
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        ai_message = response.text

        # Auto Chat Title
        cursor.execute(
            """
            SELECT title
            FROM chats
            WHERE id=?
            """,
            (current_chat_id,)
        )

        chat = cursor.fetchone()

        if chat and chat["title"] == "New Chat":

            cursor.execute(
                """
                UPDATE chats
                SET title=?
                WHERE id=?
                """,
                (
                    user_message[:35],
                    current_chat_id
                )
            )

        # Save AI Message
        cursor.execute(
            """
            INSERT INTO messages(chat_id,sender,message)
            VALUES(?,?,?)
            """,
            (
                current_chat_id,
                "assistant",
                ai_message
            )
        )

        conn.commit()

        conn.close()

        return jsonify({
            "reply": ai_message
        })

    except Exception as e:

        print(e)

        return jsonify({
            "reply": "Server Error. Please try again."
        }), 500
        # ==========================================
# Allowed File
# ==========================================

def allowed_file(filename):

    return (

        "." in filename

        and

        filename.rsplit(".", 1)[1].lower()

        in ALLOWED_EXTENSIONS

    )


# ==========================================
# Read Uploaded Document
# ==========================================

def read_document(filepath):

    ext = filepath.rsplit(".", 1)[1].lower()

    # TXT
    if ext == "txt":

        with open(
            filepath,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            return file.read()

    # PDF
    elif ext == "pdf":

        text = ""

        reader = PdfReader(filepath)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"

        return text

    # DOCX
    elif ext == "docx":

        doc = Document(filepath)

        text = ""

        for para in doc.paragraphs:

            text += para.text + "\n"

        return text

    return ""


# ==========================================
# Upload File
# ==========================================

@app.route("/upload", methods=["POST"])
def upload():

    global current_document

    if "file" not in request.files:

        return jsonify({
            "success": False,
            "message": "No file selected."
        })

    file = request.files["file"]

    if file.filename == "":

        return jsonify({
            "success": False,
            "message": "No file selected."
        })

    if not allowed_file(file.filename):

        return jsonify({
            "success": False,
            "message": "Only TXT, PDF and DOCX files are allowed."
        })

    filename = secure_filename(file.filename)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    current_document = read_document(filepath)

    return jsonify({

        "success": True,

        "filename": filename

    })
    # ==========================================
# Delete Chat
# ==========================================

@app.route("/delete_chat/<int:chat_id>", methods=["POST"])
def delete_chat(chat_id):

    if "user_id" not in session:
        return jsonify({"success": False}), 401

    conn = get_db()
    cursor = conn.cursor()

    # Delete messages first
    cursor.execute(
        """
        DELETE FROM messages
        WHERE chat_id=?
        """,
        (chat_id,)
    )

    # Delete chat
    cursor.execute(
        """
        DELETE FROM chats
        WHERE id=? AND user_id=?
        """,
        (
            chat_id,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


# ==========================================
# Clear Current Chat
# ==========================================

@app.route("/clear_chat", methods=["POST"])
def clear_chat():

    global current_chat_id

    if current_chat_id is None:

        return jsonify({
            "success": False
        })

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM messages
        WHERE chat_id=?
        """,
        (current_chat_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


# ==========================================
# User Profile
# ==========================================

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT username,email,profile_photo,created_at
        FROM users
        WHERE id=?
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


# ==========================================
# Run Server
# ==========================================

if __name__ == "__main__":

    init_db()

    print("🚀 Starting ChatMZK...")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
