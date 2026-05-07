import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key_123"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet"
)

users = {}

@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("join")
def handle_join(username):
    users[request.sid] = username

    emit(
        "update_users",
        list(users.values()),
        broadcast=True
    )


@socketio.on("disconnect")
def handle_disconnect():
    if request.sid in users:
        del users[request.sid]

        emit(
            "update_users",
            list(users.values()),
            broadcast=True
        )


@socketio.on("send_message")
def handle_message(data):
    emit(
        "receive_message",
        {
            "user": data["user"],
            "text": data["text"]
        },
        broadcast=True
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    socketio.run(
        app,
        host="0.0.0.0",
        port=port
    )
