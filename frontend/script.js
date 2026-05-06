// =============================================================================
// script.js
// =============================================================================
//
// ## 📘 File Overview: Frontend JavaScript Logic
//
// This file controls ALL the interactive behaviour of the SmartDoc AI chat UI.
// It handles:
//   - Reading and uploading the selected PDF file to the backend
//   - Sending user questions to the backend via HTTP POST
//   - Receiving the 3-mode AI response (Q&A, Summary, Insights)
//   - Rendering each response as a styled, tabbed message in the chat box
//   - Showing/hiding loading states so the user knows the app is working
//
// ## 🛠️ Tools & Functions Used
//
// | API / Method                  | Purpose                                              |
// |-------------------------------|------------------------------------------------------|
// | `fetch()`                     | Browser built-in for making HTTP requests (async)    |
// | `FormData`                    | Packages file uploads as multipart/form-data         |
// | `document.getElementById()`   | Selects DOM elements by their HTML id attribute      |
// | `innerHTML +=`                | Appends new HTML content to an existing element      |
// | `scrollTop / scrollHeight`    | Auto-scrolls the chat box to the newest message      |
// | `async / await`               | Makes asynchronous fetch calls readable & sequential |
//
// ## 🔄 User Interaction Flow
//
// ```
// User selects PDF → uploadFile() → POST /upload/ → PDF saved + embedded
// User types question → sendMessage() → POST /ask/ → 3 AI answers rendered
// ```
// =============================================================================


// ── Configuration ─────────────────────────────────────────────────────────────

const BASE_URL = "http://127.0.0.1:8000";
// ^ The base URL of the FastAPI backend server.
//   All API calls are prefixed with this so changing the server address
//   only requires editing this one constant.


// ── uploadFile() ──────────────────────────────────────────────────────────────

async function uploadFile() {
  // ^ Declare an async function so we can use `await` inside it.
  //   `async` functions always return a Promise implicitly.
  //   Called by the Upload button's onclick="uploadFile()" in index.html.

  const fileInput = document.getElementById("fileInput");
  // ^ Get the <input type="file"> element from the DOM using its id.
  //   This element holds a FileList of files the user has selected.

  const file = fileInput.files[0];
  // ^ Access the first (and only) file from the FileList.
  //   files[0] is the File object representing the selected PDF.

  if (!file) {
    // ^ Check if the user clicked Upload without actually selecting a file.
    alert("⚠️ Please select a PDF file first.");
    // ^ Show a browser alert dialog prompting the user to select a file.
    return;
    // ^ Stop the function here — don't try to upload undefined.
  }

  if (!file.name.endsWith(".pdf")) {
    // ^ Validate the file extension to make sure it's a PDF.
    //   .endsWith() checks the last characters of the filename string.
    alert("⚠️ Only PDF files are supported.");
    // ^ Inform the user that only PDFs are accepted.
    return;
    // ^ Stop execution if the file is not a PDF.
  }

  console.log("📂 Uploading file:", file.name);
  // ^ Log the filename to the browser DevTools console for debugging.
  //   Open DevTools (F12 → Console) to see these messages.

  showUploadStatus("⏳ Uploading and processing PDF...", "loading");
  // ^ Call our helper to show a status message below the upload button
  //   with a "loading" style (spinner/muted colour).

  const formData = new FormData();
  // ^ FormData is a browser API that builds a multipart/form-data request body.
  //   It's the standard way to upload files via fetch().

  formData.append("file", file);
  // ^ Add the selected File object to the FormData under the key "file".
  //   On the FastAPI side, the parameter is: file: UploadFile = File(...)
  //   The key name "file" must match the FastAPI parameter name.

  try {
    // ^ Wrap the fetch call in try/catch so network errors don't crash silently.

    const response = await fetch(`${BASE_URL}/upload/`, {
      // ^ Send an HTTP POST request to the /upload/ endpoint.
      //   `await` pauses this function until the server responds.
      //   BASE_URL + "/upload/" = "http://127.0.0.1:8000/upload/"
      method: "POST",
      // ^ HTTP method. Must be POST because we're sending a file (request body).
      body: formData
      // ^ Attach the FormData (which contains the file) as the request body.
      //   Do NOT set Content-Type manually — fetch sets it automatically
      //   to "multipart/form-data; boundary=..." when body is FormData.
    });

    const data = await response.json();
    // ^ Parse the server's JSON response body into a JavaScript object.
    //   await waits for the body to fully stream before parsing.
    //   e.g., data = { message: "PDF processed successfully" }

    console.log("✅ Upload response:", data);
    // ^ Log the parsed response object to the console for debugging.

    showUploadStatus("✅ " + data.message, "success");
    // ^ Show the server's success message below the upload button
    //   with a "success" style (green colour).

  } catch (error) {
    // ^ Catch any network-level errors (server down, DNS failure, etc.)

    console.error("❌ Upload failed:", error);
    // ^ Log the full error object to the console. console.error() displays
    //   errors in red in DevTools, making them easy to spot.

    showUploadStatus("❌ Upload failed. Is the server running?", "error");
    // ^ Show a user-friendly error message below the upload button.
  }
}


