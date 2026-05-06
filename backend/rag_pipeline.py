# =============================================================================
# rag_pipeline.py
# =============================================================================
#
# ## 📘 File Overview: RAG Pipeline (Retrieval-Augmented Generation)
#
# This file is the **core brain** of SmartDoc AI. It handles:
# - Loading and splitting PDF documents into chunks
# - Converting chunks into vector embeddings and storing them in ChromaDB
# - Retrieving relevant chunks when a user asks a question
# - Running the chunks through an LLM to generate 3 types of responses:
#     1. 📌 **Q&A**       — Direct answer to the user's question
#     2. 📝 **Summary**   — A brief summary of the relevant context
#     3. 💡 **Insights**  — Key takeaways or interesting observations
#
# ## 🛠️ Tools & Libraries Used
#
# | Tool/Library                          | Purpose                                      |
# |---------------------------------------|----------------------------------------------|
# | `langchain_community.PyPDFLoader`     | Load and parse PDF files page by page        |
# | `langchain_text_splitters`            | Split large documents into manageable chunks |
# | `langchain_huggingface.HuggingFaceEmbeddings` | Convert text chunks into vector numbers |
# | `langchain_chroma.Chroma`             | Store and search vectors (vector database)   |
# | `langchain_core.prompts`              | Build structured prompt templates for LLM    |
# | `langchain_core.output_parsers`       | Parse LLM output into plain Python strings   |
# | `langchain_core.runnables`            | Chain pipeline steps using `|` operator      |
# | `langchain_groq.ChatGroq`             | Groq-hosted LLaMA3 LLM for fast inference    |
#
# ## 🔄 Pipeline Flow
#
# ```
# PDF File
#   → PyPDFLoader (read pages)
#   → RecursiveCharacterTextSplitter (chunk pages)
#   → HuggingFaceEmbeddings (embed chunks)
#   → Chroma (store vectors)
#
# User Query
#   → Chroma Retriever (find top-k similar chunks)
#   → format_docs() (join chunks into text)
#   → ChatPromptTemplate (build 3 prompts: QA, Summary, Insights)
#   → ChatGroq LLM (generate answers)
#   → StrOutputParser (return clean strings)
# ```
# =============================================================================


# ── Imports ──────────────────────────────────────────────────────────────────

from langchain_community.document_loaders import PyPDFLoader
#✅ What it does:
#Reads PDF file
#Converts it into documents (one per page

from langchain_text_splitters import RecursiveCharacterTextSplitter
# ^ Splits large text into smaller chunks using a hierarchy of separators
#   (\n\n → \n → space → character) so that splits happen at natural boundaries.

from langchain_huggingface import HuggingFaceEmbeddings
# ^ Wraps a HuggingFace sentence-transformer model to convert text → float vectors.
#   These vectors capture the semantic meaning of the text.

from langchain_chroma import Chroma
# ^ Chroma is a lightweight local vector database. It stores embeddings and
#   allows fast similarity search to find the most relevant text chunks.

from langchain_core.prompts import ChatPromptTemplate
# ✅ Purpose:
#Creates structured prompts for LLM

from langchain_core.output_parsers import StrOutputParser
# ^ Converts the LLM's AIMessage response object into a plain Python string,
#   so it can be returned directly to the frontend.

from langchain_core.runnables import RunnablePassthrough
# ^ A passthrough runnable that takes an input and passes it unchanged.
#   Used to forward the user's query directly into the prompt template.

from langchain_groq import ChatGroq
# ^ ChatGroq connects to Groq's blazing-fast inference API to run LLaMA3-70B.
#   Requires GROQ_API_KEY set as an environment variable.

import os
# ^ Python standard library for reading environment variables (e.g., API keys)
#   and working with file paths.

from dotenv import load_dotenv
load_dotenv()
# ^ Loads environment variables from a .env file into the process's environment.



# ── Embedding Model Initialization ───────────────────────────────────────────

print("🚀 Initializing embedding model...")
# ^ Log message so the developer can see server startup progress in the terminal.

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
    # ^ "all-MiniLM-L6-v2" is a small but powerful sentence-transformer model.
    #   It converts any text into a 384-dimensional float vector.
    #   It runs locally on CPU — no API key needed.
)

