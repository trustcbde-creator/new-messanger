import eventlet
eventlet.monkey_patch()

import os
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify
)

from flask_socketio import SocketIO, emit

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# --------------------
# Flask
# --------------------

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --------------------
# SocketIO
# --------------------

socketio = SocketIO(
    app,
    cors_allowed_origins='*',
    async_mode='eventlet'
)

# --------------------
# Database
# --------------------

db = SQLAlchemy(app)

# --------------------
# Online users
# --------------------

online_users = {}

# --------------------
# Models
# --------------------

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(300),
        nullable=False
    )

    avatar = db.Column(
        db.String(500),
        default='https://cdn-icons-png.flaticon.com/512/149/149071.png'
    )

    created = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Message(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    sender = db.Column(
        db.String(50),
        nullable=False
    )

    receiver = db.Column(
        db.String(50),
        nullable=False
    )

    text = db.Column(
        db.Text,
        nullable=False
    )

    time = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

# --------------------
# Create database
# --------------------

with app.app_context():
    db.create_all()

# --------------------
# Routes
# --------------------

@app.route('/')
def index():

    if 'user' in session:
        return redirect('/chat')

    return render_template('login.html')


@app.route('/chat')
def chat():

    if 'user' not in session:
        return redirect('/')

    return render_template(
        'chat.html',
        username=session['user']
    )


@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# --------------------
# Register
# --------------------

@app.route('/register', methods=['POST'])
def register():

    data = request.json

    username = data.get('username')
    password = data.get('password')

    if not username or not password:

        return jsonify({
            'success': False,
            'message': 'Заполните все поля'
        })

    user_exists = User.query.filter_by(
        username=username
    ).first()

    if user_exists:

        return jsonify({
            'success': False,
            'message': 'Пользователь уже существует'
        })

    hashed_password = generate_password_hash(password)

    new_user = User(
        username=username,
        password=hashed_password
    )

    db.session.add(new_user)

    db.session.commit()

    return jsonify({
        'success': True
    })

# --------------------
# Login
# --------------------

@app.route('/login', methods=['POST'])
def login():

    data = request.json

    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(
        username=username
    ).first()

    if not user:

        return jsonify({
            'success': False,
            'message': 'Аккаунт не найден'
        })

    if not check_password_hash(user.password, password):

        return jsonify({
            'success': False,
            'message': 'Неверный пароль'
        })

    session['user'] = username

    return jsonify({
        'success': True
    })

# --------------------
# Users API
# --------------------

@app.route('/users')
def users():

    all_users = User.query.all()

    result = []

    for user in all_users:

        result.append({
            'username': user.username,
            'avatar': user.avatar,
            'online': user.username in online_users
        })

    return jsonify(result)

# --------------------
# Messages API
# --------------------

@app.route('/messages/<target>')
def messages(target):

    if 'user' not in session:
        return jsonify([])

    me = session['user']

    msgs = Message.query.filter(
        (
            (Message.sender == me) &
            (Message.receiver == target)
        ) |
        (
            (Message.sender == target) &
            (Message.receiver == me)
        )
    ).order_by(Message.time.asc()).all()

    result = []

    for msg in msgs:

        result.append({
            'sender': msg.sender,
            'text': msg.text,
            'time': msg.time.strftime('%H:%M')
        })

    return jsonify(result)

# --------------------
# Socket connect
# --------------------

@socketio.on('connect')
def handle_connect():

    if 'user' in session:

        online_users[session['user']] = request.sid

        emit(
            'online_update',
            broadcast=True
        )

# --------------------
# Socket disconnect
# --------------------

@socketio.on('disconnect')
def handle_disconnect():

    if 'user' in session:

        username = session['user']

        if username in online_users:
            del online_users[username]

        emit(
            'online_update',
            broadcast=True
        )

# --------------------
# Send message
# --------------------

@socketio.on('send_message')
def handle_send_message(data):

    if 'user' not in session:
        return

    sender = session['user']

    receiver = data.get('receiver')

    text = data.get('text')

    if not receiver or not text:
        return

    msg = Message(
        sender=sender,
        receiver=receiver,
        text=text
    )

    db.session.add(msg)

    db.session.commit()

    payload = {
        'sender': sender,
        'text': text,
        'time': datetime.utcnow().strftime('%H:%M')
    }

    # Отправляем получателю
    if receiver in online_users:

        emit(
            'receive_message',
            payload,
            room=online_users[receiver]
        )

    # Отправляем себе
    emit(
        'receive_message',
        payload,
        room=request.sid
    )

# --------------------
# Run
# --------------------

if __name__ == '__main__':

    port = int(os.environ.get('PORT', 10000))

    socketio.run(
        app,
        host='0.0.0.0',
        port=port
    )