// ── sendMessage() ─────────────────────────────────────────────────────────────

async function sendMessage() {
  // ^ Async function called by the Send button onclick or by pressing Enter.
  //   Sends the user's typed question to the backend and renders 3 AI responses.

  const input = document.getElementById("userInput");
  // ^ Get the <input type="text"> element where the user types their question.

  const chatBox = document.getElementById("chatBox");
  // ^ Get the chat message container div where all messages are displayed.

  const message = input.value.trim();
  // ^ Read the current text in the input field and trim whitespace from both ends.
  //   .trim() prevents sending blank or space-only messages.

  if (!message) {
    // ^ If the trimmed message is an empty string, do nothing.
    return;
    // ^ Exit early — don't send an empty request to the backend.
  }

  console.log("❓ Sending question:", message);
  // ^ Log the question being sent so we can trace issues in the console.

  appendMessage("user", message);
  // ^ Call our helper to add the user's message to the chat UI
  //   with the "user" style (right-aligned, green background).

  input.value = "";
  // ^ Clear the input field immediately after capturing the message,
  //   so the user sees it's been accepted and can type a follow-up.

  const loadingId = appendLoadingMessage();
  // ^ Add a "typing..." loading indicator to the chat and capture its unique ID.
  //   We'll replace this element with the real response once it arrives.

  try {
    // ^ Wrap fetch in try/catch to handle network errors gracefully.

    const response = await fetch(`${BASE_URL}/ask/?query=${encodeURIComponent(message)}`, {
      // ^ Send a POST request to /ask/ with the user's question as a URL query param.
      //   encodeURIComponent() URL-encodes the message so special characters
      //   (spaces → %20, ? → %3F, & → %26) don't break the URL.
      method: "POST"
      // ^ POST method is required by our FastAPI endpoint definition: @app.post("/ask/")
      //   No body is needed — the query goes in the URL query string.
    });

    const data = await response.json();
    // ^ Parse the JSON response. Expected shape:
    //   { qa: "...", summary: "...", insights: "..." }

    console.log("📩 Received 3-mode response:", data);
    // ^ Log the full response object for debugging.

    removeLoadingMessage(loadingId);
    // ^ Remove the "typing..." placeholder now that the real response has arrived.

    appendTripleResponse(data.qa, data.summary, data.insights);
    // ^ Render all three responses (Q&A, Summary, Insights) as a tabbed card
    //   in the chat box. Each tab shows one response type.

  } catch (error) {
    // ^ Handle network errors (e.g., backend not running, connection refused).

    console.error("❌ Request failed:", error);
    // ^ Log the error to the console in red.

    removeLoadingMessage(loadingId);
    // ^ Still remove the loading indicator even on error.

    appendMessage("bot error", "❌ Could not reach the server. Is the backend running?");
    // ^ Show an error message in the chat using the bot style.
  }
}


// ── appendMessage() ───────────────────────────────────────────────────────────

function appendMessage(type, text) {
  // ^ Helper function that creates a single chat message bubble and adds it
  //   to the chatBox element.
  //
  // Args:
  //   type (string): CSS class name for the message style — "user" or "bot".
  //   text (string): The message content to display inside the bubble.

  const chatBox = document.getElementById("chatBox");
  // ^ Re-select chatBox inside the helper (safe, since DOM doesn't change).

  const div = document.createElement("div");
  // ^ Create a new <div> element in memory (not yet added to the page).

  div.className = `message ${type}`;
  // ^ Set the CSS classes. e.g., "message user" or "message bot".
  //   These classes are styled in style.css.

  div.textContent = text;
  // ^ Set the text content of the div.
  //   Using textContent instead of innerHTML prevents XSS attacks
  //   (malicious HTML/JS in user input won't be executed).

  chatBox.appendChild(div);
  // ^ Add the new message div as the last child of the chatBox.
  //   This makes the message appear at the bottom of the chat.

  chatBox.scrollTop = chatBox.scrollHeight;
  // ^ Auto-scroll the chatBox to the bottom so the newest message is visible.
  //   scrollHeight = total content height; setting scrollTop to it scrolls all the way down.
}


