// Init SocketIO
const socket = io();

// send signal about joining chat for status
document.addEventListener("DOMContentLoaded", () => {
    socket.emit("joinChat",{ chatid: chatId });
    fetch("/c/${chatId}/msgs")
    .then(response => response.json())
    .then(data => {
        let messages = data.messages;
        messages.forEach(msg => {
            if (msg.senderId == userId) {
                let sender = "Me"
            }
            else {
                let sender = "Other"
            };
            let message = msg.message;
            addToChat(sender,message);
        }); 
    })
    .catch(error => console.error(error));
});


window.addEventListener("onbeforeunload", () => {
    socket.emit("leaveChat",{ chatid: chatId });
});


function sendMessage() {
    const input = document.querySelector("#message");
    let msg = input.value.trim();
    socket.emit("send_message",{chatid: chatid, message: msg});
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

socket.on("recieve_message", data => {
    const box = document.getElementById("messages");
    const msgDiv = document.createElement("div");
    msgDiv.className = "message " + (data.userid);
    msgDiv.textContent = `[${data.userid}] ${data.message}`;
    box.appendChild(msgDiv);
    box.scrollTop = box.scrollHeight;
});