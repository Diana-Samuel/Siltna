// Init SocketIO
const socket = io();

var userName;
var otherName;

// send signal about joining chat for status
document.addEventListener("DOMContentLoaded", () => {
    socket.emit("joinChat", { chatid: chatId });
    socket.on("receiveNames", data => {
        if (data.senderId == userId) {
            userName = data.senderName;
            otherName = data.receiverName;
        }
        else {
            userName = data.receiverName;
            otherName = data.senderName;
        };
        document.querySelector("#userName").textContent = userName;
        document.querySelector("#otherName").textContent = otherName;


        const msgsUrl = `/c/${chatId}/msgs`;
        fetch(msgsUrl)
            .then(response => response.json())
            .then(data => {
                let messages = data.messages;
                messages.forEach(msg => {
                    let sender;
                    if (msg.senderId == userId) {
                        sender = userName;
                    }
                    else {
                        sender = otherName;
                    };
                    let message = msg.message;
                    addToChat(sender, message);
                });
            })
            .catch(error => console.error(error));
    });
});



window.addEventListener("beforeunload", () => {
    socket.emit("leaveChat", { chatid: chatId });
});


function sendMessage() {
    const input = document.querySelector("#message");
    let msg = input.value.trim();
    socket.emit("send_message",{chatid: chatId, message: msg});
    input.value = "";
}

function addToChat(userid,message) {
    const box = document.getElementById("messages");
    const msgDiv = document.createElement("div");
    msgDiv.className = "message " + userid;
    msgDiv.textContent = `[${userid}] ${message}`;
    box.appendChild(msgDiv);
    box.scrollTop = box.scrollHeight;
}

socket.on("receive_message", data => {
    let sender;
    if (userId == data.senderId) {
        sender = userName;
    }
    else {
        sender = otherName;
    }
    addToChat(sender, data.message);
});

