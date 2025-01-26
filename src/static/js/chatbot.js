document.getElementById("chatbot-send").addEventListener("click", function() {
    const userMessage = document.getElementById("chatbot-input").value;
    if (userMessage.trim() === "") return;  // Don't send empty messages

    // Display user message in the chat
    displayMessage(userMessage, "user");

    // Clear input field
    document.getElementById("chatbot-input").value = "";

    // Display loading dots while waiting for the response
    document.getElementById("loading-indicator").style.display = 'inline-block';

    // Send message to the backend
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        // Hide the loading dots once the response is received
        document.getElementById("loading-indicator").style.display = 'none';

        if (data.response) {
            // Display the bot's reply
            displayMessage(data.response, "bot");
        } else if (data.error) {
            // Display the error message
            displayMessage(data.error, "bot");
        }
    })
    .catch(error => {
        // In case of network or other errors, hide the loading dots and display a generic error message
        document.getElementById("loading-indicator").style.display = 'none';
        console.error('Error:', error);
        displayMessage("Oops! Something went wrong. Please try again.", "bot");
    });
});

// Function to display messages in the chat
function displayMessage(message, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("chatbot-message");
    messageDiv.classList.add(sender === "bot" ? "bot-message" : "user-message");
    messageDiv.textContent = message;

    // Append the message to the chatbot body
    const chatbotBody = document.getElementById("chatbot-body");
    chatbotBody.appendChild(messageDiv);

    // Ensure the chatbot scrolls to the bottom to show the latest message
    scrollToBottom();
}

// Scroll to the bottom of the chatbot body
function scrollToBottom() {
    const chatbotBody = document.getElementById("chatbot-body");
    chatbotBody.scrollTop = chatbotBody.scrollHeight;
}

// Automatically scroll to the bottom when user starts typing
document.getElementById("chatbot-input").addEventListener("focus", function() {
    scrollToBottom();
});
