document.getElementById("chatbot-send").addEventListener("click", function() {
    const userMessage = document.getElementById("chatbot-input").value;
    if (userMessage.trim() === "") return;  // Don't send empty messages

    // Display user message in the chat
    displayMessage(userMessage, "user");

    // Clear input field
    document.getElementById("chatbot-input").value = "";

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
        if (data.response) {
            // Display the bot's reply
            displayMessage(data.response, "bot");
        } else if (data.error) {
            // Display the error message
            displayMessage(data.error, "bot");
        }
    })
    .catch(error => {
        // In case of network or other errors, display a generic error message
        console.error('Error:', error);
        displayMessage("Oops! Something went wrong. Please try again.", "bot");
    });
});

function displayMessage(message, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("chatbot-message");
    messageDiv.classList.add(sender === "bot" ? "bot-message" : "user-message");
    messageDiv.textContent = message;
    
    document.getElementById("chatbot-body").appendChild(messageDiv);
    document.getElementById("chatbot-body").scrollTop = document.getElementById("chatbot-body").scrollHeight; // Scroll to the latest message
}
