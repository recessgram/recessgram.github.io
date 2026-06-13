import sqlite3
from datetime import datetime
from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)
DB_FILE = "recessgram_final.db"

PROHIBITED_WORDS = {
    "abuse", "ass", "asshole", "bitch", "bastard", "crap", "cunt", "dick", 
    "fudge", "fuck", "idiot", "jerk", "moron", "loser", "piss", "prick", 
    "shit", "slut", "stupid", "suck", "twat", "whore"
}

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Recessgram - Login</title>
    <style>
        body { font-family: 'Comic Sans MS', sans-serif; background: #fff9c4; text-align: center; padding: 50px; }
        .box { background: white; padding: 30px; border-radius: 15px; display: inline-block; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); width: 300px; }
        input { display: block; margin: 10px auto; padding: 10px; width: 90%; border-radius: 5px; border: 1px solid #ccc; box-sizing: border-box; }
        button { background: #ff4081; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold; width: 90%; }
    </style>
</head>
<body>
    <h1>🎒 Welcome to Recessgram!</h1>
    <div class="box">
        <h3>Log In</h3>
        <form action="/web-login" method="POST">
            <input type="text" name="username" placeholder="Username" required />
            <input type="password" name="password" placeholder="Password" required />
            <button type="submit">Let's Play!</button>
        </form>
        <hr style="margin: 20px 0;">
        <h3>Join the Playground</h3>
        <form action="/web-register" method="POST">
            <input type="text" name="username" placeholder="Choose Username" required />
            <input type="password" name="password" placeholder="Create Password" required />
            <input type="number" name="age" placeholder="Age" required />
            <input type="email" name="guardian_contact" placeholder="Parent's Email" required />
            <button type="submit" style="background: #4caf50;">Create Account</button>
        </form>
    </div>
</body>
</html>
"""
MAIN_UI_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Recessgram - Dashboard</title>
    <style>
        body { font-family: 'Comic Sans MS', sans-serif; background: #e0f7fa; margin: 0; padding: 20px; }
        .navbar { background: #ff4081; padding: 15px; color: white; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .navbar a { color: white; text-decoration: none; font-weight: bold; background: rgba(0,0,0,0.2); padding: 5px 10px; border-radius: 5px; }
        .layout { display: flex; gap: 20px; max-width: 1400px; margin: auto; }
        .sidebar { width: 260px; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); height: 80vh; display: flex; flex-direction: column; }
        .column { flex: 1; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); height: 80vh; display: flex; flex-direction: column; }
        .list-container { flex: 1; overflow-y: auto; margin-top: 15px; padding-right: 5px; }
        .box-item { background: #f9f9f9; padding: 12px; border-radius: 10px; margin-bottom: 12px; border-left: 5px solid #00bcd4; }
        .chat-item { border-left-color: #ff9800; }
        .friend-item { border-left-color: #e91e63; }
        .link-item { display: block; padding: 10px; margin: 5px 0; background: #f0f0f0; border-radius: 5px; color: #333; text-decoration: none; font-weight: bold; font-size: 0.9em; }
        .link-item.active { background: #ff4081; color: white; }
        .link-item.friend-link.active { background: #e91e63; color: white; }
        textarea, input[type="text"] { width: 100%; border-radius: 5px; border: 1px solid #ccc; box-sizing: border-box; }
        textarea { height: 50px; margin-bottom: 8px; resize: none; }
        input[type="text"] { padding: 8px; margin-bottom: 8px; }
        button { background: #4caf50; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; }
    </style>
</head>
<body>
    <div class="navbar">
        <h2>🎒 Recessgram Dashboard</h2>
        <div>
            👋 @{{ current_username }} | 
            <a href="/parent-portal" style="background: #4caf50; margin-right: 10px;">🔑 Parent Portal</a>
            <a href="/logout">Log Out</a>
        </div>
    </div>
    <div class="layout">
        <div class="sidebar">
            <h3>📚 Subjects & Chats</h3>
            <div style="overflow-y: auto; max-height: 35%;">
                {% for chan in channels %}
                <a href="/dashboard?username={{ current_username }}&channel_id={{ chan.id }}" 
                   class="link-item {% if chan.id == current_channel_id and not chat_mode_friend %}active{% endif %}">
                    # {{ chan.name }}
                </a>
                {% endfor %}
            </div>
            <hr style="width: 100%; margin: 15px 0;">
            <h3>👥 Playmates</h3>
            <div style="overflow-y: auto; flex: 1;">
                {% for user_profile in users_list %}
                    {% if user_profile.username != current_username %}
                    <a href="/dashboard?username={{ current_username }}&target_friend_id={{ user_profile.id }}" 
                       class="link-item friend-link {% if user_profile.id == active_friend_id and chat_mode_friend %}active{% endif %}">
                        💬 Chat with @{{ user_profile.username }}
                    </a>
                    {% endif %}
                {% endfor %}
            </div>
        </div>
        <div class="column">
            <h3>📸 Friend Feed</h3>
            <form action="/web-post" method="POST">
                <input type="hidden" name="username" value="{{ current_username }}">
                <input type="hidden" name="channel_id" value="{{ current_channel_id }}">
                <input type="hidden" name="target_friend_id" value="{{ active_friend_id }}">
                <input type="hidden" name="chat_mode_friend" value="{{ chat_mode_friend }}">
                <textarea name="content" placeholder="Share what you are doing..." required></textarea>
                <button type="submit">Post to Feed ✨</button>
            </form>
            <div class="list-container">
                {% for post in feed %}
                <div class="box-item">
                    <div style="font-size:0.8em; color:#777;">@{{ post.username }} • {{ post.timestamp }}</div>
                    <p style="margin: 5px 0 0 0;">{{ post.content }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
        <div class="column">
            {% if chat_mode_friend %}
                <h3>💬 Friend Chat: @{{ active_friend_name }}</h3>
                <form action="/web-friend-chat" method="POST">
                    <input type="hidden" name="username" value="{{ current_username }}">
                    <input type="hidden" name="target_friend_id" value="{{ active_friend_id }}">
                    <textarea name="message" placeholder="Send a private note..." required></textarea>
                    <button type="submit" style="background:#e91e63; color:white; border:none; padding:8px; border-radius:5px; cursor:pointer;">Send Secret Note 🔐</button>
                </form>
            {% else %}
                <h3>💬 Room Thread: #{{ active_channel_name }}</h3>
                <form action="/web-chat" method="POST">
                    <input type="hidden" name="username" value="{{ current_username }}">
                    <input type="hidden" name="channel_id" value="{{ current_channel_id }}">
                    <textarea name="message" placeholder="Type a message to this room..." required></textarea>
                    <button type="submit" style="background:#ff9800; color:white; border:none; padding:8px; border-radius:5px; cursor:pointer;">Send Message 🚀</button>
                </form>
            {% endif %}
            <div class="list-container">
                {% for chat in chats %}
                <div class="box-item {% if chat_mode_friend %}friend-item{% else %}chat-item{% endif %}">
                    <div style="font-size:0.8em; {% if chat_mode_friend %}color:#e91e63;{% else %}color:#ff9800;{% endif %}">@{{ chat.username }} • {{ chat.timestamp }}</div>
                    <p style="margin: 5px 0 0 0;">{{ chat.message }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
"""

PARENT_PORTAL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Recessgram - Parent Portal</title>
    <style>
        body { font-family: 'Comic Sans MS', sans-serif; background: #f5f5f5; padding: 30px; }
        .container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ff4081; padding-bottom: 10px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #ff4081; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .badge { background: #f44336; color: white; padding: 3px 8px; border-radius: 5px; font-size: 0.85em; font-weight: bold; }
        .back-btn { text-decoration: none; color: white; background: #333; padding: 8px 15px; border-radius: 5px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🔑 Parent Control Dashboard & Safety Logs</h2>
            <a href="/" class="back-btn">⬅️ Exit Portal</a>
        </div>
        <p>This portal tracks safety incidents and filtered text trends across public threads and peer communication feeds.</p>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>User Account</th>
                <th>Parent Contact Email</th>
                <th>Blocked Message Content</th>
                <th>System Status</th>
            </tr>
            {% for alert in alerts %}
            <tr>
                <td>{{ alert.timestamp }}</td>
                <td style="color:#ff4081; font-weight:bold;">@{{ alert.username }}</td>
                <td>{{ alert.guardian }}</td>
                <td style="background:#ffebee; color:#c62828; font-family:monospace;">{{ alert.content }}</td>
                <td><span class="badge">INTERCEPTED</span></td>
            </tr>
            {% else %}
            <tr>
                <td colspan="5" style="text-align: center; color: #777; padding: 20px;">🎉 Clean record! No restricted language violations flagged.</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, age INTEGER NOT NULL, guardian_contact TEXT NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, content TEXT NOT NULL, timestamp TEXT, channel_id INTEGER, target_friend_id INTEGER, chat_mode_friend INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, message TEXT NOT NULL, timestamp TEXT, channel_id INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS friend_chats (id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, receiver_id INTEGER, message TEXT NOT NULL, timestamp TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS safety_alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, blocked_content TEXT, timestamp TEXT)')
    try:
        cursor.executemany('INSERT INTO channels (name) VALUES (?)', [('General',), ('Math',), ('Science',), ('Art',)])
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

def is_safe(text):
    cleaned_text = "".join(c if c.isalnum() else " " for c in text.lower())
    words = cleaned_text.split()
    return not any(word in PROHIBITED_WORDS for word in words)

@app.route('/')
def home():
    return LOGIN_HTML

@app.route('/logout')
def logout():
    return redirect('/')

@app.route('/parent-portal')
def parent_portal():
    pin_attempt = request.args.get('pin')
    if pin_attempt != "recess123":
        return """
        <div style="text-align:center; padding:50px; font-family:sans-serif;">
            <h3>🔑 Parent Portal Lock</h3>
            <form method="GET" action="/parent-portal">
                <input type="password" name="pin" placeholder="Enter Parent Passcode" required style="padding:5px;">
                <button type="submit" style="padding:5px; cursor:pointer;">Verify</button>
            </form>
            <p style="font-size:0.8em; color:red;">Hint: Code is recess123</p>
            <br><a href="/">Back to Dashboard</a>
        </div>
        """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT safety_alerts.timestamp, users.username, users.guardian_contact, safety_alerts.blocked_content 
        FROM safety_alerts 
        JOIN users ON safety_alerts.user_id = users.id 
        ORDER BY safety_alerts.id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    alerts = [{"timestamp": r[0], "username": r[1], "guardian": r[2], "content": r[3]} for r in rows]
    return render_template_string(PARENT_PORTAL_HTML, alerts=alerts)
@app.route('/web-login', methods=['POST'])
def web_login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0] == password:
        return redirect(f"/dashboard?username={username}")
    return "<h3>❌ Incorrect username or password!</h3><a href='/'>Try Again</a>"

@app.route('/dashboard')
def dashboard():
    username = request.args.get('username')
    channel_id = request.args.get('channel_id')
    target_friend_id = request.args.get('target_friend_id')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return "<h3>User profile not found!</h3><a href='/'>Go Back</a>"
    user_id = user_row[0]
    
    cursor.execute("SELECT id, username FROM users ORDER BY username ASC")
    users_list = [{"id": r[0], "username": r[1]} for r in cursor.fetchall()]
    cursor.execute("SELECT id, name FROM channels ORDER BY id ASC")
    channels = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]
    
    chat_mode_friend = 0
    active_friend_id = 0
    active_friend_name = ""
    
    if target_friend_id:
        chat_mode_friend = 1
        active_friend_id = int(target_friend_id)
        cursor.execute("SELECT username FROM users WHERE id = ?", (active_friend_id,))
        friend_row = cursor.fetchone()
        active_friend_name = friend_row[0] if friend_row else ""
        current_channel_id = channels[0]['id'] if channels else 1
        active_channel_name = channels[0]['name'] if channels else "General"
    else:
        if not channel_id:
            current_channel_id = channels[0]['id'] if channels else 1
        else:
            current_channel_id = int(channel_id)
        cursor.execute("SELECT name FROM channels WHERE id = ?", (current_channel_id,))
        active_channel_row = cursor.fetchone()
        active_channel_name = active_channel_row[0] if active_channel_row else "General"

    if chat_mode_friend:
        cursor.execute('''
            SELECT u.username, posts.content, posts.timestamp FROM posts 
            JOIN users u ON posts.user_id = u.id 
            WHERE posts.chat_mode_friend = 1 AND 
            ((posts.user_id = ? AND posts.target_friend_id = ?) OR (posts.user_id = ? AND posts.target_friend_id = ?))
            ORDER BY posts.id DESC
        ''', (user_id, active_friend_id, active_friend_id, user_id))
    else:
        cursor.execute('''
            SELECT u.username, posts.content, posts.timestamp FROM posts 
            JOIN users u ON posts.user_id = u.id 
            WHERE posts.chat_mode_friend = 0 AND posts.channel_id = ? 
            ORDER BY posts.id DESC
        ''', (current_channel_id,))
    feed = [{"username": r[0], "content": r[1], "timestamp": r[2]} for r in cursor.fetchall()]

    if chat_mode_friend:
        cursor.execute('''
            SELECT u.username, friend_chats.message, friend_chats.timestamp FROM friend_chats 
            JOIN users u ON friend_chats.sender_id = u.id 
            WHERE (friend_chats.sender_id = ? AND friend_chats.receiver_id = ?) 
               OR (friend_chats.sender_id = ? AND friend_chats.receiver_id = ?) 
            ORDER BY friend_chats.id DESC
        ''', (user_id, active_friend_id, active_friend_id, user_id))
    else:
        cursor.execute('''
            SELECT u.username, chats.message, chats.timestamp FROM chats 
            JOIN users u ON chats.user_id = u.id 
            WHERE chats.channel_id = ? 
            ORDER BY chats.id DESC
        ''', (current_channel_id,))
    chats_list = [{"username": r[0], "message": r[1], "timestamp": r[2]} for r in cursor.fetchall()]
    
    conn.close()
    return render_template_string(MAIN_UI_HTML, current_username=username, current_channel_id=current_channel_id, active_channel_name=active_channel_name, channels=channels, feed=feed, chats=chats_list, users_list=users_list, chat_mode_friend=chat_mode_friend, active_friend_id=active_friend_id, active_friend_name=active_friend_name)
@app.route('/web-register', methods=['POST'])
def web_register():
    username = request.form.get('username')
    password = request.form.get('password')
    age = request.form.get('age')
    guardian_contact = request.form.get('guardian_contact')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, age, guardian_contact) VALUES (?, ?, ?, ?)", (username, password, age, guardian_contact))
        conn.commit()
        conn.close()
        return redirect(f"/dashboard?username={username}")
    except sqlite3.IntegrityError:
        conn.close()
        return "<h3>That username is already taken!</h3><a href='/'>Try again</a>"

@app.route('/web-post', methods=['POST'])
def web_post():
    username = request.form.get('username')
    content = request.form.get('content')
    channel_id = int(request.form.get('channel_id'))
    target_friend_id = int(request.form.get('target_friend_id'))
    chat_mode_friend = int(request.form.get('chat_mode_friend'))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = cursor.fetchone()[0]
    if not is_safe(content):
        cursor.execute("INSERT INTO safety_alerts (user_id, blocked_content, timestamp) VALUES (?, ?, ?)", (user_id, content, timestamp))
        conn.commit()
        conn.close()
        return "<h3>⚠️ Post blocked! Let's stay kind on Recessgram.</h3><a href='javascript:history.back()'>Go Back</a>"
    cursor.execute("INSERT INTO posts (user_id, content, timestamp, channel_id, target_friend_id, chat_mode_friend) VALUES (?, ?, ?, ?, ?, ?)", (user_id, content, timestamp, channel_id, target_friend_id, chat_mode_friend))
    conn.commit()
    conn.close()
    if chat_mode_friend:
        return redirect(f"/dashboard?username={username}&target_friend_id={target_friend_id}")
    return redirect(f"/dashboard?username={username}&channel_id={channel_id}")

@app.route('/web-chat', methods=['POST'])
def web_chat():
    username = request.form.get('username')
    message = request.form.get('message')
    channel_id = int(request.form.get('channel_id'))
    timestamp = datetime.now().strftime("%H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = cursor.fetchone()[0]
    if not is_safe(message):
        cursor.execute("INSERT INTO safety_alerts (user_id, blocked_content, timestamp) VALUES (?, ?, ?)", (user_id, message, timestamp))
        conn.commit()
        conn.close()
        return "<h3>⚠️ Message blocked! Keep chats nice.</h3><a href='javascript:history.back()'>Go Back</a>"
    cursor.execute("INSERT INTO chats (user_id, message, timestamp, channel_id) VALUES (?, ?, ?, ?)", (user_id, message, timestamp, channel_id))
    conn.commit()
    conn.close()
    return redirect(f"/dashboard?username={username}&channel_id={channel_id}")

@app.route('/web-friend-chat', methods=['POST'])
def web_friend_chat():
    username = request.form.get('username')
    message = request.form.get('message')
    target_friend_id = int(request.form.get('target_friend_id'))
    timestamp = datetime.now().strftime("%H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = cursor.fetchone()[0]
    if not is_safe(message):
        cursor.execute("INSERT INTO safety_alerts (user_id, blocked_content, timestamp) VALUES (?, ?, ?)", (user_id, message, timestamp))
        conn.commit()
        conn.close()
        return "<h3>⚠️ Note blocked! Keep chats nice.</h3><a href='javascript:history.back()'>Go Back</a>"
    cursor.execute("INSERT INTO friend_chats (sender_id, receiver_id, message, timestamp) VALUES (?, ?, ?, ?)", (user_id, target_friend_id, message, timestamp))
    conn.commit()
    conn.close()
    return redirect(f"/dashboard?username={username}&target_friend_id={target_friend_id}")

if __name__ == '__main__':
    init_db()
    # UPDATED: Allows other network devices to connect
    app.run(host='0.0.0.0', port=9000)
