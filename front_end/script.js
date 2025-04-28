const header=document.getElementById('header');
const body=document.getElementById('chat_body');
const sendBtn=document.getElementById('send_btn');
const input =document.getElementById('chat_input');  // css elements implemented into JavaScript
const msg=document.getElementById('messages');
const chatbot = document.querySelector('.chatbot_design');  // <-- get the main container
const arrow = document.getElementById('arrow');

let introMessage=false;

header.onclick = () => {
    if (body.style.maxHeight && body.style.maxHeight !== "0px") {
        body.style.maxHeight = "0px"; // smoothly close
        body.style.padding = "0";
        chatbot.classList.remove('open'); // shrink width
        arrow.style.transform="rotate(0deg)";
    } else {
        body.style.maxHeight = "600px"; // smoothly open
        body.style.padding = "10px";
        chatbot.classList.add('open'); // expand width
        arrow.style.transform="rotate(180deg)";

        if (!introMessage){
            appendMessage('bot', "Hi! I'm the PODC Assistant! Ask any question about hearing or hearing loss below, I'll be happy to help :)");
            introMessage=true;
        }
    }
};

sendBtn.onclick =sendMessage;
input.addEventListener('keypress',e=>{ 
    if (e.key==='Enter') sendMessage();   // user presses 'Enter' to send their input as message.
});

function sendMessage(){
    const text=input.value.trim();
    if (!text) return;

    appendMessage('user', text);
    input.value='';

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
            appendMessage('bot', data.response, data.citations);
        } else {
            appendMessage('bot', "Sorry, something went wrong.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        appendMessage('bot', "Sorry, something went wrong.");
    });
}

function appendMessage(sender, text, citations = []) {
    const message = document.createElement('div');
    message.className = `msg ${sender}`;
    
    // Add the main response text
    const responseText = document.createElement('div');
    responseText.className = 'response-text';
    responseText.innerHTML = marked.parse(text);
    message.appendChild(responseText);
    
    // Add unique citations if they exist
    if (citations && citations.length > 0) {
        // Remove duplicate citations
        const uniqueCitations = citations.filter((citation, index, self) =>
            index === self.findIndex((c) => c.filename === citation.filename)
        );
        
        if (uniqueCitations.length > 0) {
            const citationsList = document.createElement('div');
            citationsList.className = 'citations';
            
            const citationHeader = document.createElement('div');
            citationHeader.className = 'citation-header';
            citationHeader.textContent = 'Sources:';
            citationsList.appendChild(citationHeader);
            
            uniqueCitations.forEach(citation => {
                const citationItem = document.createElement('div');
                citationItem.className = 'citation-item';
                // Clean up filename by removing file extension
                const cleanFileName = citation.filename.replace(/\.[^/.]+$/, "");
                citationItem.textContent =  cleanFileName;;
                citationsList.appendChild(citationItem);
            });
            
            message.appendChild(citationsList);
        }
    }
    
    msg.appendChild(message);
    msg.scrollTop = msg.scrollHeight;
}