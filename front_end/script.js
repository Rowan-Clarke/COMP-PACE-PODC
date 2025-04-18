const header=document.getElementById('header');
const body=document.getElementById('chat_body');
const sendBtn=document.getElementById('send_btn');
const input =document.getElementById('chat_input');  // css elements implemented into JavaScript
const msg=document.getElementById('messages');

header.onclick=()=>{
    body.style.display=body.style.display==='none' ? 'flex': 'none';  // Opens chat when clicked on.
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

    setTimeout(()=>{
        appendMessage('bot', 'Bot: '+text);  // Bot response, replace with API Call
                                            // for now this mimics the input as the response, to fix
    }, 400);
}

function appendMessage(sender, text){         // Displays a new message within the chat window
    const message=document.createElement('div');
    message.className=`msg ${sender}`;
    message.textContent=text;
    msg.appendChild(message);   // Message is added into the chat window.
    msg.scrollTop=msg.scrollHeight;  // Automatically scrolls to the bottom to display most recent message.
}