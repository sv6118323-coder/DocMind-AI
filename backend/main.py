# =============================================================================
# main.py
# =============================================================================
#
# ## 📘 File Overview: FastAPI Backend Server
#
# This file is the **backend server** for SmartDoc AI. It acts as the bridge
# between the frontend (HTML/JS) and the RAG pipeline (rag_pipeline.py).
#
# It exposes two HTTP endpoints:
#   - `POST /upload/` — Accepts a PDF file from the browser, saves it to disk,
#                       and triggers the RAG ingestion pipeline.
#   - `POST /ask/`    — Accepts a text query, runs it through the RAG pipeline,
#                       and returns three types of AI responses (QA, Summary, Insights).
#
# ## 🛠️ Tools & Libraries Used
#
# | Tool/Library              | Purpose                                                   |
# |---------------------------|-----------------------------------------------------------|
# | `FastAPI`                 | Modern Python web framework for building REST APIs        |
# | `UploadFile`, `File`      | FastAPI utilities to accept multipart file uploads        |
# | `CORSMiddleware`          | Allows the browser frontend to call this backend API      |
# | `shutil`                  | Standard library: copies file streams to disk             |
# | `os`                      | Standard library: creates directories, builds file paths  |
# | `rag_pipeline`            | Our custom module: process_pdf() and ask_question()       |
#
# ## 🔄 Request Flow
#
# ```
# Browser (index.html)
#   → POST /upload/  →  save file  →  process_pdf()  →  ChromaDB ready
#   → POST /ask/     →  ask_question()  →  3 LLM responses  →  JSON to browser
# ```
#
# ## ▶️ How to Run
#
# ```bash
# pip install fastapi uvicorn python-multipart
# uvicorn main:app --reload
# ```
# Server will start at: http://127.0.0.1:8000
# =============================================================================


# ── Imports ──────────────────────────────────────────────────────────────────

from fastapi import FastAPI, UploadFile, File
# FastAPI → creates the backend server (API app)
# UploadFile → represents uploaded files (like PDFs)
# File(...) → tells FastAPI: “this parameter comes from a file upload form”

from fastapi.middleware.cors import CORSMiddleware
#Enables CORS (Cross-Origin Resource Sharing)
#👉 Why needed?
#Frontend (HTML/JS) runs on a different origin than backend → browser blocks it without CORS

import shutil
# ^ Python standard library module for high-level file operations.
#   We use shutil.copyfileobj() to efficiently copy the uploaded file's
#   byte stream to a local file on disk.

import os
# ^ Python standard library for interacting with the operating system.
#   Used to: build file paths (os.path.join), create directories (os.makedirs).

from rag_pipeline import process_pdf, ask_question
# ^ Import our two core functions from rag_pipeline.py:
#   - process_pdf(file_path) → loads, chunks, embeds and stores the PDF
#   - ask_question(query)    → retrieves context and generates 3 AI responses

# ── App Initialization ────────────────────────────────────────────────────────

print("🚀 Starting FastAPI server...")
# ^ This log line appears in the terminal when the server boots up,
#   confirming that main.py was loaded and execution has started.

app = FastAPI(
    title="DocMind AI",
    # ^ Sets the title shown in the auto-generated API docs at /docs
    description="Upload a PDF and ask questions. Get Q&A, Summary, and Insights.",
    # ^ Description shown in the Swagger UI docs
    version="1.0.0"
    # versioning is good practice for APIs, helps with future updates and documentation, it will show the version in the auto-generated docs at /docs
)
# ^ Creates the main FastAPI application instance. All routes and middleware
#   are registered on this object.

# ── CORS Configuration ────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    # ^ Register the CORS middleware on our FastAPI app.
    allow_origins=["*"],
    # ^ Allow requests from ANY origin (any domain or file://).
    #   In production, replace "*" with your actual frontend domain,
    #   e.g., ["https://myapp.com"] for better security.
    allow_methods=["*"],
    # ^ Allow all HTTP methods: GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],
    # ^ Allow all request headers (Content-Type, Authorization, etc.).
)

# ── Upload Directory Setup ────────────────────────────────────────────────────

