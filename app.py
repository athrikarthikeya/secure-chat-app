from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
import sqlite3
import os
from cryptography.fernet import Fernet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

# 🔑 Load or create encryption key
if not os.path.exists("secret.key"):
    key = Fernet.generate_key()
    with open("secret.key", "wb") as f:
        f.write(key)
else:
    with open("secret.key", "rb") as f:
        key = f.read()

cipher = Fernet(key)

# 👥 Track users
user_count = 0

# 📦 Initialize database
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS messages (msg TEXT)')
    conn.commit()
    conn.close()

init_db()

# 🏠 Home route
@app.route('/')
def index():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT msg FROM messages')
    encrypted_msgs = c.fetchall()
    conn.close()

    messages = []
    for m in encrypted_msgs:
        try:
            decrypted = cipher.decrypt(m[0].encode()).decode()
            messages.append(decrypted)
        except:
            pass

    return render_template('index.html', messages=messages)

# 💬 Handle message
@socketio.on('message')
def handle_message(msg):
    encrypted_msg = cipher.encrypt(msg.encode()).decode()

    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('INSERT INTO messages (msg) VALUES (?)', (encrypted_msg,))
    conn.commit()
    conn.close()

    send(msg, broadcast=True)

# 🟢 User connected
@socketio.on('connect')
def handle_connect():
    global user_count
    user_count += 1
    emit('user_count', user_count, broadcast=True)

# 🔴 User disconnected
@socketio.on('disconnect')
def handle_disconnect():
    global user_count
    user_count -= 1
    emit('user_count', user_count, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)