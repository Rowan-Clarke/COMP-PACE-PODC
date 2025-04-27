const header=document.getElementById('header');
const body=document.getElementById('chat_body');
const sendBtn=document.getElementById('send_btn');
const input =document.getElementById('chat_input');  // css elements implemented into JavaScript
const msg=document.getElementById('messages');

header.onclick = () => {
    if (body.style.maxHeight && body.style.maxHeight !== "0px") {
        body.style.maxHeight = "0px"; // smoothly close
    } else {
        body.style.maxHeight = "450px"; // smoothly open
    }
};

sendBtn.onclick =sendMessage;
input.addEventListener('keypress',e=>{ 
    if (e.key==='Enter') sendMessage();   // user presses 'Enter' to send their input as message.
});

function sendMessage(){
    const text=input.value.trim();
    if (!text) return;

    appendMessage('user', text);   // user input as text
    input.value='';    // sets input value as user's input

    fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: text })
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            appendMessage('bot', data.response);
        } else {
            appendMessage('bot', "Sorry, something went wrong.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        appendMessage('bot', "Sorry, something went wrong.");
    });
}

function appendMessage(sender, text){         // Displays a new message within the chat window
    const message=document.createElement('div');
    message.className=`msg ${sender}`;
    message.innerHTML = marked.parse(text);
    msg.appendChild(message);   // Message is added into the chat window.
    msg.scrollTop=msg.scrollHeight;  // Automatically scrolls to the bottom to display most recent message.
}