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
 let hasEnded = false; // Track if the chat has ended
 let lastBotResponse = ''; // Track the last response from the bot
 let chatHistory = []; // Stores short-term memory
 const maxHistoryLength = 4; // 2 user-bot exchanges
 let feedbackMode = false; // Track if feedback mode is active
 let currentFetchController = null; // Track the current fetch request controller

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
 
function sendMessage() {
    if (feedbackMode || hasEnded) return;  // Block if feedback or chat ended

    const text = input.value.trim();
    if (!text) return;

    lastUserMessage = text;
    appendMessage('user', text);
    input.value = '';

    const loading = document.getElementById('loading');
    loading.style.display = 'block';

    input.disabled = true;
    sendBtn.disabled = true;
    sendBtn.style.opacity = 0.6;
    sendBtn.style.cursor = 'not-allowed';
    input.placeholder = "Please wait...";

    // Abort any previous fetch
    if (currentFetchController) {
        currentFetchController.abort();
    }

    currentFetchController = new AbortController();
    const signal = currentFetchController.signal;

    fetch('https://podc-chatbot-backend-v2.onrender.com/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: text,
            history: chatHistory
        }),
        signal: signal
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (hasEnded) return;  // Prevent response from showing after chat end

        loading.style.display = 'none';

        if (data.response) {
            appendMessage('bot', data.response, data.citations);
            chatHistory.push({ role: 'user', message: lastUserMessage });
            chatHistory.push({ role: 'assistant', message: data.response });

            if (chatHistory.length > maxHistoryLength) {
                chatHistory = chatHistory.slice(-maxHistoryLength);
            }
        } else {
            appendMessage('bot', "No response received from server");
        }
    })
    .catch(error => {
        if (error.name === 'AbortError') {
            console.log('Fetch aborted due to chat end');
            loading.style.display = 'none'; // Hide spinner
            input.placeholder = "Chat ended. Please leave your feedback.";
            return;
        }
        console.error('Detailed error:', error.message);
        loading.style.display = 'none';
        appendMessage('bot', "Sorry, something went wrong. Error: " + error.message);
    })
    .finally(() => {
        currentFetchController = null; // Clean up after fetch completes
        
        if (!hasEnded) {
            input.disabled = false;
            sendBtn.disabled = false;
            sendBtn.style.opacity = 1;
            sendBtn.style.cursor = 'pointer';
            input.placeholder = "Ask a question...";
            input.focus();
        }
    });
}

 
 function appendMessage(sender, text, citations = []) {
    const message = document.createElement('div');
    message.className = `msg ${sender}`;

    // Add the main response text
    const responseText = document.createElement('div');
    responseText.className = 'response-text';
    responseText.innerHTML = marked.parse(text);
    if (sender === 'bot' &&
        !text.includes("Are you sure you want to end the conversation?") &&
        !text.includes("Thank you for chatting!") &&
        !text.includes("To chat with us") &&
        !text.includes("Rate your experience") &&
        !text.includes("Thanks for visiting")) {
        lastBotResponse = text;
    }

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
            
            // Get title and author from metadata
            const title = citation.metadata?.title;
            const author = citation.metadata?.author;
            
            // Clean the filename by removing _NEW.pdf and _OLD.pdf
            const cleanedFileName = cleanFileName(citation.filename);
            
            // Create display text based on available metadata
            let displayText;
            if (title && author) {
                displayText = `${title} - ${author}`;
            } else {
                displayText = cleanedFileName;
            }
            
            if (url) {
                const link = document.createElement('a');
                link.href = url;
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.textContent = displayText;
                
                li.textContent = 'Source: ';
                li.appendChild(link);
            } else {
                li.textContent = `Source: ${displayText}`;
            }
            
            citationsList.appendChild(li);
        });

        message.appendChild(citationsList);
    }

    // End chat feature, asks rating/feedback from user afterwards.

    document.getElementById('end_chatBtn').onclick=function(){
        if (hasEnded) {
            resetChat();
            return;
        }
        if (currentFetchController) {
            currentFetchController.abort();
        }

        const end_btn = this;
        end_btn.disabled = true;
        appendMessage('bot',"Are you sure you want to end the conversation? <div><button id=\"end_yesBtn\">Yes</button><button id=\"end_noBtn\">No</button></div>"); // confirmation message

        setTimeout(()=>{
            // const confirmMsg = document.querySelector('.message.bot:last-child');
            document.getElementById('end_yesBtn').onclick=()=>{    
                end_btn.disabled = false;
                document.getElementById('end_yesBtn').parentElement.remove();  // removes the buttons after user selects

                if (!lastUserMessage) {
                    appendMessage('bot', "Thanks for visiting! Let us know if you have any questions.");
                    return;
                }
                
                appendMessage('bot',"Thank you for chatting! Rate your experience with us!");  // if Yes is clicked
                document.getElementById('end_chatBtn').textContent = "Restart Chat";
                hasEnded = true;

                // Lock input while feedback window is open
                feedbackMode = true;
                input.disabled = true;
                sendBtn.disabled = true;
                sendBtn.style.opacity = 0.6;
                sendBtn.style.cursor = 'not-allowed';
                input.placeholder = "Chat ended. Please leave your feedback.";
                document.querySelector('.input_box').classList.add('locked');

                setTimeout(() => {
                    const wrapper = document.createElement('div');
                    wrapper.className = 'msg bot'; // same style as other bot messages

                    const feedbackContent = `
                        <div class="feedback-card">
                            <p>Please rate your experience:</p>
                            <div id="star_rating" class="star-rating">
                                <span data-value="1">★</span>
                                <span data-value="2">★</span>
                                <span data-value="3">★</span>
                                <span data-value="4">★</span>
                                <span data-value="5">★</span>
                            </div>
                            <input type="hidden" id="rating_value" value="">
                            <textarea id="feedback_text" placeholder="Leave feedback (optional)" rows="3"></textarea>
                            <button id="submit_feedback">Submit Feedback</button>
                        </div>
                    `;

                    wrapper.innerHTML = feedbackContent;
                    msg.appendChild(wrapper);

                    const stars = wrapper.querySelectorAll('#star_rating span');
                    const ratingInput = wrapper.querySelector('#rating_value');

                    stars.forEach(star => {
                        star.addEventListener('mouseenter', () => {
                            const val = parseInt(star.dataset.value);
                            stars.forEach(s => {
                                s.classList.toggle('hovered', parseInt(s.dataset.value) <= val);
                            });
                        });
                        star.addEventListener('mouseleave', () => {
                            stars.forEach(s => s.classList.remove('hovered'));
                        });
                        star.addEventListener('click', () => {
                            const val = parseInt(star.dataset.value);
                            ratingInput.value = val;
                            stars.forEach(s => {
                                s.classList.toggle('selected', parseInt(s.dataset.value) <= val);
                            });
                        });
                    });

                    msg.scrollTop = msg.scrollHeight;

                    document.getElementById('submit_feedback').onclick = () => {
                        const rating = document.getElementById('rating_value').value;
                        const feedback = document.getElementById('feedback_text').value.trim();
                        const submitBtn = document.getElementById('submit_feedback');
                        submitBtn.disabled = true;
                        input.disabled = true;
                        sendBtn.disabled = true;
                        sendBtn.style.opacity = 0.6;
                        sendBtn.style.cursor = 'not-allowed';
                        input.placeholder = "Chat ended. Restart to ask another question.";

                        if (!rating) {
                            alert("Please select a rating.");
                            return;
                        }

                        fetch('https://podc-chatbot-backend-v2.onrender.com/feedback', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                rating: parseInt(rating),
                                feedback: feedback,
                                user_prompt: lastUserMessage,
                                response: lastBotResponse,
                                timestamp: new Date().toISOString()
                            })
                        }).then(() => {
                            alert('Thanks for your feedback!');
                            wrapper.remove();
                        }).catch(() => {
                            alert('Error submitting feedback. Please try again later.');
                        });
                    };
                }, 300);
            };

            document.getElementById('end_noBtn').onclick=()=>{
                appendMessage('bot', "No problem, how can I help? :)");  // if No is clicked
                end_btn.disabled = false;
                document.getElementById('end_noBtn').parentElement.remove(); // removes the buttons after user selects
            };
        }, 100);
    };

    // Flagging feature
    if (
        sender === 'bot' &&
        !text.includes("To consent discussing sensitive information") &&
        !text.includes("Thank you for accepting") &&
        !text.includes("To chat with us, you need to press Accept :)") && 
        !text.includes("Are you sure you want to end the conversation?") &&
        !text.includes("No problem, how can I help? :)") &&
        !text.includes("Thank you for chatting! Rate your experience with us!") &&
        !text.includes("Thanks for visiting! Let us know if you have any questions.")
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
                    
                    input.placeholder = "Ask a question...";  // placeholder text is reset

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

function resetChat() {
    msg.innerHTML = '';
    lastUserMessage = '';
    introMessage = false;
    hasEnded = false;
    userAccepted = false; // Reset consent state
    feedbackMode = false;
    input.value = ''; // Clear unsent input
    chatHistory = []; // Clear memory

    document.getElementById('end_chatBtn').textContent = 'End Chat';

    // disable input until user accepts again
    input.disabled = true;
    sendBtn.disabled = true;
    sendBtn.style.opacity = 0.6;
    sendBtn.style.cursor = 'not-allowed';
    input.placeholder = "Please accept to start chatting...";
    document.querySelector('.input_box').classList.remove('locked');

    appendMessage('bot', "Hi! I'm the PODC Assistant! Ask any question about hearing or hearing loss below, I'll be happy to help :) \n To consent discussing sensitive information, please press Accept. <div><button id=\"accept_bttn\">Accept</button><button id=\"decline_bttn\">Decline</button></div>");
}

};