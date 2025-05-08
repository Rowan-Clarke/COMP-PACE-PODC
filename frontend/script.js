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
 
     // Update to use Render backend URL
     // Show loading spinner
     const loading = document.getElementById('loading');
     loading.style.display = 'block';
 
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
        // Filter unique citations based on filename
        const uniqueCitations = citations.filter((citation, index, self) =>
            index === self.findIndex(c => c.filename === citation.filename)
        );

        const citationsList = document.createElement('ul');
        citationsList.className = 'citations-list';

        uniqueCitations.forEach(citation => {
            const li = document.createElement('li');
            
            // Create the citation text with hyperlink
            if (citation.metadata && citation.metadata.url) {
                // If URL exists in metadata, create a hyperlink
                const link = document.createElement('a');
                link.href = citation.metadata.url;
                link.target = '_blank'; // Open in new tab
                link.rel = 'noopener noreferrer'; // Security best practice
                link.textContent = citation.filename;
                li.textContent = 'Source: ';
                li.appendChild(link);
            } else {
                // Fallback for citations without URLs
                li.textContent = `Source: ${citation.filename}`;
            }
            
            citationsList.appendChild(li);
        });

        message.appendChild(citationsList);
    }

    msg.appendChild(message);
    msg.scrollTop = msg.scrollHeight;
}