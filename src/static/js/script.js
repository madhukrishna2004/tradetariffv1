function playMessageSound() {
    let sound = document.getElementById("message-sound");
    sound.play().catch(error => console.log("Audio play blocked:", error));
}

function addChatbotMessage(text) {
    let chatBox = document.getElementById("chatbot-body");
    let botMessage = `<div class="chatbot-message bot-message"><strong></strong> ${text}</div>`;
    chatBox.innerHTML += botMessage;
    chatBox.scrollTop = chatBox.scrollHeight;

    // Play sound when a new bot message is added
    playMessageSound();
}

function sendMessage() {
    let userInput = document.getElementById("chatbot-input").value;
    let chatBox = document.getElementById("chatbot-body");

    if (userInput.trim() === "") return;

    let userMessage = `<div class="chatbot-message user-message"><strong></strong> ${userInput}</div>`;
    chatBox.innerHTML += userMessage;
    document.getElementById("chatbot-input").value = "";

    // Check if the response is already in local storage
    let cachedResponse = localStorage.getItem(userInput);
    if (cachedResponse) {
        addChatbotMessage(cachedResponse);
        return;
    }

    // Show loading message
    let loadingMessage = `<div class="chatbot-message bot-message" id="loading">...</div>`;
    chatBox.innerHTML += loadingMessage;
    chatBox.scrollTop = chatBox.scrollHeight;

    fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: userInput })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("loading").remove(); // Remove loading message
        addChatbotMessage(data.response);

        // Store the response in local storage
        localStorage.setItem(userInput, data.response);
    })
    .catch(error => {
        document.getElementById("loading").remove(); // Remove loading message
        console.error("Error:", error);
    });
}

async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    const audioChunks = [];
    const chatBox = document.getElementById("chatbot-body");

    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'audio.wav');

        // Show loading message
        let loadingMessage = `<div class="chatbot-message bot-message" id="loading">...</div>`;
        chatBox.innerHTML += loadingMessage;
        chatBox.scrollTop = chatBox.scrollHeight;

        const response = await fetch('/voice', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        document.getElementById("loading").remove(); // Remove loading message
        addChatbotMessage(data.response);
    };

    mediaRecorder.start();

    setTimeout(() => {
        mediaRecorder.stop();
    }, 5000); // Record for 5 seconds
}

// Integrate send button with Enter key
document.getElementById("chatbot-input").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});
