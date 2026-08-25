// ==========================================
// ChatMZK AI - Professional JavaScript
// ==========================================

// ===============================
// Global Variables
// ===============================

let currentChatId = null;
let isGenerating = false;


// ===============================
// Elements
// ===============================

const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const messages = document.getElementById("messages");
const newChatBtn = document.getElementById("newChatBtn");
const chatList = document.getElementById("chatList");

const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");

const clearChatBtn = document.getElementById("clearChatBtn");
const profileBtn = document.getElementById("profileBtn");
const shareBtn = document.getElementById("shareBtn");
const logoutBtn = document.getElementById("logoutBtn");

const typingIndicator =
    document.getElementById("typingIndicator");


// ===============================
// Scroll Bottom
// ===============================

function scrollBottom() {

    messages.scrollTo({

        top: messages.scrollHeight,

        behavior: "smooth"

    });

}


// ===============================
// Create Message
// ===============================

function createMessage(sender, text) {

    const div = document.createElement("div");

    if (sender === "user") {

        div.className = "user-message";

        div.innerHTML = `
            <strong>You</strong>
            <div class="message-text"></div>
        `;

    } else {

        div.className = "ai-message";

        div.innerHTML = `
            <strong>ChatMZK</strong>
            <div class="message-text"></div>
        `;

    }

    const textElement =
        div.querySelector(".message-text");

    textElement.textContent = text;

    messages.appendChild(div);

    scrollBottom();

    return div;

}


// ===============================
// Thinking Bubble
// ===============================

function createThinkingBubble() {

    const div = document.createElement("div");

    div.className = "ai-message";

    div.innerHTML = `
        <strong>ChatMZK</strong>
        <div class="message-text">
            <span class="thinking-dots">
                Thinking...
            </span>
        </div>
    `;

    messages.appendChild(div);

    scrollBottom();

    return div;

}


// ===============================
// Type AI Response
// ===============================

async function typeResponse(element, text) {

    element.innerHTML = `
        <strong>ChatMZK</strong>
        <div class="message-text"></div>
    `;

    const textElement =
        element.querySelector(".message-text");

    let i = 0;

    while (i < text.length) {

        textElement.textContent += text.charAt(i);

        i++;

        scrollBottom();

        await new Promise(resolve =>
            setTimeout(resolve, 10)
        );

    }

    addCopyButton(element, text);

}


// ===============================
// Copy Button
// ===============================

function addCopyButton(messageElement, text) {

    const button =
        document.createElement("button");

    button.className = "copy-btn";

    button.textContent = "📋 Copy";

    button.addEventListener("click", async function () {

        try {

            await navigator.clipboard.writeText(text);

            button.textContent = "✅ Copied";

            setTimeout(() => {

                button.textContent = "📋 Copy";

            }, 2000);

        } catch (error) {

            console.error(
                "Copy Error:",
                error
            );

        }

    });

    messageElement.appendChild(
        document.createElement("br")
    );

    messageElement.appendChild(button);

}


// ===============================
// Send Message
// ===============================

async function sendMessage() {

    if (isGenerating) return;

    const text = input.value.trim();

    if (!text) return;

    isGenerating = true;

    sendBtn.disabled = true;

    createMessage("user", text);

    input.value = "";

    input.style.height = "auto";

    const thinkingBubble =
        createThinkingBubble();

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {

                "Content-Type":
                    "application/json"

            },

            body: JSON.stringify({

                message: text

            })

        });

        if (!response.ok) {

            throw new Error(
                "Server returned " +
                response.status
            );

        }

        const data =
            await response.json();

        if (data.reply) {

            await typeResponse(
                thinkingBubble,
                data.reply
            );

        } else {

            thinkingBubble.innerHTML = `
                <strong>ChatMZK</strong>
                <div class="message-text">
                    ❌ No response received.
                </div>
            `;

        }

        await loadChats();

    }

    catch (error) {

        console.error(
            "Chat Error:",
            error
        );

        thinkingBubble.innerHTML = `
            <strong>ChatMZK</strong>
            <div class="message-text">
                ❌ Server Error. Please try again.
            </div>
        `;

    }

    finally {

        isGenerating = false;

        sendBtn.disabled = false;

        input.focus();

        scrollBottom();

    }

}


// ===============================
// Enter Key
// ===============================

input.addEventListener(
    "keydown",
    function (e) {

        if (
            e.key === "Enter" &&
            !e.shiftKey
        ) {

            e.preventDefault();

            sendMessage();

        }

    }
);


// ===============================
// Auto Resize Textarea
// ===============================

input.addEventListener(
    "input",
    function () {

        this.style.height = "auto";

        this.style.height =
            this.scrollHeight + "px";

    }
);


// ===============================
// Send Button
// ===============================

sendBtn.addEventListener(
    "click",
    sendMessage
);


// ===============================
// New Chat Button
// ===============================

newChatBtn.addEventListener(
    "click",
    createNewChat
);


// ===============================
// Load Chats
// ===============================

async function loadChats() {

    try {

        const response =
            await fetch("/get_chats");

        if (!response.ok) return;

        const chats =
            await response.json();

        chatList.innerHTML = "";

        chats.forEach(chat => {

            const item =
                createChatItem(chat);

            chatList.appendChild(item);

        });

    }

    catch (error) {

        console.error(
            "Load Chats Error:",
            error
        );

    }

}


// ===============================
// Create Chat Item
// ===============================

