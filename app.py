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


@socketio.on('disconnect')
def disconnect():

    if 'user' in session:

        if session['user'] in online_users:
            del online_users[session['user']]

        emit('online_update', broadcast=True)


@socketio.on('send_message')
def send_message(data):

    sender = session['user']

    receiver = data['receiver']

    text = data['text']

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

    if receiver in online_users:

        emit(
            'receive_message',
            payload,
            room=online_users[receiver]
        )

    emit(
        'receive_message',
        payload,
        room=request.sid
    )


if __name__ == '__main__':

    port = int(os.environ.get('PORT', 10000))

    socketio.run(
        app,
        host='0.0.0.0',
        port=port
    )