print("✅ Embedding model loaded successfully")
# ^ Confirms the embedding model is ready. If this fails, the server won't start.

# ── Global State ─────────────────────────────────────────────────────────────

vector_db = None
# ^ This global variable holds the ChromaDB instance after a PDF is processed.
#   It starts as None; if a user asks a question before uploading, we catch this.


# ── PDF Processing Function ───────────────────────────────────────────────────

def process_pdf(file_path):
    """
    Loads a PDF, splits it into chunks, embeds the chunks,
    and stores them in the global ChromaDB vector store.

    
    Returns:
        str: Success message to be sent back to the frontend.
    """

    print(f"\n📂 Loading PDF: {file_path}")
    # Initializes loader for the given PDF file path. This does not read the file yet.

    loader = PyPDFLoader(file_path)
    # Initializes loader

    documents = loader.load()
    # ✅ What happens:
    # Reads PDF
    # Converts into pages

    print(f"📄 Total pages loaded: {len(documents)}")
    # ^ Shows how many pages were found in the PDF.

    print("✂️ Splitting document into chunks...")
    # ^ Log that chunking is about to begin.

    splitter = RecursiveCharacterTextSplitter(
        #✅ Why chunking?
        #LLM can't process full PDF
        #Smaller chunks = better retrieval
        chunk_size=500,
        # ^ Each chunk will be at most 500 characters long.
        #   Smaller chunks = more precise retrieval but more DB entries.
        chunk_overlap=50
        # last 50 characters of previous chunk will be repeated at the start of the next chunk. This helps maintain context across chunks during retrieval.
    )

    docs = splitter.split_documents(documents) 
    # ^ Splits all the pages into smaller chunks.
    #   Returns a new list of Document objects — now many more, but smaller.

    print(f"🧩 Total chunks created: {len(docs)}")
    # ^ Log total number of chunks created from the PDF.

    print("📦 Creating vector database (Chroma)...")
    # ^ Log that we're about to embed and store all chunks.

    global vector_db
    # ^ Declare we're modifying the global variable, not a local one.

    vector_db = Chroma.from_documents(docs, embeddings)
    # What happens here:
    # Each chunk → embedding
    # Stored in Chroma DB
    print("✅ Embeddings stored successfully!")
    # ^ Log that the vector database is fully built and ready.

    return "PDF processed successfully"
    # ^ Return a simple success string. main.py sends this back to the frontend.


# ── Question Answering Function ───────────────────────────────────────────────

