window.onload = () => {
const header=document.getElementById('header');
 const body=document.getElementById('chat_body');
 const sendBtn=document.getElementById('send_btn');
 const input =document.getElementById('chat_input');  // css elements implemented into JavaScript
 const msg=document.getElementById('messages');
 const chatbot = document.querySelector('.chatbot_design');  // <-- get the main container
 const arrow = document.getElementById('arrow');
 
 let userAccepted = false; // user consent
 let introMessage=false;  // introduction message from bot
 let lastUserMessage = "";  // Track the last thing the user sent

 // Add this helper function at the top of your script
 function cleanFileName(filename) {
    return filename
        .replace(/_NEW\.pdf$/, '')
        .replace(/_OLD\.pdf$/, '');
 }

 // Disable chat input and send button until user accepts the consent form
 input.disabled = true;
 sendBtn.disabled = true;
 sendBtn.style.opacity = 0.6;
 sendBtn.style.cursor = 'not-allowed';

 
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
             appendMessage('bot', "Hi! I'm the PODC Assistant! Ask any question about hearing or hearing loss below, I'll be happy to help :) \n To consent discussing sensitive information, please press Accept. <div><button id=\"accept_bttn\">Accept</button><button id=\"decline_bttn\">Decline</button></div>");
             introMessage=true;
         }
     }
 };
 
 sendBtn.onclick =sendMessage;
 input.addEventListener('keypress',e=>{ 
     if (e.key==='Enter' && !input.disabled) sendMessage();   // user presses 'Enter' to send their input as message.
 });
 
 function sendMessage(){
     const text=input.value.trim();
     if (!text) return;
 
     lastUserMessage = text;
     appendMessage('user', text);  // user's message
     input.value='';
 
     // Update to use Render backend URL
     // Show loading spinner
     const loading = document.getElementById('loading');
     loading.style.display = 'block';
 

     // Disable input and send button
     input.disabled = true;
     sendBtn.disabled = true;
     sendBtn.style.opacity = 0.6;
     sendBtn.style.cursor = 'not-allowed';
     input.placeholder = "Please wait...";

     fetch('https://podc-chatbot-backend-v2.onrender.com/chat', {
         method: 'POST',
         headers: {
             'Content-Type': 'application/json'
         },
         body: JSON.stringify({ message: text })
     })
     .then(response => {
         if (!response.ok) {
             throw new Error(`HTTP error! status: ${response.status}`);
         }
         return response.json();
     })
     .then(data => {
         loading.style.display = 'none';
         // Add detailed debug logging
         console.log('Full response data:', data);
         console.log('Citations:', data.citations);
         if (data.citations) {
             data.citations.forEach(citation => {
                 console.log('Citation metadata:', {
                     filename: citation.filename,
                     url: citation.metadata?.url,
                     fileId: citation.file_id
                 });
             });
         }
         console.log('Response data:', data); // Add this debug log
         if (data.response) {
             appendMessage('bot', data.response, data.citations);
         } else {
             appendMessage('bot', "No response received from server");
         }
     })
     .catch(error => {
         console.error('Detailed error:', error.message);
         console.error('Full error object:', error);
         loading.style.display = 'none';
         appendMessage('bot', "Sorry, something went wrong. Error: " + error.message);
     })
     .finally(() => {
         // Re-enable input and button
         input.disabled = false;
         sendBtn.disabled = false;
         sendBtn.style.opacity = 1;
         sendBtn.style.cursor = 'pointer';
         input.placeholder = "Ask a question...";
         input.focus();
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

    // Add citations if they exist
    if (citations && citations.length > 0) {
        const uniqueCitations = citations.filter((citation, index, self) =>
            index === self.findIndex(c => c.filename === citation.filename)
        );

        const citationsList = document.createElement('ul');
        citationsList.className = 'citations-list';

        uniqueCitations.forEach(citation => {
            const li = document.createElement('li');
            const url = citation.metadata?.url;
            
            // Clean the filename by removing _NEW.pdf and _OLD.pdf
            const cleanedFileName = cleanFileName(citation.filename);
            
            if (url) {
                const link = document.createElement('a');
                link.href = url;
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.textContent = cleanedFileName;  // Use cleaned filename
                
                li.textContent = 'Source: ';
                li.appendChild(link);
            } else {
                li.textContent = `Source: ${cleanedFileName}`;  // Use cleaned filename
            }
            
            citationsList.appendChild(li);
        });

        message.appendChild(citationsList);
    }

    // Flagging feature
    if (
        sender === 'bot' &&
        !text.includes("To consent discussing sensitive information") &&
        !text.includes("Thank you for accepting") &&
        !text.includes("To chat with us, you need to press Accept :)")
    ) {
    
        const flagBtn = document.createElement('button');
        flagBtn.textContent = 'Flag';
        flagBtn.className = 'flag-btn';
        flagBtn.onclick = () => {
            // Prevent multiple flag submissions
            if (flagBtn.disabled) return;
            flagBtn.disabled = true;
            flagBtn.textContent = "Flagged";
            flagBtn.style.opacity = 0.6;

            fetch('https://podc-chatbot-backend-v2.onrender.com/flag', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    flaggedText: text,
                    userPrompt: lastUserMessage,
                    timestamp: new Date().toISOString()
                })
            }).then(() => {
                alert('Thanks for flagging. The team will review this response.');
            }).catch(() => {
                alert('Something went wrong while submitting your feedback.');
            });
        };
        message.appendChild(flagBtn);
    }

    msg.appendChild(message);
    msg.scrollTop = msg.scrollHeight;

    if(!userAccepted){
        setTimeout(()=>{
            
            const accept=document.getElementById('accept_bttn');
            const decline=document.getElementById('decline_bttn');

            if(accept && decline){    // accept and decline button options/logic
                accept.onclick=()=>{
                    userAccepted=true;
                    input.disabled=false;   // input box and send button are useable after user consents (pressing accept)
                    sendBtn.disabled=false;

                    // Reset cursor and opacity
                    sendBtn.style.cursor = 'pointer';
                    sendBtn.style.opacity = 1;

                    appendMessage('bot', "Thank you for accepting, How can I help? :)")  // thank you message
                    accept.disabled=true;
                    accept.style.display = 'none';  
                    decline.style.display = 'none';   // remove buttons after user makes decision
                };

                decline.onclick=()=>{
                    input.disabled=true;   // input box and send button are disabled until user consents.
                    sendBtn.disabled=true;
                    appendMessage('bot', "To chat with us, you need to press Accept :)")  // message is displayed until user accepts.
                };
            }
        }, 100);
    }
}
};