function createChatItem(chat) {

    const li =
        document.createElement("li");

    li.className = "chat-item";

    const title =
        document.createElement("span");

    title.className =
        "chat-item-title";

    title.textContent =
        chat.title || "New Chat";

    title.addEventListener(
        "click",
        function () {

            openChat(chat.id);

        }
    );

    const deleteBtn =
        document.createElement("button");

    deleteBtn.className =
        "delete-chat-btn";

    deleteBtn.textContent = "🗑";

    deleteBtn.title =
        "Delete chat";

    deleteBtn.addEventListener(
        "click",
        function (e) {

            e.stopPropagation();

            deleteChat(chat.id);

        }
    );

    li.appendChild(title);

    li.appendChild(deleteBtn);

    return li;

}


// ===============================
// Open Chat
// ===============================

async function openChat(chatId) {

    currentChatId = chatId;

    try {

        const response =
            await fetch(
                "/get_messages/" + chatId
            );

        if (!response.ok) {

            throw new Error(
                "Unable to load chat"
            );

        }

        const data =
            await response.json();

        messages.innerHTML = "";

        data.forEach(msg => {

            createMessage(
                msg.sender,
                msg.message
            );

        });

    }

    catch (error) {

        console.error(
            "Open Chat Error:",
            error
        );

    }

}


// ===============================
// Create New Chat
// ===============================

async function createNewChat() {

    try {

        const response =
            await fetch(
                "/new_chat",
                {
                    method: "POST"
                }
            );

        const data =
            await response.json();

        if (data.chat_id) {

            currentChatId =
                data.chat_id;

            messages.innerHTML = "";

            input.value = "";

            input.focus();

            await loadChats();

        }

    }

    catch (error) {

        console.error(
            "New Chat Error:",
            error
        );

    }

}


// ===============================
// Delete Chat
// ===============================

async function deleteChat(chatId) {

    const confirmed =
        confirm(
            "Delete this chat?"
        );

    if (!confirmed) return;

    try {

        const response =
            await fetch(
                "/delete_chat/" + chatId,
                {
                    method: "POST"
                }
            );

        const data =
            await response.json();

        if (data.success) {

            if (
                currentChatId === chatId
            ) {

                currentChatId = null;

                messages.innerHTML = "";

            }

            await loadChats();

        }

    }

    catch (error) {

        console.error(
            "Delete Chat Error:",
            error
        );

    }

}


// ===============================
// Clear Current Chat
// ===============================

async function clearChat() {

    const confirmed =
        confirm(
            "Clear current chat?"
        );

    if (!confirmed) return;

    try {

        const response =
            await fetch(
                "/clear_chat",
                {
                    method: "POST"
                }
            );

        const data =
            await response.json();

        if (data.success) {

            messages.innerHTML = "";

        }

    }

    catch (error) {

        console.error(
            "Clear Chat Error:",
            error
        );

    }

}


// ===============================
// Clear Button
// ===============================

if (clearChatBtn) {

    clearChatBtn.addEventListener(
        "click",
        clearChat
    );

}


// ===============================
// Upload Button
// ===============================

if (uploadBtn) {

    uploadBtn.addEventListener(
        "click",
        function () {

            fileInput.click();

        }
    );

}


// ===============================
// File Upload
// ===============================

if (fileInput) {

    fileInput.addEventListener(
        "change",
        async function () {

            if (!this.files.length) {
                return;
            }

            const file =
                this.files[0];

            fileName.textContent =
                file.name;

            const formData =
                new FormData();

            formData.append(
                "file",
                file
            );

            try {

                const response =
                    await fetch(
                        "/upload",
                        {
                            method: "POST",
                            body: formData
                        }
                    );

                const data =
                    await response.json();

                if (data.success) {

                    fileName.textContent =
                        "✅ " + data.filename;

                } else {

                    fileName.textContent =
                        "❌ " +
                        (data.message ||
                        "Upload failed");

                }

            }

            catch (error) {

                console.error(
                    "Upload Error:",
                    error
                );

                fileName.textContent =
                    "❌ Upload failed";

            }

        }
    );

}


// ===============================
// Profile Button
// ===============================

if (profileBtn) {

    profileBtn.addEventListener(
        "click",
        function () {

            window.location.href =
                "/profile";

        }
    );

}


// ===============================
// Logout Button
// ===============================

if (logoutBtn) {

    logoutBtn.addEventListener(
        "click",
        function () {

            window.location.href =
                "/logout";

        }
    );

}


// ===============================
// Share Button
// ===============================

if (shareBtn) {

    shareBtn.addEventListener(
        "click",
        async function () {

            const shareText =
                "Check out ChatMZK AI - Rehan Ahmad AI Assistant";

            try {

                if (
                    navigator.share
                ) {

                    await navigator.share({

                        title:
                            "ChatMZK AI",

                        text:
                            shareText,

                        url:
                            window.location.href

                    });

                } else {

                    await navigator.clipboard.writeText(
                        window.location.href
                    );

                    alert(
                        "ChatMZK link copied!"
                    );

                }

            }

            catch (error) {

                console.log(
                    "Share cancelled"
                );

            }

        }
    );

}


// ===============================
// Start Application
// ===============================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadChats();

        input.focus();

    }
);
// ==========================================
// Share ChatMZK
// ==========================================

const shareBtn = document.getElementById("shareBtn");

if (shareBtn) {
    shareBtn.addEventListener("click", async () => {

        const shareUrl = window.location.href;

        try {

            if (navigator.share) {

                await navigator.share({
                    title: "ChatMZK AI",
                    text: "ChatMZK AI open karein",
                    url: shareUrl
                });

            } else {

                await navigator.clipboard.writeText(shareUrl);

                alert("ChatMZK ka link copy ho gaya!");

            }

        } catch (error) {

            console.log("Share cancelled");

        }

    });
}