def ask_question(query):
    """
    Takes a user query, retrieves relevant PDF chunks from ChromaDB,
    and generates 3 types of responses using a Groq LLM:
        - Q&A answer
        - Summary of context
        - Key insights

   

    Returns:
        dict: A dictionary with keys "qa", "summary", "insights".
    """

    print(f"\n❓ User Question: {query}")
    # ^ Log the incoming query for debugging.

    if vector_db is None:
        # ^ Check if the user forgot to upload a PDF first.
        print("❌ ERROR: No PDF processed yet!")
        # ^ Log the error clearly.
        return {
            "qa": "Please upload a PDF first.",
            "summary": "No document loaded.",
            "insights": "Upload a PDF to get insights."
        }
        # ^ Return a structured error dict matching the 3-mode format.

    print("🔍 Creating retriever...")
    # ^ Log that we're setting up the retrieval step.

    retriever = vector_db.as_retriever(
        search_kwargs={"k": 4}
        #in this line retriever will fetch top 4 most similar chunks from the vector db
    )
    

    def format_docs(docs):
        
        print("📄 Formatting retrieved documents...")
        # ^ Log that we've received the retrieved chunks and are formatting them.
        return "\n\n".join(doc.page_content for doc in docs)
        #combines the retrieved chunks into a single string

    print("🤖 Initializing LLM (Groq / LLaMA3)...")
    # ^ Log that the LLM is about to be set up.

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        # ^ Use LLaMA3.1-8B model hosted on Groq. 8192 is the context window size.
        #   Groq's infrastructure runs this at extremely high token throughput.
        api_key=os.getenv("GROQ_API_KEY")
        # ^ Read the Groq API key from the environment variable GROQ_API_KEY form the .env file. 
    )

    # ── Helper: Build and Run a Single RAG Chain ──────────────────────────────

    def run_chain(prompt_template_str):
        """
        Builds a RAG chain using a given prompt string and runs it.

        Returns:
            str: The LLM's generated response as a plain string.
        """

        prompt = ChatPromptTemplate.from_template(prompt_template_str)
        # ^ Parse the prompt string into a ChatPromptTemplate object.
        #   At runtime, {context} and {question} placeholders are filled in.

        rag_chain = (
            {
                "context": retriever | format_docs,
                # ^ Retriever fetches top-k chunks → format_docs joins them into a string.
                #   This fills the {context} placeholder in the prompt.
                "question": RunnablePassthrough()
                # ^ RunnablePassthrough takes whatever input is given (the query string)
                #   and passes it through unchanged to fill {question}.
            }
            | prompt
            # ^ The dict above is fed into the prompt template, filling the placeholders.
            | llm
            # ^ The filled prompt is sent to the ChatGroq LLM for generation.
            | StrOutputParser()
            # ^ The LLM returns an AIMessage object. StrOutputParser extracts .content
            #   and returns it as a plain Python string.
        )

        return rag_chain.invoke(query)
        # ^ Execute the full chain with the user's query as input.
        #   LangChain handles passing the query through each step automatically.

    # ── Prompt 1: Q&A ─────────────────────────────────────────────────────────

    print("🔗 Running Q&A chain...")
    # ^ Log which mode is being processed.

    qa_prompt = """
You are a helpful assistant. Answer the user's question clearly and directly,
based only on the context provided below.

Context:
{context}

Question:
{question}

Provide a concise and accurate answer. If the answer is not in the context, say so.
"""
    # ^ This prompt tells the LLM to act as a Q&A assistant.
    #   It restricts the answer to only what is in the retrieved context,
    #   preventing hallucination of facts not present in the PDF.

    qa_answer = run_chain(qa_prompt)
    # ^ Run the RAG chain with the Q&A prompt and get the answer string.

    # ── Prompt 2: Summary ─────────────────────────────────────────────────────

    print("🔗 Running Summary chain...")
    # ^ Log which mode is being processed.

    summary_prompt = """
You are a document summarizer. Based on the context provided below,
write a brief and clear summary of the most relevant information
related to the user's question.

Context:
{context}

Question:
{question}

Write a 3–5 sentence summary of the relevant content.
"""
    # ^ This prompt instructs the LLM to summarize the retrieved context
    #   in relation to what the user asked, in 3-5 sentences.

    summary_answer = run_chain(summary_prompt)
    # ^ Run the RAG chain with the Summary prompt and get the summary string.

    # ── Prompt 3: Insights ────────────────────────────────────────────────────

    print("🔗 Running Insights chain...")
    # ^ Log which mode is being processed.

    insights_prompt = """
You are an intelligent analyst. Based on the context provided below,
extract 3 to 5 key insights or important takeaways relevant to
the user's question. Present them as a numbered list.

Context:
{context}

Question:
{question}

List the key insights clearly and concisely.
"""
    # ^ This prompt asks the LLM to think analytically and extract
    #   the most important points as a numbered list for easy reading.

    insights_answer = run_chain(insights_prompt)
    # ^ Run the RAG chain with the Insights prompt and get the insights string.

    # ── Return All Three Responses ────────────────────────────────────────────

    print("✅ All three responses generated successfully!")
    # ^ Log that all three chains completed without errors.

    return {
        "qa": qa_answer,
        # ^ Direct Q&A answer to the user's question.
        "summary": summary_answer,
        # ^ A brief summary of the relevant PDF content.
        "insights": insights_answer
        # ^ Key takeaways as a numbered list.
    }
    # ^ Return a Python dict. main.py will convert this to JSON for the frontend.