UPLOAD_DIR = "uploads"
# ^ Define the folder name where uploaded PDFs will be saved on the server.
#   This is a relative path, so files go to ./uploads/ in the project directory.

os.makedirs(UPLOAD_DIR, exist_ok=True)
# ^ Create the uploads/ directory on disk if it doesn't already exist.
#   exist_ok=True means: don't raise an error if the folder is already there.
#   This runs once at startup, so the directory is always ready.


# ── Endpoint 1: Upload PDF ────────────────────────────────────────────────────

@app.post("/upload/")
# ^ Register this function as a handler for HTTP POST requests to /upload/.
#   FastAPI reads the type annotations below to automatically parse the request.
async def upload_pdf(file: UploadFile = File(...)):
    #async → non-blocking (important for file uploads) it is useful when handling multiple requests simultaneously, allowing the server to process other tasks while waiting for file I/O operations to complete.
    #file: UploadFile → expects file input
    #File(...) → required parameter
    print(f"\n📥 Received file: {file.filename}")
    # ^ Log the name of the incoming file so we can see what was uploaded
    #   in the terminal. file.filename comes from the browser's FormData.

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    # ^ Construct the full file path where the PDF will be saved.
    #   e.g., if UPLOAD_DIR = "uploads" and filename = "report.pdf",
    #   then file_path = "uploads/report.pdf"

    with open(file_path, "wb") as buffer:
        # ^ Open the target file path for writing in binary mode ("wb").
        #   wb tells python to store uploaded content as raw bytes (rather than text). at given file path so it can be used later by the model
        #   The `with` block ensures the file is properly closed even if an error occurs.
        # buffer is a temporary memory area that holds data while its being transferred from the uploaded file stream to the disk file.
        shutil.copyfileobj(file.file, buffer)
        # ^ Copy bytes from the uploaded file stream (file.file) into the
        #   local file (buffer). This is memory-efficient — it reads and writes
        #   in chunks rather than loading the whole PDF into RAM at once.

    print("💾 File saved to disk successfully")
    # ^ Log confirmation that the file write completed without errors.

    message = process_pdf(file_path)
    # ^ Call process_pdf() from rag_pipeline.py.
    #   This function:
    #     1. Reads the saved PDF from file_path
    #     2. Splits it into text chunks
    #     3. Embeds each chunk into a float vector
    #     4. Stores all vectors in the global ChromaDB instance
    #   Returns a success string like "PDF processed successfully".

    print("🎯 PDF fully processed and ready for queries")
    # ^ Log that the vector database is now ready to answer questions.

    return {"message": message}
    # ^ Return a JSON response to the frontend.
    #   FastAPI automatically converts Python dicts to JSON.
    #   e.g.: {"message": "PDF processed successfully"}


# ── Endpoint 2: Ask Question ──────────────────────────────────────────────────

@app.post("/ask/")
#API endpoint: POST /ask/
async def ask(query: str):
   #Takes query as string
    print(f"\n📨 Incoming query: {query}")
    # ^ Log the user's query in the terminal for debugging and monitoring.

    if not query or query.strip() == "":
        # ^ Validate that the query is not empty or just whitespace.
        #   strip() removes leading and trailing spaces.
        return {
            "qa": "Please enter a question.",
            "summary": "No question provided.",
            "insights": "Ask a question to get insights."
        }
        # ^ Return a polite error if the query is blank,
        #   so the frontend can display it without crashing.

    result = ask_question(query)
    # ^ Call ask_question() from rag_pipeline.py with the user's query.
    #   This function:
    #     1. Embeds the query into a vector
    #     2. Retrieves the top-4 most similar PDF chunks from ChromaDB
    #     3. Runs 3 separate LLM chains (Q&A, Summary, Insights)
    #     4. Returns a dict: {"qa": "...", "summary": "...", "insights": "..."}

    print("📤 Sending 3-mode response to frontend")
    # ^ Log that the server is sending the response back.

    return result
    # ^ FastAPI auto-converts the returned Python dict to a JSON response body.
    #   The frontend (script.js) will parse this and display each mode separately.
