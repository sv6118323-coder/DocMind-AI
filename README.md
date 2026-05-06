# 🧠 DocMind AI

> **Turn any PDF into a conversation.**  
> Upload a document. Ask anything. Get answers, summaries, and key insights — powered by RAG + LLaMA3.

---

## 📌 What is DocMind AI?

DocMind AI is a **Retrieval-Augmented Generation (RAG)** application that lets you have an intelligent conversation with any PDF document. Instead of reading through pages manually, simply upload your document and ask questions in plain English.

Every response is delivered in **three modes**:

| Mode | Description |
|------|-------------|
| 📌 **Q&A** | A direct, accurate answer to your question |
| 📝 **Summary** | A concise overview of the relevant context |
| 💡 **Insights** | Key takeaways presented as a numbered list |

---

## 🚀 Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, Python |
| **RAG Framework** | LangChain |
| **LLM** | LLaMA 3.1 8B via Groq API |
| **Embeddings** | `all-MiniLM-L6-v2` (HuggingFace) |
| **Vector Database** | ChromaDB (local, in-memory) |
| **PDF Parsing** | PyPDFLoader |
| **Frontend** | Vanilla HTML, CSS, JavaScript |

---

## 🗂️ Project Structure

```
docmind-ai/
├── main.py            # FastAPI server — /upload/ and /ask/ endpoints
├── rag_pipeline.py    # Core RAG logic — PDF ingestion + LLM query chains
├── index.html         # Frontend chat UI with tabbed response cards
├── serve.py           # Simple static file server for the frontend
├── requirements.txt   # Python dependencies
├── .env               # Your secret API keys — never pushed to GitHub
├── .gitignore         # Tells Git to ignore .env, uploads/, __pycache__/ etc.
└── uploads/           # Auto-created folder for uploaded PDFs (git ignored)
```

---

## ⚙️ How It Works

```
PDF Upload
  → PyPDFLoader reads pages
  → RecursiveCharacterTextSplitter chunks the text (500 chars, 50 overlap)
  → HuggingFace Embeddings converts chunks to 384-dimensional vectors
  → ChromaDB stores the vector index in memory

User Query
  → ChromaDB retrieves top-4 most relevant chunks
  → 3 LangChain RAG chains run sequentially (Q&A · Summary · Insights)
  → Groq/LLaMA3 generates a response for each chain
  → FastAPI returns JSON → Frontend renders tabbed UI
```

---

## 🛠️ Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/docmind-ai.git
cd docmind-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your Groq API key

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> Get a free API key at [console.groq.com](https://console.groq.com)

### 4. Start the backend server

```bash
uvicorn main:app --reload
```

Backend runs at: `http://127.0.0.1:8000`  
Auto-generated API docs available at: `http://127.0.0.1:8000/docs`

### 5. Start the frontend server

Open a second terminal:

```bash
python serve.py
```

Frontend runs at: `http://localhost:3000`

---

## 📖 Usage

1. Open `http://localhost:3000` in your browser
2. Click **Choose PDF** and select any `.pdf` file
3. Click **Upload & Process** — wait for the ✅ confirmation message
4. Type your question in the chat input and press **Send**
5. Switch between the **Q&A**, **Summary**, and **Insights** tabs to explore the response

---

## 🔌 API Reference

### `POST /upload/`

Accepts a PDF file and ingests it into the vector database.

**Request:** `multipart/form-data` with a `file` field

**Response:**
```json
{ "message": "PDF processed successfully" }
```

---

### `POST /ask/?query=your+question`

Runs the query through all three RAG chains and returns responses.

**Response:**
```json
{
  "qa": "Direct answer to your question...",
  "summary": "3–5 sentence summary of relevant content...",
  "insights": "1. Key point\n2. Another point\n3. ..."
}
```

---

## 🔐 Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key for LLaMA3 inference |

These are stored in a `.env` file locally and loaded at runtime using `python-dotenv`. The `.env` file is listed in `.gitignore` and is **never pushed to GitHub**.

---

## 📸 Screenshots

> *(Add screenshots of your UI here)*

---

## 🧩 Known Limitations

- Only one PDF can be active at a time — uploading a new file replaces the previous index
- ChromaDB is in-memory; the vector store resets when the server restarts
- Large PDFs (100+ pages) may take a few seconds to process

---

## 🛣️ Roadmap

- [ ] Multi-document support
- [ ] Persistent vector store across sessions
- [ ] Source citation with page numbers in responses
- [ ] Streaming LLM responses to the frontend
- [ ] Docker support for one-command deployment

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Acknowledgements

- [LangChain](https://www.langchain.com/) — RAG framework
- [Groq](https://groq.com/) — Ultra-fast LLaMA3 inference
- [ChromaDB](https://www.trychroma.com/) — Local vector database
- [HuggingFace](https://huggingface.co/) — Sentence transformer embeddings
- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