// ── appendLoadingMessage() ────────────────────────────────────────────────────

function appendLoadingMessage() {
  // ^ Adds a temporary "AI is thinking..." placeholder message to the chat.
  //   Returns a unique ID so it can be found and removed later.

  const chatBox = document.getElementById("chatBox");
  // ^ Get the chat container.

  const id = "loading-" + Date.now();
  // ^ Generate a unique ID using the current timestamp (milliseconds since epoch).
  //   e.g., "loading-1714123456789". This ensures multiple loading indicators
  //   don't interfere with each other.

  const div = document.createElement("div");
  // ^ Create a new div element for the loading indicator.

  div.className = "message bot loading";
  // ^ Apply "message bot loading" classes for styling.
  //   The "loading" class applies a pulsing/animation effect in style.css.

  div.id = id;
  // ^ Assign the unique ID so we can find and remove this specific element later.

  div.textContent = "🤖 AI is thinking...";
  // ^ The placeholder text the user sees while waiting for the response.

  chatBox.appendChild(div);
  // ^ Add the loading indicator to the bottom of the chat.

  chatBox.scrollTop = chatBox.scrollHeight;
  // ^ Scroll to the bottom so the loading indicator is visible.

  return id;
  // ^ Return the unique ID so the caller can remove this element later.
}


// ── removeLoadingMessage() ────────────────────────────────────────────────────

function removeLoadingMessage(id) {
  // ^ Finds the loading placeholder by its unique ID and removes it from the DOM.
  //
  // Args:
  //   id (string): The unique ID returned by appendLoadingMessage().

  const el = document.getElementById(id);
  // ^ Look up the loading element by its ID in the entire document.

  if (el) {
    // ^ Only try to remove it if the element actually exists.
    //   (Defensive check — it might have been removed already.)
    el.remove();
    // ^ Remove the element from the DOM. It disappears immediately from the UI.
  }
}


// ── appendTripleResponse() ────────────────────────────────────────────────────

function appendTripleResponse(qa, summary, insights) {
  // ^ Creates a tabbed card in the chat box showing all 3 AI response types.
  //   Each tab (Q&A, Summary, Insights) shows a different part of the response.
  //
  // Args:
  //   qa (string):       The direct Q&A answer from the LLM.
  //   summary (string):  The summary of the relevant context.
  //   insights (string): The numbered key insights from the context.

  const chatBox = document.getElementById("chatBox");
  // ^ Get the chat container.

  const cardId = "card-" + Date.now();
  // ^ Generate a unique ID for this response card so tab switching
  //   only affects this specific card and not others in the chat.

  const card = document.createElement("div");
  // ^ Create the outer container div for the tabbed response card.

  card.className = "message bot triple-card";
  // ^ Apply the standard message + bot styles plus "triple-card" for
  //   the custom tab layout defined in style.css.

  card.innerHTML = `
    <div class="tab-buttons">
      <!-- Tab button for Q&A — starts active (selected) by default -->
      <button class="tab-btn active" onclick="switchTab('${cardId}', 'qa', this)">📌 Q&amp;A</button>

      <!-- Tab button for Summary -->
      <button class="tab-btn" onclick="switchTab('${cardId}', 'summary', this)">📝 Summary</button>

      <!-- Tab button for Insights -->
      <button class="tab-btn" onclick="switchTab('${cardId}', 'insights', this)">💡 Insights</button>
    </div>

    <!-- Q&A panel — visible by default -->
    <div class="tab-panel active" id="${cardId}-qa">${escapeHTML(qa)}</div>

    <!-- Summary panel — hidden by default -->
    <div class="tab-panel" id="${cardId}-summary">${escapeHTML(summary)}</div>

    <!-- Insights panel — hidden by default -->
    <div class="tab-panel" id="${cardId}-insights">${escapeHTML(insights)}</div>
  `;
  // ^ Build the full HTML structure for the tabbed card:
  //   - Three tab buttons at the top, each calling switchTab() with the card's unique ID.
  //   - Three panels below, each containing one response mode.
  //   - Only the first tab and panel have the "active" class initially.
  //   - escapeHTML() sanitises the LLM output to prevent XSS.
  //   - &amp; is used for & in HTML attributes to ensure valid HTML.

  chatBox.appendChild(card);
  // ^ Add the completed card to the bottom of the chat box.

  chatBox.scrollTop = chatBox.scrollHeight;
  // ^ Scroll to the bottom so the new card is in view.
}


