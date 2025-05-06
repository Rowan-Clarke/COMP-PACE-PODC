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
    const text = input.value.trim();
    if (!text) return;

    appendMessage('user', text);
    input.value = '';

    // Create a placeholder message for the bot
    const botMessageId = 'bot-message-' + Date.now();
    appendPlaceholderMessage('bot', botMessageId);

    // Show loading spinner
    const loading = document.getElementById('loading');
    loading.style.display = 'block';

    const eventSource = new EventSource(`https://podc-chatbot-backend-v2.onrender.com/chat?message=${encodeURIComponent(text)}`);
    let fullResponse = '';
    let citations = [];

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'text') {
            fullResponse += data.content;
            updateBotMessage(botMessageId, fullResponse, citations);
        } else if (data.type === 'citations') {
            citations = data.content;
            updateBotMessage(botMessageId, fullResponse, citations);
        }
    };

    eventSource.onerror = (error) => {
        console.error('EventSource failed:', error);
        eventSource.close();
        loading.style.display = 'none';
        if (!fullResponse) {
            updateBotMessage(botMessageId, 'Sorry, something went wrong.', []);
        }
    };
}

function appendPlaceholderMessage(sender, messageId) {
    const message = document.createElement('div');
    message.className = `msg ${sender}`;
    message.id = messageId;
    msg.appendChild(message);
    msg.scrollTop = msg.scrollHeight;
}

function updateBotMessage(messageId, text, citations) {
    const message = document.getElementById(messageId);
    if (!message) return;

    // Update main text
    let responseText = message.querySelector('.response-text');
    if (!responseText) {
        responseText = document.createElement('div');
        responseText.className = 'response-text';
        message.appendChild(responseText);
    }
    responseText.innerHTML = marked.parse(text);

    // Update citations
    if (citations && citations.length > 0) {
        let citationsList = message.querySelector('.citations');
        if (!citationsList) {
            citationsList = document.createElement('div');
            citationsList.className = 'citations';
            message.appendChild(citationsList);
        }

        citationsList.innerHTML = ''; // Clear existing citations
        
        const citationHeader = document.createElement('div');
        citationHeader.className = 'citation-header';
        citationHeader.textContent = 'Sources:';
        citationsList.appendChild(citationHeader);

        const uniqueCitations = citations.filter((citation, index, self) =>
            index === self.findIndex((c) => c.filename === citation.filename)
        );

        uniqueCitations.forEach(citation => {
            const citationItem = document.createElement('div');
            citationItem.className = 'citation-item';
            const cleanFileName = citation.filename.replace(/\.[^/.]+$/, "");
            citationItem.textContent = cleanFileName;
            citationsList.appendChild(citationItem);
        });
    }

    msg.scrollTop = msg.scrollHeight;
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