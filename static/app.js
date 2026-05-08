const socket = io({

        div.innerHTML = `
            <img src="${user.avatar}">

            <div>
                <div>${user.username}</div>
                <div class="status">
                    ${user.online ? '🟢 В сети' : '⚫ Не в сети'}
                </div>
            </div>
        `

        div.onclick = () => openChat(user.username)

        usersDiv.appendChild(div)
    })
}


async function openChat(user){

    currentChat = user

    document.getElementById('chat-header').innerText = user

    const req = await fetch('/messages/' + user)

    const messages = await req.json()

    const msgDiv = document.getElementById('messages')

    msgDiv.innerHTML = ''

    messages.forEach(msg => {
        addMessage(msg)
    })
}


function addMessage(msg){

    const div = document.createElement('div')

    div.className =
        msg.sender === MY_NAME
        ? 'my-message'
        : 'their-message'

    div.innerHTML = `
        <div>${msg.text}</div>
        <small>${msg.time}</small>
    `

    document.getElementById('messages').appendChild(div)
}


function sendMessage(){

    const input = document.getElementById('message-input')

    if(input.value.trim() === '') return

    if(currentChat === '') return

    socket.emit('send_message', {
        receiver: currentChat,
        text: input.value
    })

    input.value = ''
}


socket.on('receive_message', msg => {

    if(currentChat === msg.sender || msg.sender === MY_NAME){
        addMessage(msg)
    }
})


socket.on('online_update', () => {
    loadUsers()
})


loadUsers()