// ── switchTab() ───────────────────────────────────────────────────────────────

function switchTab(cardId, tabName, clickedBtn) {
  // ^ Handles tab switching inside a triple-response card.
  //   Called by each tab button's onclick attribute.
  //
  // Args:
  //   cardId (string):     The unique ID of the card containing these tabs.
  //   tabName (string):    One of "qa", "summary", or "insights".
  //   clickedBtn (Element): The button DOM element that was clicked.

  const card = clickedBtn.closest(".triple-card");
  // ^ Walk up the DOM from the clicked button to find its parent .triple-card element.
  //   .closest() searches ancestors and returns the first match.
  //   This scopes the tab switch to this specific card only.

  card.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
  // ^ Select all tab buttons inside this card and remove the "active" class from each.
  //   This deactivates all tabs before activating the clicked one.

  card.querySelectorAll(".tab-panel").forEach(panel => panel.classList.remove("active"));
  // ^ Select all tab panels inside this card and remove the "active" class from each.
  //   This hides all panels before showing the selected one.

  clickedBtn.classList.add("active");
  // ^ Add "active" class back to the button that was just clicked.
  //   This visually highlights the selected tab.

  document.getElementById(`${cardId}-${tabName}`).classList.add("active");
  // ^ Find the specific panel that corresponds to the clicked tab
  //   (e.g., "card-1714123456789-qa") and add "active" to show it.
  //   The CSS rule .tab-panel.active { display: block } makes it visible.
}


// ── showUploadStatus() ────────────────────────────────────────────────────────

function showUploadStatus(message, type) {
  // ^ Updates the upload status message element with a given text and style.
  //
  // Args:
  //   message (string): The status text to display (e.g., "✅ PDF uploaded!")
  //   type (string):    Style type — "loading", "success", or "error".

  const statusEl = document.getElementById("uploadStatus");
  // ^ Get the status message element below the upload button.

  statusEl.textContent = message;
  // ^ Set its text content (safely, no HTML injection).

  statusEl.className = `upload-status ${type}`;
  // ^ Apply the appropriate CSS class for styling (e.g., green for success).
}


// ── escapeHTML() ──────────────────────────────────────────────────────────────

function escapeHTML(str) {
  // ^ Sanitises a string by replacing HTML special characters with their
  //   safe HTML entity equivalents. This prevents XSS (Cross-Site Scripting)
  //   attacks where malicious HTML/JS in LLM output could be executed.
  //
  // Args:
  //   str (string): The raw string to sanitise (e.g., LLM response text).
  //
  // Returns:
  //   string: The sanitised string safe to insert into innerHTML.

  return str
    .replace(/&/g, "&amp;")
    // ^ Replace & with &amp; first (must be first to avoid double-encoding).
    .replace(/</g, "&lt;")
    // ^ Replace < with &lt; so HTML tags are rendered as text, not parsed.
    .replace(/>/g, "&gt;")
    // ^ Replace > with &gt; for the same reason.
    .replace(/"/g, "&quot;")
    // ^ Replace " with &quot; to prevent breaking out of HTML attributes.
    .replace(/\n/g, "<br>")
    // ^ Replace newline characters with <br> tags so line breaks are preserved
    //   in the rendered HTML output (since HTML ignores plain \n characters).
}


// ── Enter Key Handler ─────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", function () {
  // ^ Wait until the entire HTML document has been parsed and loaded.
  //   This ensures the #userInput element exists before we attach an event listener.

  const userInput = document.getElementById("userInput");
  // ^ Get the text input field where users type their questions.

  userInput.addEventListener("keydown", function (event) {
    // ^ Listen for any key press while focus is in the input field.
    // ^ event is the KeyboardEvent object with info about which key was pressed.

    if (event.key === "Enter") {
      // ^ Check if the pressed key is the Enter key.
      //   event.key returns the key value as a string (e.g., "Enter", "a", "Shift").
      sendMessage();
      // ^ Trigger sendMessage() as if the Send button was clicked,
      //   providing a convenient keyboard shortcut for the user.
    }
  });
});
