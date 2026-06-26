# KTU CHATBOT

## Overview

**KTU CHATBOT** is an AI-powered assistant and academic evaluation system designed to help students learn concepts efficiently from their study materials and assist educators in automating exam grading. 

The chatbot uses Retrieval-Augmented Generation (RAG) to retrieve relevant content from uploaded notes/textbooks and generate accurate answers using Google's Gemini API. In addition to standard question answering, the system provides specialized tools for generating structured answer keys from question papers and grading student answer sheets.

The application features a modern, responsive web interface built with a **Flask** backend and a polished HTML/CSS/JavaScript frontend.

---

## Features

* **AI-Powered Notes Chatbot**: Ask questions in natural language and receive precise, context-grounded answers.
* **Retrieval-Augmented Generation (RAG)**: Uses FAISS semantic vector search to retrieve relevant pages from uploaded textbooks to minimize hallucinations.
* **Dynamic Knowledge Base Uploads**: Upload study materials (PDFs) directly from the browser to automatically rebuild or expand the FAISS vector database.
* **Answer Key Generator**: Upload an exam question paper PDF to automatically extract questions (with their marks) and generate a suggested answer key based on the textbook notes.
* **Editable PDF Answer Keys**: Review and customize the generated answer key in the UI before exporting it as a downloadable PDF.
* **Automated Answer Sheet Evaluator**: Upload a student's answer sheet PDF and evaluate it against the answer key with three selectable grading strictness levels:
  * **Liberal (Lenient)**: Focuses on core concepts and keywords, giving the student the benefit of the doubt.
  * **Medium (Standard)**: Balances conceptual understanding with correct terminology.
  * **Hard (Strict)**: Requires precise terminology and comprehensive points to award full marks.
* **Programmatic Grading & Reports**: Automatically extracts marks from the AI evaluation to calculate the final total score, percentage, and generates a structured markdown feedback report.

---

## Technology Stack

* **Backend**: Python, Flask
* **AI/LLM**: Google Gemini API (`google-genai`)
* **Vector Search & RAG**: FAISS (cpu), LangChain, HuggingFace Embeddings (`all-MiniLM-L6-v2`)
* **PDF Processing**: PyPDF (`PdfReader`), FPDF (`fpdf` for generating answer key PDFs)
* **Frontend**: Vanilla HTML5, CSS3 (Modern, responsive layout with glassmorphic elements), JavaScript

---

## Project Structure

```text
KTU-CHATBOT/
│
├── app.py                  # Main Flask application server & endpoints
├── chatbot.py              # CLI version of the RAG chatbot
├── build_vector_db.py      # Script to manually build vector database from local data
├── requirements.txt        # Project package dependencies
├── README.md               # Project documentation
├── .env                    # Environment variables (Gemini API Key)
│
├── templates/
│   └── index.html          # Web UI interface
│
├── static/
│   ├── css/
│   │   └── style.css       # Page styles and UI formatting
│   └── js/
│       └── main.js         # Frontend interactive logic (Chat, Uploads, Evaluator)
│
├── data/                   # Directory containing textbook PDFs
│   └── industry_module1.pdf
│
└── vector_db/              # Generated FAISS vector index files
```

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sanikasomanath10/KTU-CHATBOT.git
   cd KTU-CHATBOT
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   * **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   * **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**:
   Create a `.env` file in the root directory and add your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

---

## Running the Application

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Access the application**:
   Open your browser and navigate to:
   ```text
   http://127.0.0.1:5000
   ```

---

## How It Works (RAG Pipeline)

1. **PDF Text Extraction**: Study materials and uploaded textbooks are parsed page-by-page.
2. **Text Chunking**: Text is split into chunks of 1500 characters with a 200-character overlap using LangChain's `RecursiveCharacterTextSplitter`.
3. **Embeddings & Vector Indexing**: Text chunks are converted into dense vector embeddings using the Sentence Transformers `all-MiniLM-L6-v2` model and saved locally in a FAISS index.
4. **Contextual Retrieval**: User questions are matched against the FAISS index using cosine similarity to retrieve the top matching text chunks.
5. **Response Generation**: The retrieved text chunks are injected as context into a structured prompt sent to the Gemini model (`gemini-2.5-flash`) to generate a factual, context-constrained answer.

---

## Authors

* **Alka A.S.** - *B.Tech Computer Science and Engineering, Government Engineering College Sreekrishnapuram*
