import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet"
)

# {sid: username}
users = {}

# {username: sid}
user_sids = {}

@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("join")
def handle_join(username):

    users[request.sid] = username
    user_sids[username] = request.sid

    emit(
        "update_users",
        list(user_sids.keys()),
        broadcast=True
    )


@socketio.on("disconnect")
def handle_disconnect():

    if request.sid in users:

        username = users[request.sid]

        del users[request.sid]

        if username in user_sids:
            del user_sids[username]

        emit(
            "update_users",
            list(user_sids.keys()),
            broadcast=True
        )


@socketio.on("private_message")
def handle_private_message(data):

    target = data["target"]
    sender = data["user"]
    text = data["text"]

    if target in user_sids:

        target_sid = user_sids[target]

        emit(
            "receive_private_message",
            {
                "user": sender,
                "text": text
            },
            room=target_sid
        )

        # Отправляем и себе
        emit(
            "receive_private_message",
            {
                "user": sender,
                "text": text
            },
            room=request.sid
        )


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    socketio.run(
        app,
        host="0.0.0.0",
        port=port
    )
