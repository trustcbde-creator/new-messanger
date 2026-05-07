import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# В реальном проекте используйте случайную строку для безопасности
app.config['SECRET_KEY'] = 'secret_key_123'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Словарь для хранения пользователей {id_сессии: имя}
users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(username):
    # Сохраняем пользователя по его уникальному ID сессии
    users[request.sid] = username
    print(f"User {username} joined")
    # Рассылаем всем обновленный список имен
    emit('update_users', list(users.values()), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in users:
        print(f"User {users[request.sid]} disconnected")
        del users[request.sid]
        # Обновляем список у всех оставшихся
        emit('update_users', list(users.values()), broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    # Пробрасываем сообщение всем пользователям
    emit('receive_message', {
        'user': data['user'],
        'text': data['text']
    }, broadcast=True)

if __name__ == '__main__':
    # Порт для хостинга берется из переменной окружения PORT
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
